```k
requires "foundry.md"
requires "driver.md"
requires "no_code_size_checks.md"
requires "trace.md"
requires "trace-json.md"
requires "state-json.md"
requires "config.md"
requires "json-utils.md"
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
    imports JSON-UTILS

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
###############################################################################
# eth_sendTransaction

When eth_sendTransaction is called, we sign it, apply the inrinsic gas costs,
execute it, mine a block including it, and return the transaction hash.
Additionally, we eagerly compute the transaction trace and and save it to disk.
Similarly, we save a state snapshot after the block was mined.

```k
    syntax KItem ::= "#ethSendTransactionResponse"

    rule <k> RPCRequest( REQ_ID, EthSendTransaction( FROM, TO, GAS_LIMIT, GAS_PRICE, VALUE, DATA ) )
            => #signTx(!TX_ID, FROM)
            ...
        </k>
        <rpcRequestID> _ => REQ_ID </rpcRequestID>
        <origin>       _ => FROM   </origin>
        <currentTxID>  _ => !TX_ID </currentTxID>
        <schedule>     SCHED       </schedule>
        <callState>
            <callGas> _ => G0(SCHED, DATA, (TO ==K .Account) ) </callGas>
            ...
        </callState>
        <block>
            <timestamp> TS => TS +Int 1 </timestamp>
            ...
        </block>
        <network>
            <chainID>  CHAIN_ID </chainID>
            <account>
            <acctID> FROM     </acctID> // TODO: What if FROM account does not exist yet?
            <nonce>  TXNONCE  </nonce>
            ...
            </account>
            <txOrder>   ... (.List => ListItem(!TX_ID )) </txOrder>
            <txPending> ... (.List => ListItem(!TX_ID )) </txPending>
            <messages>
                ( .Bag => 
                    <message>
                        <msgID>      !TX_ID    </msgID>
                        <txChainID>  CHAIN_ID  </txChainID>
                        <txNonce>    TXNONCE   </txNonce>
                        <txType>     Legacy    </txType>
                        <to>         TO        </to>
                        <txGasLimit> GAS_LIMIT </txGasLimit>
                        <txGasPrice> GAS_PRICE </txGasPrice>
                        <value>      VALUE     </value>
                        <data>       DATA      </data>
                        ...
                    </message>
                )
                ...
            </messages>
            ...
        </network>

    rule <k> #signTxError
        => RPCResponse({
                "code"    : -32000,
                "message" : "Could not sign transaction: account not found"
            })
        ~> #saveRpcResponse( IO_DIR )
        ...
        </k>
        <ioDir> IO_DIR </ioDir>

    rule <k> #signTxSuccess
        => #applyIntrinsicGas( TX_ID )
        ...
        </k>
        <currentTxID> TX_ID </currentTxID>

    rule <k> #intrinsicGasError( _ERR_CODE )
        => RPCResponse({
                "code"    : -32000,
                "message" : "Intrinsic gas error "
            })
        ~> #saveRpcResponse( IO_DIR )
        ...
        </k>
        <ioDir> IO_DIR </ioDir>

    rule <k> #intrinsicGasSuccess
        => #executeTx( TX_ID )
        ~> #finishTx
        ~> #finalizeTx(false, Ctxfloor(SCHED, DATA))
        ~> #finalizeBlock
        ~> #makeTxReceipts
        ~> #mineBlock
        ~> #ethSendTransactionResponse
        ~> #saveRpcResponse( IO_DIR )
        ~> #saveStateDump( IO_DIR )
        ...
        </k>
        <ioDir>       IO_DIR </ioDir>
        <currentTxID> TX_ID  </currentTxID>
        <schedule>    SCHED  </schedule>
        <message>
            <msgID> TX_ID </msgID>
            <data>  DATA  </data>
            ...
        </message>

    rule <k> #ethSendTransactionResponse
        => RPCResponse( intToHex( TX_HASH ) )
        ... </k>
        <currentTxID>  TXID    </currentTxID>
        <txReceipt>
            <txHash> TX_HASH </txHash>
            <txID>   TXID    </txID>
            ...
        </txReceipt>
```
###############################################################################
eth_getTransactionReceipt

```k
    rule <k> RPCRequest( REQ_ID, EthGetTransactionReceipt( TX_HASH ) )
        => RPCResponse({
                "type"              : "0x0",
                "transactionHash"   : intToHex( TX_HASH ),
                "transactionIndex"  : "0x0", // kontrol-node always includes exactly one tx per block
                "blockHash"         : intToHex( BLOCK_HASH ),
                "blockNumber"       : intToHex( BLOCK_NUMBER ),
                "from"              : intToHex( FROM ),
                "to"                : intToHex( TO ),
                "cumulativeGasUsed" : intToHex( CGAS ), // TODO: What is the difference between cumulativeGasUsed and gasUsed
                "gasUsed"           : intToHex( CGAS ), 
                "contractAddress"   : #if TO ==K .Account #then intToHex( #newAddr(FROM, TX_NONCE) ) #else null #fi,
                "logs"              : [ .JSONs ], // TODO
                "logsBloom"         : "", // TODO
                "status"            : #if TX_STATUS ==K EVMC_SUCCESS #then "1" #else "0" #fi,
                "effectiveGasPrice" : "0" // TODO
            })
            ~> #saveRpcResponse( IO_DIR )
            ...
        </k>
        <ioDir>        IO_DIR      </ioDir>
        <rpcRequestID> _ => REQ_ID </rpcRequestID>
        <currentTxID>         TXID                           </currentTxID>
        <txReceipt>
            <txHash>          TX_HASH                        </txHash>
            <txCumulativeGas> CGAS                           </txCumulativeGas>
            <logSet>          _                              </logSet>
            <bloomFilter>     _                              </bloomFilter>
            <txStatus>        TX_STATUS                      </txStatus>
            <txID>            TXID                           </txID>
            <sender>          FROM                           </sender>
            <txBlockNumber>   BLOCK_NUMBER                   </txBlockNumber>
        </txReceipt>
        <message>
            <msgID>        TXID                           </msgID>
            <txNonce>      TX_NONCE                       </txNonce>
            <to>           TO                             </to>
            ...
        </message>
        <block>
            <previousHash> BLOCK_HASH                     </previousHash>
            ...
        </block>
```

###############################################################################
eth_getTransactionByHash

```k
    rule <k> RPCRequest( REQ_ID, EthGetTransactionByHash( TX_HASH ) )
        => RPCResponse({
                "type"             : "0x0",
                "nonce"            : intToHex( TX_NONCE ),
                "to"               : intToHex( TO ), // TODO: null for contract creation
                "gas"              : intToHex( GAS_LIMIT ),
                "value"            : intToHex( VALUE ),
                "input"            : bytesToHex( DATA ),
                "gasPrice"         : intToHex( GAS_PRICE ),
                "chainId"          : intToHex( CHAIN_ID ),
                "v"                : intToHex( SIG_V ),
                "r"                : bytesToHex( SIG_R ),
                "s"                : bytesToHex( SIG_S )
            })
            ~> #saveRpcResponse( IO_DIR )
            ...
        </k>
        <ioDir>        IO_DIR      </ioDir>
        <rpcRequestID> _ => REQ_ID </rpcRequestID>
        <txReceipt>
            <txHash> TX_HASH </txHash>
            <txID>   TXID    </txID>
            ...
        </txReceipt>
        <message>
            <msgID>      TXID      </msgID>
            <txNonce>    TX_NONCE  </txNonce>
            <to>         TO        </to>
            <txGasLimit> GAS_LIMIT </txGasLimit>
            <txGasPrice> GAS_PRICE </txGasPrice>
            <value>      VALUE     </value>
            <data>       DATA      </data>
            <txChainID>  CHAIN_ID  </txChainID>
            <sigV>       SIG_V     </sigV>
            <sigR>       SIG_R     </sigR>
            <sigS>       SIG_S     </sigS>
            ...
        </message>
```

===============================================================================
eth_getCode

```k
    rule <k> RPCRequest( REQ_ID, EthGetCode( ADDR, _BLOCK_NUM ) ) // TODO: block number
        => RPCResponse( bytesToHex(CODE) )
        ~> #saveRpcResponse( IO_DIR )
        ...
        </k>
        <ioDir>        IO_DIR      </ioDir>
        <rpcRequestID> _ => REQ_ID </rpcRequestID>
        <account>
            <acctID> ADDR </acctID>
            <code>   CODE </code>
            ...
        </account>
```

===============================================================================
eth_getBlockByNumber

```k
    syntax KItem ::= "#ethGetBlockByNumberResponse"

    rule <k> RPCRequest( REQ_ID, EthGetBlockByNumber( BLOCK_NUMBER) )
            => #setBlockData( #getBlockData( BLOCK_NUMBER ) )
            ~> #ethGetBlockByNumberResponse
            ~> #saveRpcResponse( IO_DIR )
            ~> #setBlockData( #getBlockData( ORIGINAL_BLOCK_NUMBER ) )
            ...
            </k>
            <ioDir>        IO_DIR      </ioDir>
            <rpcRequestID> _ => REQ_ID </rpcRequestID>
            <block>
                <number> ORIGINAL_BLOCK_NUMBER </number>
                ...
            </block>

    rule <k> #ethGetBlockByNumberResponse
            => RPCResponse({
                "hash"             : intToHex( 0 ), // TODO
                "parentHash"       : intToHex( PREV_HASH ),
                "sha3Uncles"       : intToHex( OMMERS_HASH ),
                "miner"            : intToHex( MINER ),
                "stateRoot"        : intToHex( STATE_ROOT ),
                "transactionsRoot" : intToHex( TRANSACTIONS_ROOT ),
                "receiptsRoot"     : intToHex( RECEIPTS_ROOT ),
                "logsBloom"        : "0x0", // TODO
                "difficulty"       : intToHex( BLOCK_DIFFICULTY ),
                "number"           : intToHex( BLOCK_NUMBER ),
                "gasLimit"         : intToHex( GAS_LIMIT ),
                "gasUsed"          : intToHex( GAS_USED ),
                "timestamp"        : intToHex( BLOCK_TIMESTAMP ),
                "extraData"        : bytesToHex( EXTRA_DATA ),
                "mixHash"          : intToHex( MIX_HASH ),
                "nonce"            : intToHex( NONCE ),
                "size"             : "0x0", // TODO
                "transactions"     : [ .JSONs ], // TODO
                "uncles"           : [ .JSONs ]  // TODO
            })
            ... </k>
            <block>
            <previousHash>     PREV_HASH        </previousHash>
            <ommersHash>       OMMERS_HASH      </ommersHash>
            <coinbase>         MINER            </coinbase>
            <stateRoot>        STATE_ROOT       </stateRoot>
            <transactionsRoot> TRANSACTIONS_ROOT </transactionsRoot>
            <receiptsRoot>     RECEIPTS_ROOT    </receiptsRoot>
            <difficulty>       BLOCK_DIFFICULTY </difficulty>
            <number>           BLOCK_NUMBER     </number>
            <gasLimit>         GAS_LIMIT        </gasLimit>
            <gasUsed>          GAS_USED         </gasUsed>
            <timestamp>        BLOCK_TIMESTAMP  </timestamp>
            <extraData>        EXTRA_DATA       </extraData>
            <mixHash>          MIX_HASH         </mixHash>
            <blockNonce>       NONCE            </blockNonce>
            ...
            </block>
```

===============================================================================
eth_getBlockByHash

```k

    rule <k> RPCRequest( REQ_ID, EthGetBlockByHash( BLOCK_HASH) )
            => #setBlockData( #getBlockData( BLOCK_HASH ) )
            ~> #ethGetBlockByNumberResponse
            ~> #saveRpcResponse( IO_DIR )
            ~> #setBlockData( #getBlockData( ORIGINAL_BLOCK_NUMBER ) )
            ...
            </k>
            <ioDir>        IO_DIR      </ioDir>
            <rpcRequestID> _ => REQ_ID </rpcRequestID>
            <block>
                <number> ORIGINAL_BLOCK_NUMBER </number>
                ...
            </block>
```

===============================================================================
eth_getTransactionCount

```k
    rule <k> RPCRequest( REQ_ID, EthGetTransactionCount( ADDR, _BLOCK_NUM ) ) // TODO: block number
          => RPCResponse( intToHex( NONCE ) )
          ~> #saveRpcResponse( IO_DIR )
          ...
        </k>
        <ioDir>        IO_DIR      </ioDir>
        <rpcRequestID> _ => REQ_ID </rpcRequestID>
        <account>
            <acctID> ADDR  </acctID>
            <nonce>  NONCE </nonce>
            ...
        </account>
```

===============================================================================
eth_getStorageAt

```k
    rule <k> RPCRequest( REQ_ID, EthGetStorageAt( ADDR, SLOT, _BLOCK_NUM ) ) // TODO: block number
        => RPCResponse( intToHex( {STORAGE[ SLOT ] orDefault 0}:>Int ) )
        ~> #saveRpcResponse( IO_DIR )
        ...
        </k>
        <ioDir>        IO_DIR      </ioDir>
        <rpcRequestID> _ => REQ_ID </rpcRequestID>
        <account>
            <acctID>  ADDR    </acctID>
            <storage> STORAGE </storage>
            ...
        </account>
```

===============================================================================
anvil_stateDump

```k
    rule <k> RPCRequest( REQ_ID, AnvilStateDump() )
        => RPCResponse(
                #let CONTENTS:IOString = #readFile( #stateDumpFile( IO_DIR, BLOCK_NUMBER ) )
                #in String2JSON( {CONTENTS}:>String )
           )
        ~> #saveRpcResponse( IO_DIR )
        ...
        </k>
        <ioDir>        IO_DIR      </ioDir>
        <rpcRequestID> _ => REQ_ID </rpcRequestID>
        <number> BLOCK_NUMBER </number>

```

===============================================================================
debug_traceTransaction

At the point the debug_traceTransaction method is called, the transaction has already been
processed and its trace stored on disk. We just need to read the trace and return it.
Since the trace can be large, we avoid loading it into memory as a JSON object, and 
just build the response string directly.

```k

    rule <k> RPCRequest( REQ_ID, DebugTraceTransaction( TX_HASH ) )
        => #writeFile( #responseFile( IO_DIR, REQ_ID ),
            "{ \"jsonrpc\": \"2.0\"" +String
            ", \"id\": " +String intToHex( REQ_ID ) +String
            ", \"result\": " +String
                "{ \"failed\":" +String #if TX_STATUS ==Int 1 #then "true" #else "false" #fi +String
                ", \"gas\":" +String Int2String( TX_CUMULATIVE_GAS ) +String
                ", \"return_value\": \"0x\"" +String // TODO
                ", \"structLogs\": [" +String {#readFile( #traceFile( IO_DIR, TXID) )}:>String +String
            "] } }"
        ) ...
        </k>
        <ioDir>        IO_DIR      </ioDir>
        <rpcRequestID> _ => REQ_ID </rpcRequestID>
        <txReceipt>
            <txHash> TX_HASH </txHash>
            <txID>   TXID    </txID>
            <txCumulativeGas> TX_CUMULATIVE_GAS </txCumulativeGas>
            <txStatus> TX_STATUS </txStatus>
            ...
        </txReceipt>

```



Transaction Signing
-------------------

```k

    // ECDSASign returns [r,s,recid]
    // previously of EIP155, v is computed as:  v = recid + 27
    // post of EIP155, v is computed as :       v = 2 * CHAIN_ID + recid + 35

    syntax KItem ::= #signTx(Int, Int)
                   | #signTx(Int, String)
                   | "#signTxSuccess"
                   | "#signTxError"
    
    // Sign a transaction with an account managed by this node
    rule <k> #signTx(TXID, ACCTFROM:Int)
          => #signTx(TXID, ECDSASign( Keccak256raw(#rlpEncodeTxData(#getTxData(TXID))), #padToWidth( 32, #asByteStack(KEY))))
          ...
        </k>
        <accountKeys> ... ACCTFROM |-> KEY ... </accountKeys>
        <mode> NORMAL </mode>
         <message>
           <msgID> TXID </msgID>
           ...
         </message>
    
    // Error signing a transaction with an unknown account
    rule <k> #signTx(TXID, ACCTFROM:Int) => #signTxError ... </k>
         <accountKeys> KEYMAP                      </accountKeys>
         <mode>        NORMAL                      </mode>
         <txPending>   ListItem(TXID) => .List ... </txPending> // TODO: Is this the best place to remove the tx from pending?
         <txOrder>     ListItem(TXID) => .List ... </txOrder>
      requires notBool ACCTFROM in_keys(KEYMAP)
  
    // Sign a transaction with a given signature
    rule <k> #signTx(TXID, SIG:String) => #signTxSuccess ... </k>
         <chainID> B </chainID>
         <message>
           <msgID> TXID </msgID>
           <sigR> _ => #parseHexBytes( substrString( SIG, 0, 64 ) )           </sigR>
           <sigS> _ => #parseHexBytes( substrString( SIG, 64, 128 ) )         </sigS>
           <sigV> _ => 2 *Int B +Int #parseHexWord( substrString( SIG, 128, 130 ) ) +Int 35 </sigV>
           ...
         </message>

    syntax KItem ::= #applyIntrinsicGas( Int )
                   | "#intrinsicGasSuccess"
                   | #intrinsicGasError( ExceptionalStatusCode )

    // Revert if insufficient gas
    rule <k> #applyIntrinsicGas( TXID )
          => #intrinsicGasError( #if BAL <Int GLIMIT *Int GPRICE #then EVMC_BALANCE_UNDERFLOW #else EVMC_OUT_OF_GAS #fi)
          ...
         </k>
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
    rule <k> #applyIntrinsicGas( TXID )
          => #intrinsicGasSuccess ... </k>
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

    syntax KItem ::= #executeTx( Int )

    // Execute a contract creation transaction
    rule <k> #executeTx( TXID:Int )
          => #accessAccounts ACCTFROM #newAddr(ACCTFROM, NONCE) #precompiledAccountsSet(SCHED)
          ~> #loadAccessList(TA)
          ~> #create ACCTFROM #newAddr(ACCTFROM, NONCE) VALUE CODE
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
    rule <k> #executeTx( TXID:Int )
          => #accessAccounts ACCTFROM ACCTTO #precompiledAccountsSet(SCHED)
          ~> #loadAccessList(TA)
          ~> #call ACCTFROM ACCTTO ACCTTO VALUE VALUE DATA false
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
           ( .Bag =>
            <txReceipt>
                <txHash>          #asInteger( #hashTxData( #getTxData(TXID ) ) ) </txHash>
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
    syntax KItem ::= "#mineBlock"  [symbol(mineBlock)]
                   | #setBlockData( BlockData )

    syntax BlockData ::= #getBlockData( Int )        [function]
    syntax Int       ::= #hashBlockData( BlockData ) [function]

    rule <k> #mineBlock => #startBlock ... </k>
          <stateTrie>  TREE       </stateTrie> // TODO: We never set the initial trie
          <txReceipts> TXRECEIPTS </txReceipts> // TODO: Should these be cleared?
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
                <number>           BN => BN +Int 1 </number>
                <previousHash>     _  =>  #hashBlockData( #getBlockData( BN ) ) </previousHash>
                <stateRoot>        _  => #parseHexWord( Keccak256( #rlpEncodeMerkleTree( TREE ) ) )</stateRoot>
                <transactionsRoot> _  => #parseHexWord( Keccak256( #rlpEncodeMerkleTree( #transactionsRoot( TXLIST ) ) ) ) </transactionsRoot>
                <receiptsRoot>     _  => #parseHexWord( Keccak256( #rlpEncodeMerkleTree( #receiptsRoot( <txReceipts> TXRECEIPTS </txReceipts> ) ) ) ) </receiptsRoot>
                ...
          </block>
          <blockStorage> M => M[ BN                                    <- #getBlockData( BN )]
                               [ #hashBlockData( #getBlockData( BN ) ) <- #getBlockData( BN )]
          </blockStorage>
       

    syntax BlockData ::= BlockData(
        Int, // previousHash
        Int, // ommersHash
        Int, // coinbase
        Int, // stateRoot
        Int, // transactionsRoot
        Int, // receiptsRoot
        Bytes, // logsBloom
        Int, // difficulty
        Int, // number
        Int, // gasLimit
        Gas, // gasUsed
        Int, // timestamp
        Bytes, // extraData
        Int, // mixHash
        Int, // blockNonce
        Int, // base fee
        Int, // withdrawalsRoot
        Int, // blobGasUsed
        Int, // excessBlobGas
        Int, // beaconRoot
        Int, // requestsRoot
        JSON // omnersBlockHeaders
    )

    rule [[ #getBlockData( BN ) => BlockData(
        PH, HO, HC, HR, HT, HE, HB, HD, BN, HL, HG, HS, HX, HM, HN, BF, WR, BG, EG, BR, RR, OBH
    ) ]]
        <block>
            <previousHash>     PH </previousHash>
            <ommersHash>       HO </ommersHash>
            <coinbase>         HC </coinbase>
            <stateRoot>        HR </stateRoot>
            <transactionsRoot> HT </transactionsRoot>
            <receiptsRoot>     HE </receiptsRoot>
            <logsBloom>        HB </logsBloom>
            <difficulty>       HD </difficulty>
            <number>           BN </number>
            <gasLimit>         HL </gasLimit>
            <gasUsed>          HG </gasUsed>
            <timestamp>        HS </timestamp>
            <extraData>        HX </extraData>
            <mixHash>          HM </mixHash>
            <blockNonce>       HN </blockNonce>
            <baseFee>          BF </baseFee>
            <withdrawalsRoot>  WR </withdrawalsRoot>
            <blobGasUsed>      BG </blobGasUsed>
            <excessBlobGas>    EG </excessBlobGas>
            <beaconRoot>       BR </beaconRoot>
            <requestsRoot>     RR </requestsRoot>
            <ommerBlockHeaders> OBH </ommerBlockHeaders>
        </block>

    rule [[ #getBlockData( BN ) => {BLOCK_STORAGE[ BN ]}:>BlockData ]]
        <blockStorage> BLOCK_STORAGE:Map </blockStorage>
        <number> CURRENT_BN </number>
        requires BN =/=Int CURRENT_BN andBool BN in_keys(BLOCK_STORAGE)

    rule <k> #setBlockData( BlockData(
            PH, HO, HC, HR, HT, HE, HB, HD, BN, HL, HG, HS, HX, HM, HN, BF, WR, BG, EG, BR, RR, OBH
         ))
        => .K ... </k>
        <block>
            <previousHash>     _ => PH </previousHash>
            <ommersHash>       _ => HO </ommersHash>
            <coinbase>         _ => HC </coinbase>
            <stateRoot>        _ => HR </stateRoot>
            <transactionsRoot> _ => HT </transactionsRoot>
            <receiptsRoot>     _ => HE </receiptsRoot>
            <logsBloom>        _ => HB </logsBloom>
            <difficulty>       _ => HD </difficulty>
            <number>           _ => BN </number>
            <gasLimit>         _ => HL </gasLimit>
            <gasUsed>          _ => HG </gasUsed>
            <timestamp>        _ => HS </timestamp>
            <extraData>        _ => HX </extraData>
            <mixHash>          _ => HM </mixHash>
            <blockNonce>       _ => HN </blockNonce>
            <baseFee>          _ => BF </baseFee>
            <withdrawalsRoot>  _ => WR </withdrawalsRoot>
            <blobGasUsed>      _ => BG </blobGasUsed>
            <excessBlobGas>    _ => EG </excessBlobGas>
            <beaconRoot>       _ => BR </beaconRoot>
            <requestsRoot>     _ => RR </requestsRoot>
            <ommerBlockHeaders> _ => OBH </ommerBlockHeaders>
        </block>


    rule #hashBlockData(BlockData(
            PH, HO, HC, HR, HT, HE, HB, HD, BN, HL, HG, HS, HX, HM, HN, _BF, _WR, _BG, _EG, _BR, _RR, _OBH
         ))
        => #blockHeaderHash(PH, HO, HC, HR, HT, HE, HB, HD, BN, HL, gas2Int( HG ), HS, HX, HM, HN)
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