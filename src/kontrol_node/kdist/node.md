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
    imports MAP
    imports SERIALIZATION
    imports ETHEREUM-SIMULATION
    imports NO-CODE-SIZE-CHECKS
    imports EVM-TRACING
    imports STATE-JSON
    imports RPC-JSON
    imports TRACE-JSON
    imports KONTROL-NODE-CONFIG

    syntax EthereumSimulation ::= Start
    syntax Start ::= #start(
      String // IO directory
    ) [symbol(start)]

    configuration <simbolikVM/>
```

Create the initial configuration by reading the inputs from the IO directory

```k

  rule <k> #start( IO_DIR )
        => #unlockAccounts()
        ~> #loadStateDump( IO_DIR, 0)
        ~> #loadRpcRequests( IO_DIR )
        ~> #saveStateDump( IO_DIR )
        ...
       </k>
       <ioDir> _ => IO_DIR </ioDir>
```

  Unlocked test accounts. These are the same ten accounts used by most dev tools.
  Mnemonic: test test test test test test test test test test test junk

```k

  syntax KItem ::= #unlockAccounts()

  rule <k> #unlockAccounts() => .K ... </k>
    <accountKeys> _ =>
      #parseAddr("0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266") |-> #parseWord("0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80")
      #parseAddr("0x70997970C51812dc3A010C7d01b50e0d17dc79C8") |-> #parseWord("0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d")
      #parseAddr("0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC") |-> #parseWord("0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a")
      #parseAddr("0x90F79bf6EB2c4f870365E785982E1f101E93b906") |-> #parseWord("0x7c852118294e51e653712a81e05800f419141751be58f605c371e15141b007a6")
      #parseAddr("0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65") |-> #parseWord("0x47e179ec197488593b187f80a00eb0da91f1b9d0b13f8733639f19c30a34926a")
      #parseAddr("0x9965507D1a55bcC2695C58ba16FB37d819B0A4dc") |-> #parseWord("0x8b3a350cf5c34c9194ca85829a2df0ec3153be0318b5e2d3348e872092edffba")
      #parseAddr("0x976EA74026E726554dB657fA54763abd0C3a0aa9") |-> #parseWord("0x92db14e403b83dfe3df233f83dfa3a0d7096f21ca9b0d6d6b8d88b2b4ec1564e")
      #parseAddr("0x14dC79964da2C08b23698B3D3cc7Ca32193d9955") |-> #parseWord("0x4bbbf85ce3377467afe5d46f804f221813b2bb87f24d81f60f1fcdbf7cbf4356")
      #parseAddr("0x23618e81E3f5cdF7f54C3d65f7FBc0aBf5B21E8f") |-> #parseWord("0xdbda1821b80551c9d65939329250298aa3472ba22feea921c0cf5d620ea67b97")
      #parseAddr("0xa0Ee7A142d267C1f36714E4a8F75612F20a79720") |-> #parseWord("0x2a871d0798f97d79848a013d4936a73bf4cc922c825d33c1cf7073dff6d409c6")
    </accountKeys>
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
          ~> #validateTx TX_ID // checks gas
          ~> #updateTimestamp  // advances the block timestamp by some arbitrary delta
          ~> #executeTx TX_ID 
          ~> #finalizeBlock
          ~> #makeTxReceipts
          ~> #updateBlockHeader
          ~> #createTransactionHash()
          ~> #saveRpcResponse( IO_DIR )
          ...
          </k>
          <ioDir> IO_DIR </ioDir>
          <origin> FROM </origin>

    // ECDSASign returns [r,s,recid]
    // previously of EIP155, v is computed as:  v = recid + 27
    // post of EIP155, v is computed as :       v = 2 * CHAIN_ID + recid + 35

    syntax KItem ::= "#signTX" Int Int
                   | "#signTX" Int String
    
    // Sign a transaction with an account managed by this node
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

    // Sign a transaction with a given signature
    rule <k> #signTX TXID SIG:String => .K ... </k>
         <chainID> B </chainID>
         <message>
           <msgID> TXID </msgID>
           <sigR> _ => #parseHexBytes( substrString( SIG, 0, 64 ) )           </sigR>
           <sigS> _ => #parseHexBytes( substrString( SIG, 64, 128 ) )         </sigS>
           <sigV> _ => 2 *Int B +Int #parseHexWord( substrString( SIG, 128, 130 ) ) +Int 35 </sigV>
           ...
         </message>

    // Signing failed. TODO: Send error response and continue with next request
    rule <k> #signTX TXID ACCTFROM:Int => .K ... </k>
         <accountKeys> KEYMAP                      </accountKeys>
         <mode>        NORMAL                      </mode>
         <txPending>   ListItem(TXID) => .List ... </txPending>
         <txOrder>     ListItem(TXID) => .List ... </txOrder>
      requires notBool ACCTFROM in_keys(KEYMAP)


    syntax KItem ::= "#setup_G0" Int

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

    // Revert if insufficient gas
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

    // Sufficient gas
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
    rule <k> #updateTimestamp => .K ... </k> <timestamp> TS => TS +Int TD </timestamp> <timeDiff> TD </timeDiff>

    syntax KItem ::= "#executeTx" Int

    // Execute a contract creation transaction
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

    // Exeucte a contract call transaction
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

```

Transaction Receipts

```k
    syntax KItem ::= "#makeTxReceipts"
                   | "#makeTxReceiptsAux" List

    rule <k> #makeTxReceipts => #makeTxReceiptsAux TXLIST ... </k>
         <txOrder> TXLIST </txOrder>
    rule <k> #makeTxReceiptsAux .List => .K ... </k>
    rule <k> #makeTxReceiptsAux (ListItem(TXID) TXLIST) => #makeTxReceipt TXID ~> #makeTxReceiptsAux TXLIST ... </k>

    syntax KItem ::= "#makeTxReceipt" Int

    rule <k> #makeTxReceipt TXID => .K ... </k>
         <txReceipts>
           ( .Bag
          => <txReceipt>
               <txHash> #unparseDataBytes( #hashTxData( #getTxData (TXID ) ) ) </txHash>
               <txCumulativeGas> CGAS                           </txCumulativeGas>
               <logSet>          LOGS                           </logSet>
               <bloomFilter>     #bloomFilter(LOGS)             </bloomFilter>
               <txStatus>        bool2Word(SC ==K EVMC_SUCCESS) </txStatus>
               <txID>            TXID                           </txID>
               <sender>          ACCT                           </sender>
               <txBlockNumber>   BN                             </txBlockNumber>
             </txReceipt>
           )
           ...
         </txReceipts>
         <message>
           <msgID>    TXID </msgID>
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
    syntax KItem ::= "#updateBlockHeader"  [symbol(updateBlockHeader)]

    rule <k> #updateBlockHeader
          => #startBlock
          ... </k>
          <stateTrie>        TREE            </stateTrie> // TODO: We never set the initial trie
          <txReceipts>       TXRECEIPTS      </txReceipts> // TODO: Should these be cleared?
          <callState>
            <gas>              _  => 0         </gas>
            ...
          </callState>
          <network>
            <txOrder>          TXLIST => .List </txOrder>
            <txPending>        _      => .List </txPending>
            ...
          </network>
          <block>
            <previousHash>     PH => #blockHeaderHash(PH, HO, HC, HR, HT, HE, HB, HD, BN, HL, gas2Int( HG ), HS, HX, HM, HN)        </previousHash>
            <ommersHash>       HO              </ommersHash>
            <coinbase>         HC              </coinbase>
            <stateRoot>        HR => #parseHexWord( Keccak256( #rlpEncodeMerkleTree( TREE ) ) )</stateRoot>  // TODO: should <prevHash> use the old or new state root?
            <transactionsRoot> HT => #parseHexWord( Keccak256( #rlpEncodeMerkleTree( #transactionsRoot( TXLIST ) ) ) ) </transactionsRoot>
            <receiptsRoot>     HE => #parseHexWord( Keccak256( #rlpEncodeMerkleTree( #receiptsRoot( <txReceipts> TXRECEIPTS </txReceipts> ) ) ) ) </receiptsRoot>
            <logsBloom>        HB              </logsBloom>
            <difficulty>       HD              </difficulty>
            <number>           BN => BN +Int 1 </number>
            <gasLimit>         HL              </gasLimit>
            <gasUsed>          HG              </gasUsed>
            <timestamp>        HS              </timestamp>
            <extraData>        HX              </extraData>
            <mixHash>          HM              </mixHash>
            <blockNonce>       HN              </blockNonce>
            ...
          </block>
```

State Root
----------

```k
          syntax MerkleTree ::= #stateRoot ( NetworkCell, Schedule ) [function]
                              | #putAccountsInTrie( MerkleTree, AccountsCell ) [function]

          rule #stateRoot(
                  <network>
                    <accounts> ACCTSCELL </accounts>
                    ...
                  </network>,
                  SCHED
                )
              => #putAccountsInTrie(
                    MerkleUpdateMap(
                        .MerkleTree,
                        #precompiledAccountsMap(#precompiledAccountsSet(SCHED))
                    ),
                    <accounts> ACCTSCELL </accounts>
                  )

          rule #putAccountsInTrie( TREE, <accounts> .Bag </accounts> ) => TREE
          rule #putAccountsInTrie(
                  (TREE => MerkleUpdate(
                      TREE,
                      #parseByteStack( #unparseData(ACCT,20) ),
                      #unparseDataBytes( #rlpEncodeFullAccount(NONCE, BAL, STORAGE, CODE) )
                  )),
                  <accounts>
                    (<account>
                      <acctID>  ACCT    </acctID>
                      <nonce>   NONCE   </nonce>
                      <balance> BAL     </balance>
                      <storage> STORAGE </storage>
                      <code>    CODE    </code>
                      ...
                    </account> => .Bag)
                    ...
                  </accounts>
                )

```

Transactions Root
-----------------

```k
          syntax MerkleTree ::= #transactionsRoot( List )              [function]
                              | #transactionsRootAux( MerkleTree, Int, List ) [function]

          rule #transactionsRoot( TXLIST )
            => #transactionsRootAux( .MerkleTree, 0, TXLIST )
          
          rule #transactionsRootAux( TREE, _, .List ) => TREE
          rule #transactionsRootAux(
                  ( TREE => MerkleUpdate(
                      TREE,
                      #rlpEncodeWord(I),
                      #unparseDataBytes( #rlpEncodeTxData( #getTxData( TXID ) ) )
                  ) ),
                  ( I                => I +Int 1 ),
                  ( ListItem( TXID ) => .List ) _
                )

```

Receipts Root
-------------

```k
          syntax MerkleTree ::= #receiptsRoot( TxReceiptsCell )                     [function]
                              | #receiptsRootAux( MerkleTree, Int, TxReceiptsCell ) [function]


          rule #receiptsRoot( TXRECEIPTS )
            => #receiptsRootAux( .MerkleTree, 0, TXRECEIPTS )

          rule #receiptsRootAux( TREE, _, _ ) => TREE
          rule #receiptsRootAux(
                ( TREE           => MerkleUpdate(
                    TREE,
                    #rlpEncodeWord(I),
                    #unparseDataBytes( #rlpEncodeReceipt(TS, TG, TB, TL) ) )
                ),
                ( I              => I +Int 1 ),
                <txReceipts>
                    ( <txReceipt>
                      <txID>            TXID </txID>
                      <txStatus>        TS   </txStatus>
                      <txCumulativeGas> TG   </txCumulativeGas>
                      <bloomFilter>     TB   </bloomFilter>
                      <logSet>          TL   </logSet>
                      ...
                    </txReceipt> => .Bag )
                    ...
                </txReceipts>
              )


endmodule

```