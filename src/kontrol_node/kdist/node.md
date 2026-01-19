```k
requires "foundry.md"
requires "driver.md"
requires "no_code_size_checks.md"
requires "trace.md"
requires "trace-json.md"
requires "state-json.md"
requires "config.md"
requires "rpc-json.md"

module KONTROL-NODE
    imports FOUNDRY
    imports ETHEREUM-SIMULATION
    imports NO-CODE-SIZE-CHECKS
    imports EVM-TRACING
    imports STATE-JSON
    imports RPC-JSON
    imports TRACE-JSON
    imports KONTROL-NODE-CONFIG


    syntax RPCResponse ::= String | Int

    syntax EthereumSimulation ::= Start
    syntax Start ::= #start(
      String // IO directory
    ) [symbol(start)]

    configuration <simbolikVM/>
```

Create the initial configuration by reading the inputs from the IO directory

```k

  rule <k> #start( IO_DIR )
        => #loadStateDump( IO_DIR, 0)
        ~> #loadRpcRequests( IO_DIR )
        ~> #saveStateDump( IO_DIR )
        ...
       </k>
       <ioDir> _ => IO_DIR </ioDir>

```

  Transaction Signing and execution
  ---------------------------------

  The next block of K code contains the set of functions used to implement `eth_sendTransaction`.
  The information send with the request is used to load a new `<message>` cell, sign, validate, and execute it.
  Once these steps are performed, a receipt is generated.

```k
    // Assumes the transaction is fully loaded into the <message>-cell
    // and that the initial state is fully initialized.
    // It then executes the transaction
    rule <k> #processTx( TX_ID )
          => #signTX TX_ID FROM
          ~> #setup_G0 TX_ID
          ~> #validateTx TX_ID
          ~> #updateTimestamp
          ~> #executeTx TX_ID
          ~> #makeTxReceipt TX_ID
          ~> #finalizeBlock
          ~> #computeHeaderHash
          ...
          </k>
          <origin> FROM </origin>

    // ECDSASign returns [r,s,recid]
    // previously of EIP155, v is computed as:  v = recid + 27
    // post of EIP155, v is computed as :       v = 2 * CHAIN_ID + recid + 35

    syntax KItem ::= "#signTX" Int Int
                   | "#signTX" Int String
 // -------------------------------------
    rule <k> #signTX TXID ACCTFROM:Int => #signTX TXID ECDSASign( Keccak256raw(#rlpEncodeTxData (LegacySignedTxData(TN, TP, TG, TT, TV, TD, B))), #padToWidth( 32, #asByteStack(KEY))) ... </k>
        <accountKeys> ... ACCTFROM |-> KEY ... </accountKeys>
        <mode> NORMAL </mode>
        <chainID> B </chainID>
         <message>
           <msgID> TXID </msgID>
           <txNonce>    TN     </txNonce>
           <txGasPrice> TP     </txGasPrice>
           <txGasLimit> TG     </txGasLimit>
           <to>         TT     </to>
           <value>      TV     </value>
           <data>       TD     </data>
           ...
         </message>

    rule <k> #signTX TXID SIG:String => .K ... </k>
         <chainID> B </chainID>
         <message>
           <msgID> TXID </msgID>
           <sigR> _ => #parseHexBytes( substrString( SIG, 0, 64 ) )           </sigR>
           <sigS> _ => #parseHexBytes( substrString( SIG, 64, 128 ) )         </sigS>
           <sigV> _ => 2 *Int B +Int #parseHexWord( substrString( SIG, 128, 130 ) ) +Int 35 </sigV>
           ...
         </message>

    rule <k> #signTX TXID ACCTFROM:Int => .K ... </k>
         <accountKeys> KEYMAP                      </accountKeys>
         <mode>        NORMAL                      </mode>
         <txPending>   ListItem(TXID) => .List ... </txPending>
         <txOrder>     ListItem(TXID) => .List ... </txOrder>
         <rpcResponse> _ => -1 </rpcResponse> // TODO: Come up with error code values for this cell
      requires notBool ACCTFROM in_keys(KEYMAP)


    syntax KItem ::= "#setup_G0" Int
 // --------------------------------
    rule <k> #setup_G0 TXID => .K ... </k>
         <schedule> SCHED </schedule>
         <callGas> _ => G0(SCHED, DATA, (ACCTTO ==K .Account) ) </callGas>
         <message>
           <msgID> TXID   </msgID>
           <data>  DATA   </data>
           <to>    ACCTTO </to>
           ...
         </message>

    syntax KItem ::= "#validateTx" Int
 // ----------------------------------
    rule <k> #validateTx TXID => #end #if BAL <Int GLIMIT *Int GPRICE #then EVMC_BALANCE_UNDERFLOW #else EVMC_OUT_OF_GAS #fi ... </k>
         <callGas> G0_INIT </callGas>
         <origin> ACCTFROM </origin>
         <account>
           <acctID> ACCTFROM </acctID>
           <balance> BAL </balance>
           ...
         </account>
         <message>
           <msgID>      TXID   </msgID>
           <txGasPrice> GPRICE </txGasPrice>
           <txGasLimit> GLIMIT </txGasLimit>
           ...
         </message>
      requires GLIMIT <Int G0_INIT
        orBool BAL <Int GLIMIT *Int GPRICE

    rule <k> #validateTx TXID => .K ... </k>
         <origin> ACCTFROM </origin>
         <callGas> G0_INIT => GLIMIT -Int G0_INIT </callGas>
         <account>
           <acctID> ACCTFROM </acctID>
           <balance> BAL </balance>
           ...
         </account>
         <message>
           <msgID>      TXID   </msgID>
           <txGasPrice> GPRICE </txGasPrice>
           <txGasLimit> GLIMIT </txGasLimit>
           ...
         </message>
      requires GLIMIT >=Int G0_INIT
       andBool BAL >=Int GLIMIT *Int GPRICE

    syntax KItem ::= "#updateTimestamp"
 // -----------------------------------
    rule <k> #updateTimestamp => .K ... </k> <timestamp> TS => TS +Int TD </timestamp> <timeDiff> TD </timeDiff>

    syntax KItem ::= "#executeTx" Int
 // ---------------------------------
    rule <k> #executeTx TXID:Int
          => #accessAccounts ACCTFROM #newAddr(ACCTFROM, NONCE) #precompiledAccountsSet(SCHED)
          ~> #loadAccessList(TA)
          ~> #create ACCTFROM #newAddr(ACCTFROM, NONCE) VALUE CODE
          ~> #finishTx
          ~> #finalizeTx(false, Ctxfloor(SCHED, CODE))
         ...
         </k>
         <traceBalance> TRBAL </traceBalance>
         <schedule> SCHED </schedule>
         <gasPrice> _ => GPRICE </gasPrice>
         <origin> ACCTFROM </origin>
         <callDepth> _ => -1 </callDepth>
         <txPending> ListItem(TXID:Int) ... </txPending>
         <message>
           <msgID>      TXID     </msgID>
           <txGasPrice> GPRICE   </txGasPrice>
           <txGasLimit> GLIMIT   </txGasLimit>
           <to>         .Account </to>
           <value>      VALUE    </value>
           <data>       CODE     </data>
           <txAccess>   TA       </txAccess>
           ...
         </message>
         <account>
           <acctID> ACCTFROM </acctID>
           <balance> BAL => BAL -Int (GLIMIT *Int GPRICE) </balance>
           <nonce> NONCE </nonce>
           ...
         </account>
         <currentBalanceMutations> CBM => #if TRBAL #then CBM[ ACCTFROM <- BAL -Int (GLIMIT *Int GPRICE) ] #else CBM #fi </currentBalanceMutations>

    rule <k> #executeTx TXID:Int
          => #accessAccounts ACCTFROM ACCTTO #precompiledAccountsSet(SCHED)
          ~> #loadAccessList(TA)
          ~> #call ACCTFROM ACCTTO ACCTTO VALUE VALUE DATA false
          ~> #finishTx
          ~> #finalizeTx(false, Ctxfloor(SCHED, DATA))
         ...
         </k>
         <traceBalance> TRBAL </traceBalance>
         <traceNonce> TRNONCE </traceNonce>
         <schedule> SCHED </schedule>
         <origin> ACCTFROM </origin>
         <gasPrice> _ => GPRICE </gasPrice>
         <txPending> ListItem(TXID) ... </txPending>
         <callDepth> _ => -1 </callDepth>
         <message>
           <msgID>      TXID   </msgID>
           <txGasPrice> GPRICE </txGasPrice>
           <txGasLimit> GLIMIT </txGasLimit>
           <to>         ACCTTO </to>
           <value>      VALUE  </value>
           <data>       DATA   </data>
           <txAccess>   TA     </txAccess>
           ...
         </message>
         <account>
           <acctID> ACCTFROM </acctID>
           <balance> BAL => BAL -Int (GLIMIT *Int GPRICE) </balance>
           <nonce> NONCE => NONCE +Int 1 </nonce>
           ...
         </account>
         <currentNonceMutations> CNM => #if TRNONCE #then CNM[ ACCTFROM <- NONCE +Int 1 ] #else CNM #fi </currentNonceMutations>
         <currentBalanceMutations> CBM => #if TRBAL #then CBM[ ACCTFROM <- BAL -Int (GLIMIT *Int GPRICE) ] #else CBM #fi </currentBalanceMutations>
      requires ACCTTO =/=K .Account

    syntax KItem ::= "#makeTxReceipt" Int
 // -------------------------------------
    rule <k> #makeTxReceipt TXID => .K ... </k>
         <rpcResponse> _ =>  Keccak256(#rlpEncode( [ TN, TP, TG, #addrBytes(TT), TV, TD, TW, TR, TS ] )) </rpcResponse>
         <txReceipts>
           ( .Bag
          => <txReceipt>
               <txHash> Keccak256(#rlpEncode( [ TN, TP, TG, #addrBytes(TT), TV, TD, TW, TR, TS ] )) </txHash>
               <txCumulativeGas> CGAS                           </txCumulativeGas>
               <logSet>          LOGS                           </logSet>
               <bloomFilter>     #bloomFilter(LOGS)             </bloomFilter>
               <txStatus>        bool2Word(SC ==K EVMC_SUCCESS) </txStatus>
               <txID>            TXID                           </txID>
               <sender>          ACCT                           </sender>
               <txBlockNumber>   BN                             </txBlockNumber>
               <contractAddress>
                 #if TT ==K .Account #then #newAddr(ACCT, TN) #else .Account #fi
               </contractAddress>
             </txReceipt>
           )
           ...
         </txReceipts>
         <message>
           <msgID>      TXID </msgID>
           <txNonce>    TN  </txNonce>
           <txGasPrice> TP  </txGasPrice>
           <txGasLimit> TG  </txGasLimit>
           <to>         TT  </to>
           <value>      TV  </value>
           <sigV>       TW  </sigV>
           <sigR>       TR  </sigR>
           <sigS>       TS  </sigS>
           <data>       TD  </data>
           ...
         </message>
         <statusCode> SC   </statusCode>
         <gasUsed>    CGAS </gasUsed>
         <log>        LOGS </log>
         <number>     BN   </number>
         <origin>     ACCT </origin>
```

  Block Mining
  ------------

  The productions below are used to perform the mining of blocks, advancing the blockchain state.

```k
    syntax KItem ::= "#updateParentHash"
                   | "#incrementBlockNumber"
                   | "#clearGas"
                   | "#clearTxLists"
              //   | "#updateTrieRoots"
              //   | "#updateStateRoot"
              //   | "#updateTransactionsRoot"
              //   | "#updateReceiptsRoot"
              //   | "#initStateTrie"
              //   | "#updateStateTrie"
              //   | #updateStateTrie ( JSONs )
 // -------------------------------------------

    rule <k> #updateParentHash => .K ... </k>
         <previousHash> _ => HP </previousHash>
         <currentBlockHash> HP </currentBlockHash>

    rule <k> #incrementBlockNumber => .K ... </k> <number> BN => BN +Int 1 </number>

    rule <k> #clearTxLists => .K ... </k>
         <txPending> _ => .List </txPending>
         <txOrder>   _ => .List </txOrder>

    rule <k> #clearGas => .K ... </k> <gas> _ => 0 </gas>
```

  Helper Funcs
  ------------

```k
    syntax KItem ::= "#computeHeaderHash" [symbol(computeHeaderHash)]
 // -----------------------------------------------------------------
    rule <k> #computeHeaderHash => .K ... </k>
         <currentBlockHash> _ => #blockHeaderHash(HP, HO, HC, HR, HT, HE, HB, HD, HI, HL, HG, HS, HX, HM, HN) </currentBlockHash>
         <previousHash>     HP </previousHash>
         <ommersHash>       HO </ommersHash>
         <coinbase>         HC </coinbase>
         <stateRoot>        HR </stateRoot>
         <transactionsRoot> HT </transactionsRoot>
         <receiptsRoot>     HE </receiptsRoot>
         <logsBloom>        HB </logsBloom>
         <difficulty>       HD </difficulty>
         <number>           HI </number>
         <gasLimit>         HL </gasLimit>
         <gasUsed>          HG </gasUsed>
         <timestamp>        HS </timestamp>
         <extraData>        HX </extraData>
         <mixHash>          HM </mixHash>
         <blockNonce>       HN </blockNonce>

    syntax KItem ::= "#updateBlockHeader" [symbol(updateBlockHeader)]
 // -----------------------------------------------------------------
    rule <k> #updateBlockHeader
          => #updateParentHash
          ~> #startBlock
          ~> #incrementBlockNumber
          ~> #clearTxLists
          ~> #clearGas ... </k>

    syntax KItem ::= "#setAcctBalance" Int Int
 // ------------------------------------------
    rule <k> #setAcctBalance KEY BAL => .K ... </k>
         <traceBalance> TRBAL </traceBalance>
         <accounts>
           <account>
             <acctID> KEY </acctID>
             <balance> _ => BAL </balance>
             ...
           </account>
           ...
         </accounts>
         <currentBalanceMutations> CBM => #if TRBAL #then CBM[ KEY <- BAL ] #else CBM #fi </currentBalanceMutations>
endmodule

```