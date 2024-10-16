```k
requires "foundry.md"
requires "driver.md"

module KONTROL-NODE
    imports FOUNDRY
    imports ETHEREUM-SIMULATION

    syntax RPCRequest ::= ".RPCRequest" [symbol(EmptyRPCRequest)]
 // -------------------------------------------------------------

    syntax RPCResponse ::= String | Int
                         | ".RPCResponse" [symbol(EmptyRPCResponse)]
 // ----------------------------------------------------------------

    configuration <simbolikVM>
                    <foundry/>
                    <rpcResponse> .RPCResponse </rpcResponse>
                    <accountKeys> .Map </accountKeys>
                    <timeFreeze> true </timeFreeze>
                    <timeDiff> 0 </timeDiff>
                    <currentTxID> 0 </currentTxID>
                    <txReceipts>
                      <txReceipt multiplicity ="*" type="Map">
                        <txHash>          "":String  </txHash>
                        <txCumulativeGas> 0          </txCumulativeGas>
                        <logSet>          .List      </logSet>
                        <bloomFilter>     .Bytes     </bloomFilter>
                        <txStatus>        0          </txStatus>
                        <txID>            0          </txID>
                        <sender>          .Account   </sender>
                        <txBlockNumber>   0          </txBlockNumber>
                        <contractAddress> .Account   </contractAddress>
                      </txReceipt>
                    </txReceipts>
                  </simbolikVM>
```

  Transaction debugging
  ---------------------
  Once debug_traceTransaction get up and running in a PR, these changes below should be moved to Kontrol:trace.md.

```k
    syntax TraceItem ::= "{" Int "|" OpCode "|" WordStack "|" Bytes "|" Map "|" Int "|" Int "}" [symbol(traceItem)]
 // ---------------------------------------------------------------------------------------------------------------
    rule <k> #next [ OPC ] ... </k>
         <activeTracing>  true          </activeTracing>
         <traceStorage>   DSTG          </traceStorage>
         <traceWordStack> DSTK          </traceWordStack>
         <traceMemory>    DMEM          </traceMemory>
         <recordedTrace>  false => true </recordedTrace>
         <pc>             PCOUNT        </pc>
         <wordStack>      WS            </wordStack>
         <callDepth>      CD            </callDepth>
         <localMem>       MEM           </localMem>
         <id>             ACCT          </id>
         <gas>            GA            </gas>
         <account>
           <acctID>  ACCT    </acctID>
           <storage> STORAGE </storage>
           ...
         </account>
         <traceData>
           ...
           .List => ListItem({ PCOUNT
                             | OPC
                             | #if DSTK ==K true #then WS      #else .WordStack #fi
                             | #if DMEM ==K true #then MEM     #else .Bytes     #fi
                             | #if DSTG ==K true #then STORAGE #else .Map       #fi
                             | CD | GA
                             })
         </traceData> [priority(24)]
```
  Transaction Signing and execution
  ---------------------------------

  The next block of K code contains the set of functions used to implement `eth_sendTransaction`.
  The information send with the request is used to load a new `<message>` cell, sign, validate, and execute it.
  Once these steps are performed, a receipt is generated.

```k
    syntax RPCRequest ::= "#eth_sendTransaction" TxType Account Account Int Int Int Int Bytes [symbol(eth_sendTransaction)]
 // -----------------------------------------------------------------------------------------------------------------------
    rule <k> #eth_sendTransaction TXTYPE ACCTFROM ACCTTO TXGAS TXGASPRICE TXVALUE TXNONCE TXDATA
          => mkTX !TXID
          ~> #loadTransaction !TXID TXTYPE ACCTFROM ACCTTO TXGAS TXGASPRICE TXVALUE TXNONCE TXDATA
          ~> #runTransaction !TXID ACCTFROM
          ~> #makeTxReceipt !TXID
          // ~> #mineBlock
          ... </k>

    syntax KItem ::= "#loadTransaction" Int TxType Account Account Int Int Int Int Bytes
 // ------------------------------------------------------------------------------------
    rule <k> #loadTransaction TXID TXTYPE ACCTFROM ACCTTO TXGAS TXGASPRICE TXVALUE TXNONCE TXDATA
          => #signTX TXID ACCTFROM
          ...
         </k>
         <chainID> CID </chainID>
         <currentTxID> _ => TXID </currentTxID>
         <message>
           <msgID> TXID </msgID>
           <txNonce>    _ => TXNONCE    </txNonce>
           <txGasPrice> _ => TXGASPRICE </txGasPrice>
           <txGasLimit> _ => TXGAS      </txGasLimit>
           <to>         _ => ACCTTO     </to>
           <value>      _ => TXVALUE    </value>
           <data>       _ => TXDATA     </data>
           <txChainID>  _ => CID        </txChainID>
           <txType>     _ => TXTYPE     </txType>
           ...
         </message>
         <account> <acctID> ACCTFROM </acctID> <nonce> TXNONCE </nonce> ... </account>



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

    syntax KItem ::= "#runTransaction" Int Account
 // ----------------------------------------------
    rule <k> #runTransaction TXID:Int ACCTFROM
          => #setup_G0 TXID
          ~> #validateTx TXID
          ~> #updateTimestamp
          ~> #executeTx TXID
          ...
          </k>
         <origin> _ => ACCTFROM </origin>

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
          ~> #finalizeTx(false)
         ...
         </k>
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

    rule <k> #executeTx TXID:Int
          => #accessAccounts ACCTFROM ACCTTO #precompiledAccountsSet(SCHED)
          ~> #loadAccessList(TA)
          ~> #call ACCTFROM ACCTTO ACCTTO VALUE VALUE DATA false
          ~> #finishTx
          ~> #finalizeTx(false)
         ...
         </k>
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
    syntax KItem ::= "#mineBlock"
 // -----------------------------
    rule <k> #mineBlock
          => #finalizeBlock
          ~> #updateParentHash
      //  ~> #updateStateTrie
      //  ~> #updateTrieRoots
          ~> #incrementBlockNumber
          ~> #startBlock
          ~> #cleanTxLists
          ~> #clearGas
          ...
         </k>

    syntax KItem ::= "#updateParentHash"
                   | "#incrementBlockNumber"
              //   | "#updateTrieRoots"
              //   | "#updateStateRoot"
              //   | "#updateTransactionsRoot"
              //   | "#updateReceiptsRoot"
              //   | "#initStateTrie"
              //   | "#updateStateTrie"
                   | "#cleanTxLists"
                   | "#clearGas"
                   | #updateStateTrie ( JSONs )
 // -------------------------------------------

    rule <k> #updateParentHash => .K ... </k>
         <previousHash> HP => #blockHeaderHash(HP, HO, HC, HR, HT, HE, HB, HD, HI, HL, HG, HS, HX, HM, HN) </previousHash>
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

    rule <k> #incrementBlockNumber => .K ... </k> <number> BN => BN +Int 1 </number>

    rule <k> #cleanTxLists => .K ... </k>
         <txPending> _ => .List </txPending>
         <txOrder>   _ => .List </txOrder>

    rule <k> #clearGas => .K ... </k> <gas> _ => 0 </gas>
```

  Helper Funcs
  ------------

```k
    syntax KItem ::= "#acctFromPrivateKey" String Int [symbol(acctFromPrivateKey)]
 // ------------------------------------------------------------------------------
    rule <k> #acctFromPrivateKey KEYSTR BAL => #newAccount #addrFromPrivateKey(KEYSTR) ~> #setAcctBalance #addrFromPrivateKey(KEYSTR) BAL ... </k>
         <accountKeys> M => M[#addrFromPrivateKey(KEYSTR) <- #parseHexWord(KEYSTR)] </accountKeys>
         <rpcResponse> _ => #addrFromPrivateKey(KEYSTR) </rpcResponse>

    syntax KItem ::= "#setAcctBalance" Int Int
 // ------------------------------------------
    rule <k> #setAcctBalance KEY BAL => .K ... </k>
            <accounts>
              <account>
                <acctID> KEY </acctID>
                <balance> _ => BAL </balance>
                ...
              </account>
              ...
            </accounts>
endmodule

```