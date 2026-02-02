```k
requires "config.md"
requires "driver.md"
requires "foundry.md"
requires "fs.md"
requires "json.md"
requires "json-utils.md"
requires "no_code_size_checks.md"
requires "trace.md"
requires "trace-json.md"

module KONTROL-NODE
    imports ETHEREUM-SIMULATION
    imports EVM-TRACING
    imports FILE-SYSTEM
    imports FOUNDRY
    imports JSON
    imports JSON-UTILS
    imports KONTROL-NODE-CONFIG
    imports MAP
    imports NO-CODE-SIZE-CHECKS
    imports SERIALIZATION
    imports TRACE-JSON

    syntax EthereumSimulation ::= Start

    syntax Start ::= #start( String ) [symbol(start)]

    rule <k> #start( IO_DIR )
        => #unlockAccounts()
        ~> #loadLatestSnapshot
        ~> #loadRpcRequest
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
            #parseAddr("0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266") |-> #padToWidth( 32, #parseByteStack("0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"))
            #parseAddr("0x70997970C51812dc3A010C7d01b50e0d17dc79C8") |-> #padToWidth( 32, #parseByteStack("0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"))
            #parseAddr("0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC") |-> #padToWidth( 32, #parseByteStack("0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a"))
            #parseAddr("0x90F79bf6EB2c4f870365E785982E1f101E93b906") |-> #padToWidth( 32, #parseByteStack("0x7c852118294e51e653712a81e05800f419141751be58f605c371e15141b007a6"))
            #parseAddr("0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65") |-> #padToWidth( 32, #parseByteStack("0x47e179ec197488593b187f80a00eb0da91f1b9d0b13f8733639f19c30a34926a"))
            #parseAddr("0x9965507D1a55bcC2695C58ba16FB37d819B0A4dc") |-> #padToWidth( 32, #parseByteStack("0x8b3a350cf5c34c9194ca85829a2df0ec3153be0318b5e2d3348e872092edffba"))
            #parseAddr("0x976EA74026E726554dB657fA54763abd0C3a0aa9") |-> #padToWidth( 32, #parseByteStack("0x92db14e403b83dfe3df233f83dfa3a0d7096f21ca9b0d6d6b8d88b2b4ec1564e"))
            #parseAddr("0x14dC79964da2C08b23698B3D3cc7Ca32193d9955") |-> #padToWidth( 32, #parseByteStack("0x4bbbf85ce3377467afe5d46f804f221813b2bb87f24d81f60f1fcdbf7cbf4356"))
            #parseAddr("0x23618e81E3f5cdF7f54C3d65f7FBc0aBf5B21E8f") |-> #padToWidth( 32, #parseByteStack("0xdbda1821b80551c9d65939329250298aa3472ba22feea921c0cf5d620ea67b97"))
            #parseAddr("0xa0Ee7A142d267C1f36714E4a8F75612F20a79720") |-> #padToWidth( 32, #parseByteStack("0x2a871d0798f97d79848a013d4936a73bf4cc922c825d33c1cf7073dff6d409c6"))
        </accountKeys>
```
###############################################################################
# Requests

## eth_chainId

```k
    rule <k> RPCRequest( REQ_ID, EthChainId() ) 
        => RPCResponse( CHAIN_ID )
        ...
        </k>
        <rpcRequestID> _ => REQ_ID </rpcRequestID>
        <chainID> CHAIN_ID </chainID>
```

###############################################################################
## eth_sendTransaction

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
            <caller>  _ => FROM </caller>
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
        ...
        </k>

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
        ...
        </k>

    rule <k> #intrinsicGasSuccess
        => #executeTx( TX_ID )
        ~> #finishTx
        ~> #finalizeTx(false, Ctxfloor(SCHED, DATA))
        ~> #finalizeBlock
        ~> #makeTxReceipts
        ~> #mineBlock
        ~> #saveStateDump
        ~> #saveMetadata
        ~> #ethSendTransactionResponse
        ...
        </k>
        <currentTxID> TX_ID  </currentTxID>
        <schedule>    SCHED  </schedule>
        <message>
            <msgID> TX_ID </msgID>
            <data>  DATA  </data>
            ...
        </message>

    rule <k> #ethSendTransactionResponse
        => RPCResponse( bytesToHex( TX_HASH ) )
        ... </k>
        <currentTxID>  TXID    </currentTxID>
        <txReceipt>
            <txHash> TX_HASH </txHash>
            <txID>   TXID    </txID>
            ...
        </txReceipt>
```
###############################################################################
## eth_getTransactionReceipt

```k
    rule <k> RPCRequest( REQ_ID, EthGetTransactionReceipt( TX_HASH ) )
        => RPCResponse({
                "type"              : "0x0",
                "transactionHash"   : bytesToHex( TX_HASH ),
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
            ...
        </k>
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
## eth_getTransactionByHash

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
            ...
        </k>
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

## eth_getCode

```k
    rule <k> RPCRequest( REQ_ID, EthGetCode( ADDR, _BLOCK_NUM ) ) // TODO: block number
        => RPCResponse( bytesToHex(CODE) )
        ...
        </k>
        <rpcRequestID> _ => REQ_ID </rpcRequestID>
        <account>
            <acctID> ADDR </acctID>
            <code>   CODE </code>
            ...
        </account>
```

## eth_getBalance

```k
    rule <k> RPCRequest( REQ_ID, EthGetBalance( ADDR, _BLOCK_NUM ) ) // TODO: block number
        => RPCResponse( intToHex( ACCT_BALANCE ) )
        ...
        </k>
        <rpcRequestID> _ => REQ_ID </rpcRequestID>
        <account>
            <acctID> ADDR </acctID>
            <balance> ACCT_BALANCE </balance>
            ...
        </account>
```

###############################################################################
## eth_getBlockByNumber

```k
    syntax KItem ::= #ethGetBlockResponse( BlockData )

    rule <k> RPCRequest( REQ_ID, EthGetBlockByNumber( BLOCK_NUMBER, _HYDRATED_TXS ) ) // TODO: hydrated txs
            => #ethGetBlockResponse( #getBlockData( BLOCK_NUMBER ) )
            ...
            </k>
            <rpcRequestID> _ => REQ_ID </rpcRequestID>

    rule <k> #ethGetBlockResponse( ( BlockData(
            PH, HO, HC, HR, HT, HE, HB, HD, BN, HL, HG, HS, HX, HM, HN, BF, WR, BG, EG, BR, RR, OBH
         )) )
            => RPCResponse({
                "hash"             : #hashBlockData( BlockData(
                    PH, HO, HC, HR, HT, HE, HB, HD, BN, HL, HG, HS, HX, HM, HN, BF, WR, BG, EG, BR, RR, OBH
                )),
                "parentHash"       : intToHex( PH ),
                "sha3Uncles"       : intToHex( HO ),
                "miner"            : intToHex( HC ),
                "stateRoot"        : intToHex( HR ),
                "transactionsRoot" : intToHex( HT ),
                "receiptsRoot"     : intToHex( HE ),
                "logsBloom"        : bytesToHex( HB ),
                "difficulty"       : intToHex( HD ),
                "number"           : intToHex( BN ),
                "gasLimit"         : intToHex( HL ),
                "gasUsed"          : intToHex( HG ),
                "timestamp"        : intToHex( HS ),
                "extraData"        : bytesToHex( HX ),
                "mixHash"          : intToHex( HM ),
                "nonce"            : intToHex( HN ),
                "size"             : "0x1",
                "transactions"     : [ .JSONs ], // TODO
                "uncles"           : [ .JSONs ]  // TODO
            })
            ... </k>
```

###############################################################################
## eth_getBlockByHash

```k

    rule <k> RPCRequest( REQ_ID, EthGetBlockByHash( BLOCK_HASH, _HYDRATED_TXS ) ) // TODO: hydrated txs
            => #ethGetBlockResponse( #getBlockDataByHash( BLOCK_HASH ) )
            ...
            </k>
            <rpcRequestID> _ => REQ_ID </rpcRequestID>
```

###############################################################################
## eth_getTransactionCount

```k
    rule <k> RPCRequest( REQ_ID, EthGetTransactionCount( ADDR, _BLOCK_NUM ) ) // TODO: block number
          => RPCResponse( intToHex( NONCE ) )
          ...
        </k>
        <rpcRequestID> _ => REQ_ID </rpcRequestID>
        <account>
            <acctID> ADDR  </acctID>
            <nonce>  NONCE </nonce>
            ...
        </account>
```

###############################################################################
## eth_getStorageAt

```k
    rule <k> RPCRequest( REQ_ID, EthGetStorageAt( ADDR, SLOT, _BLOCK_NUM ) ) // TODO: block number
        => RPCResponse( intToHex( {STORAGE[ SLOT ] orDefault 0}:>Int ) )
        ...
        </k>
        <rpcRequestID> _ => REQ_ID </rpcRequestID>
        <account>
            <acctID>  ADDR    </acctID>
            <storage> STORAGE </storage>
            ...
        </account>
```

###############################################################################
## anvil_dumpState

```k
    rule <k> RPCRequest( REQ_ID, AnvilDumpState() )
        => RPCResponse(
                #let CONTENTS:IOString = #readFile( #snapshotFile( BLOCK_NUMBER -Int 1 ) )
                #in String2JSON( {CONTENTS}:>String )
           )
        ...
        </k>
        <rpcRequestID> _ => REQ_ID </rpcRequestID>
        <number> BLOCK_NUMBER </number>

```

###############################################################################
## debug_traceTransaction

At the point the debug_traceTransaction method is called, the transaction has already been
processed and its trace stored on disk. We just need to read the trace and return it.
Since the trace can be large, we avoid loading it into memory as a JSON object, and 
just build the response string directly.

```k

    rule <k> RPCRequest( REQ_ID, DebugTraceTransaction( TX_HASH ) )
        => RPCRawResponse(
            "{ \"jsonrpc\": \"2.0\"" +String
            ", \"id\": " +String intToHex( REQ_ID ) +String
            ", \"result\": " +String
                "{ \"failed\":" +String #if TX_STATUS ==Int 1 #then "true" #else "false" #fi +String
                ", \"gas\":" +String Int2String( TX_CUMULATIVE_GAS ) +String
                ", \"return_value\": \"0x\"" +String // TODO
                ", \"structLogs\": [" +String {#readFile( #traceFile( TXID) )}:>String +String
            "] } }"
        ) ...
        </k>
        <rpcRequestID> _ => REQ_ID </rpcRequestID>
        <txReceipt>
            <txHash> TX_HASH </txHash>
            <txID>   TXID    </txID>
            <txCumulativeGas> TX_CUMULATIVE_GAS </txCumulativeGas>
            <txStatus> TX_STATUS </txStatus>
            ...
        </txReceipt>

```


###############################################################################
# Transaction Signing

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
          => #signTx(TXID, ECDSASign( #hashTxData( #getTxData(TXID)), KEY) )
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

###############################################################################
# Transaction Receipts

```k
    syntax KItem ::= "#makeTxReceipts"
                   | "#makeTxReceiptsAux" List
                   | "#makeTxReceipt" Int

    rule <k> #makeTxReceipts => #makeTxReceiptsAux TXLIST ... </k>
         <txOrder> TXLIST </txOrder>
    rule <k> #makeTxReceiptsAux .List => .K ... </k>
    rule <k> #makeTxReceiptsAux (ListItem(TXID) TXLIST) => #makeTxReceipt TXID ~> #makeTxReceiptsAux TXLIST ... </k>

    rule <k> #makeTxReceipt TXID => .K ... </k>
         <txReceipts>
           ( .Bag =>
            <txReceipt>
                <txHash>          txHash( TXID )                 </txHash>
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


    syntax Bytes ::= txHash( Int ) [function]

    rule [[ txHash( TX_ID ) => Keccak256raw( #rlpEncode( [TN, TP, TG, #addrBytes(TT), TV, TD, TW, TR, TS] ) ) ]]
        <message>
            <msgID> TX_ID </msgID>
            <txNonce>    TN </txNonce>
            <txGasPrice> TP </txGasPrice>
            <txGasLimit> TG </txGasLimit>
            <to>         TT </to>
            <value>      TV </value>
            <data>       TD </data>
            <sigV>       TW </sigV>
            <sigR>       TR </sigR>
            <sigS>       TS </sigS>
            ...
        </message>
```


###############################################################################
# Block Mining


The productions below are used to perform the mining of blocks, advancing the blockchain state.

```k
    syntax KItem ::= "#mineBlock"  [symbol(mineBlock)]
                   | #setBlockData( BlockData )

    syntax BlockData ::= #getBlockData( Int )        [function]
                       | #getBlockDataByHash( Int )  [function]
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
          <blockStorage> M => M[ BN                                    <- #getBlockData( BN )] </blockStorage>
          <blockHashes>  H => H[ #hashBlockData( #getBlockData( BN ) ) <- BN                 ] </blockHashes>

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

    rule [[ #getBlockDataByHash( BLOCK_HASH ) => {#getBlockData({BLOCK_STORAGE[ BLOCK_HASH ]}:>Int)}:>BlockData ]]
        <blockStorage> BLOCK_STORAGE:Map </blockStorage>
        <blockHashes>  BLOCK_HASHES:Map </blockHashes>
        requires BLOCK_HASH in_keys(BLOCK_HASHES) andBool BLOCK_HASHES[ BLOCK_HASH ] in_keys(BLOCK_STORAGE)

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

###############################################################################
## State Root
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

###############################################################################
## Transactions Root


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

###############################################################################
## Receipts Root

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
```

###############################################################################
# JSON RPC Intermediate Representation

This section defines an intermediate represention for JSON RPC requests.

```k
      syntax KItem ::= RPCResponse | RPCRequest

      syntax RPCResponse ::= RPCResponse( JSON )
                           | RPCRawResponse( String )
      syntax RPCRequest  ::= RPCRequest( Int, RPCRequestParams)

      syntax RPCRequestParams ::= EthChainId()
                                | EthSendTransaction(
                                    Account , // from
                                    Account , // to
                                    Int , // gas
                                    Int , // gas price
                                    Int , // value
                                    Bytes // input
                                  )
                                | EthGetTransactionReceipt( Bytes )  // tx hash
                                | EthGetTransactionByHash( Bytes )   // tx hash
                                | EthGetCode( Int, Int )             // address, block number
                                | EthGetBalance( Int, Int )          // address, block number
                                | EthGetBlockByNumber( Int, Bool )   // block number, hydrated txs
                                | EthGetBlockByHash( Int, Bool )     // block hash
                                | EthGetTransactionCount( Int, Int ) // address, block number
                                | EthGetStorageAt( Int, Int, Int )   // address, slot, block number
                                | AnvilDumpState()                   // TODO: add options
                                | DebugTraceTransaction( Bytes )     // tx hash
```

###############################################################################
## Convert JSON RPC representation to intermedaite representation

This section defines rules to convert from the JSON representation to the
intermediate representation.

```k
    syntax KItem ::= #rpcLoad( JSON )

    syntax RPCRequest       ::= #rpcLoadRequest( JSON )         [function]
    syntax RPCRequestParams ::= #rpcLoadParams( String, JSON )  [function]

    // RPC requests can be batched, in this case we iterate over the list
    rule <k> #rpcLoad( [ .JSONs ] ) => .K ... </k>
    rule <k> #rpcLoad( [ FIRST, REST ] )
        => #rpcLoadRequest( FIRST )
        ~> #rpcLoad( [ REST ] ) ... </k>
    // If the request is not batched, we just load a single request
    rule <k> #rpcLoad( { FIRST } ) 
        => #rpcLoadRequest( { FIRST } ) ... </k>
    // If the request is malformed, we ignore it
    // TODO: add error handling
    rule <k> #rpcLoad( _ ) => .K ... </k> [owise]

    rule #rpcLoadRequest( J )
            => #let REQ_ID  = #getInt(    "id",     J) #in
            #let METHOD     = #getString( "method", J) #in
            #let PARAMS_RAW = #getJSON(   "params", J) #in
            #let REQ_PARAMS = #rpcLoadParams( METHOD, PARAMS_RAW ) #in
            RPCRequest(REQ_ID, REQ_PARAMS)

    rule #rpcLoadParams( "eth_chainId", [ .JSONs ] )
        => EthChainId()

    rule #rpcLoadParams( "eth_sendTransaction", [ J ])
        => #let FROM       = #getAccount( "from", J, DEFAULTSENDER ) #in
            #let TO        = #getAccount( "to"  , J, .Account ) #in
            #let GAS_LIMIT = #getWord( "gas" , J, pow24 ) #in
            #let GAS_PRICE = #getWord( "gas_price", J, 1 ) #in
            #let VALUE     = #getWord( "value", J, 0 ) #in
            #let DATA      = #getBytes( "data", J, .Bytes ) #in
            EthSendTransaction( FROM, TO, GAS_LIMIT, GAS_PRICE, VALUE, DATA )

    rule #rpcLoadParams( "eth_getTransactionReceipt", [ TX_HASH:String ] )
        => EthGetTransactionReceipt( #parseByteStack( TX_HASH ) )

    rule #rpcLoadParams( "eth_getTransactionByHash", [ TX_HASH:String ] )
        => EthGetTransactionByHash( #parseByteStack( TX_HASH ) )

    rule #rpcLoadParams( "eth_getCode", [ ADDR:String, BLOCK_NUM:String ] )
        => #let ADDR_INT = #parseAddr( ADDR ) #in
            #let BLOCK_INT = #parseBlockNumber( BLOCK_NUM ) #in
            EthGetCode( ADDR_INT, BLOCK_INT )

    rule #rpcLoadParams( "eth_getBalance", [ ADDR:String, BLOCK_NUM:String ] )
        => #let ADDR_INT = #parseAddr( ADDR ) #in
           #let BLOCK_INT = #parseBlockNumber( BLOCK_NUM ) #in 
            EthGetBalance( ADDR_INT, 0 )

    rule #rpcLoadParams( "eth_getBlockByNumber", [ BLOCK_NUM:String, HYDRATED_TXS:Bool ] )
        => #let BLOCK_INT = #parseBlockNumber( BLOCK_NUM ) #in
            EthGetBlockByNumber( BLOCK_INT, HYDRATED_TXS )

    rule #rpcLoadParams( "eth_getBlockByHash", [ BLOCK_HASH:String, HYDRATED_TXS:Bool ] )
        => EthGetBlockByHash( #parseWord( BLOCK_HASH ), HYDRATED_TXS )

    rule #rpcLoadParams( "eth_getTransactionCount", [ ADDR:String, BLOCK_NUM:String ] )
        => #let ADDR_INT = #parseAddr( ADDR ) #in
           #let BLOCK_INT = #parseBlockNumber( BLOCK_NUM ) #in
            EthGetTransactionCount( ADDR_INT, BLOCK_INT )

    rule #rpcLoadParams( "eth_getStorageAt", [ ADDR:String, SLOT:String, BLOCK_NUM:String ] )
        => #let ADDR_INT = #parseAddr( ADDR ) #in
            #let SLOT_INT = #parseWord( SLOT ) #in
            #let BLOCK_INT = #parseBlockNumber( BLOCK_NUM ) #in
            EthGetStorageAt( ADDR_INT, SLOT_INT, BLOCK_INT )

    rule #rpcLoadParams( "anvil_dumpState", [ _ ] )
        => AnvilDumpState()

    rule #rpcLoadParams( "debug_traceTransaction", [ TX_HASH:String, _OPTIONS:JSON ] )
        => DebugTraceTransaction( #parseByteStack( TX_HASH ) )

    // Helpers
    syntax Int ::= "DEFAULTSENDER" [function]
    rule DEFAULTSENDER => #parseAddr("0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266")

    syntax Int ::= #parseBlockNumber( String ) [function]
    rule [[ #parseBlockNumber( "latest" ) => CURRENT_BLOCK_NUMBER -Int 1 ]]
        <number> CURRENT_BLOCK_NUMBER </number>
    rule #parseBlockNumber( BN ) => #parseWord( BN ) [owise]

    syntax Account ::= #getAccount(JSONKey, JSON, Account) [function]
    rule #getAccount( KEY, J, DEF_VAL ) => #let RAW = #getJSON( KEY, J ) #in
                                        #if RAW ==K null #then DEF_VAL #else #parseAddr( {RAW}:>String ) #fi
```
###############################################################################
# State Snapshots

## JSON encoding of Snapshots

This section defines rule to create a StateDump JSON object from the current
K configuration.

```k

    syntax KItem ::= "#createStateDump"         // Internal use only, create a StateDump from the current configuration
                   | #StateDump( JSON )         // Internal use only, wrap a StateDump JSON object to disambiguate it from other KItems containing JSON data

    syntax JSON  ::= ( JSON )  [bracket]
    syntax JSONs ::= ( JSONs ) [bracket]
    syntax JSON  ::= accountsToJSON( AccountsCell )          [function, total, symbol(accountsToJSON)]
                   | accountToJSON( AccountCell )            [function, total, symbol(accountToJSON)]
                   | storageToJSON(Map)                      [function, total, symbol(accStorageToJson)]
                   | blocksToJSON(Map)                       [function, total, symbol(blocksToJSON)]
                   | blockToJSON(BlockData)                  [function, total, symbol(blockToJSON)]

    syntax JSONs ::= accountsToJSONs( AccountsCell, JSONs )  [function, total, symbol(accountsToJSONs)]
                   | storageToJSONs( Map, JSONs )            [function, total, symbol(accStorageToJSONs)]
                   | blocksToJSONs( Map, JSONs )             [function, total, symbol(blocksToJSONs)]


    // Duplicated in trace-json.md where this is called intMapToJson
    rule storageToJSON( ST ) => { storageToJSONs( ST, .JSONs ) }
    rule storageToJSONs( .Map, ACCU ) => ACCU
    rule storageToJSONs( (KEY |-> VAL) ST, ACCU) => storageToJSONs( ST, ( intToHex(KEY) : intToHex(VAL), ACCU ) )

    rule accountToJSON (
        <account>
            <acctID>            ACC_ID            </acctID>
            <balance>           ACC_BALANCE       </balance>
            <code>              ACC_CODE          </code>
            <storage>           ACC_STORAGE       </storage>
            <nonce>             ACC_NONCE         </nonce>
            ...
        </account>
    ) => intToHex(ACC_ID) : {
        "balance": intToHex( ACC_BALANCE ),
        "code": bytesToHex( ACC_CODE ),
        "storage": storageToJSON( ACC_STORAGE ),
        "nonce" : ACC_NONCE
    }

    rule accountsToJSON( ACCS ) => { accountsToJSONs( ACCS, .JSONs ) }
    rule accountsToJSONs( <accounts> <account> ACC </account> ACCS:Bag </accounts>, ACCU)
            => accountsToJSONs( <accounts> ACCS </accounts>, (accountToJSON( <account> ACC </account> ) , ACCU) ) 
    rule accountsToJSONs( <accounts> .Bag </accounts>, ACCU ) => ACCU [owise]

    rule <k> #createStateDump
        => #StateDump({
            "bestBlockNumber": BLOCK_NUMBER -Int 1,
            "block": {
                "number": intToHex( BLOCK_NUMBER -Int 1 ),
                "beneficiary": intToHex( BLOCK_COINBASE ),
                "timestamp": intToHex( BLOCK_TIMESTAMP ),
                "gas_limit": BLOCK_GAS_LIMIT,
                "basefee": BLOCK_BASE_FEE,
                "difficulty": intToHex( BLOCK_DIFFICULTY ),
                "prevrandao": "0x0000000000000000000000000000000000000000000000000000000000000000",
                "blob_excess_gas_and_price": {
                    "excess_blob_gas": BLOCK_EXCESS_BLOB_GAS,
                    "blob_gasprice": 1
                }
            },
            "accounts": accountsToJSON( <accounts> ACCOUNTS </accounts> ),
            "blocks": blocksToJSON( BLOCK_STORAGE )
        }) ...
    </k>
    <block>
        <number>        BLOCK_NUMBER          </number>
        <coinbase>      BLOCK_COINBASE        </coinbase>
        <timestamp>     BLOCK_TIMESTAMP       </timestamp>
        <gasLimit>      BLOCK_GAS_LIMIT       </gasLimit>
        <baseFee>       BLOCK_BASE_FEE        </baseFee>
        <difficulty>    BLOCK_DIFFICULTY      </difficulty>
        <excessBlobGas> BLOCK_EXCESS_BLOB_GAS </excessBlobGas>
        ...
    </block>
    <accounts> ACCOUNTS </accounts>
    <blockStorage> BLOCK_STORAGE </blockStorage>

    rule blocksToJSON( BS ) => [ blocksToJSONs( BS, .JSONs ) ] [priority(50)]
    rule blocksToJSONs( .Map, ACCU ) => ACCU
    rule blocksToJSONs( (_ |-> VAL) BS, ACCU) => blockToJSON({VAL}:>BlockData), blocksToJSONs( BS, ACCU )

    rule blockToJSON( BlockData(
            PH, HO, HC, HR, HT, HE, HB, HD, BN, HL, HG, HS, HX, HM, HN, BF, WR, BG, EG, BR, RR, OBH
         ))
        => { "header": {
                "parentHash":       intToHex( PH ),
                "sha3Uncles":       intToHex( HO ),
                "miner":            intToHex( HC ),
                "stateRoot":        intToHex( HR ),
                "transactionsRoot": intToHex( HT ),
                "receiptsRoot":     intToHex( HE ),
                "logsBloom":        bytesToHex( HB ),
                "difficulty":       intToHex( HD ),
                "number":           intToHex( BN ),
                "gasLimit":         intToHex( HL ),
                "gasUsed":          #if isInt(HG) #then intToHex( HG ) #else "0x0" #fi,
                "timestamp":        intToHex( HS ),
                "extraData":        bytesToHex( HX ),
                "mixHash":          intToHex( HM ),
                "nonce":            intToHex( HN ),
                "baseFeePerGas":    intToHex( BF ),
                "withdrawalsRoot":  intToHex( WR ),
                "blobGasUsed":      intToHex( BG ),
                "excessBlobGas":    intToHex( EG ),
                "parentBeaconBlockRoot": intToHex( BR ),
                "requestsHash":     intToHex( RR )
            },
            "transactions": [ .JSONs ],
            "ommers": OBH
        }
```

###############################################################################
## JSON decoding of snapshots

This secion defines rules to load a StateDump JSON object into the current
K configuration.

It's very similar to the [state-utils.md](https://github.com/runtimeverification/evm-semantics/blob/master/kevm-pyk/src/kevm_pyk/kproj/evm-semantics/state-utils.md)
module defined in `evm-semantics`, but targets specifically the Anvil's
StateDump format - not the ethereum/test format.

```k

    syntax KItem ::= #loadSnapshot( Snapshot )
                   | #loadBlocks( Blocks )
                   | #loadBlock( BlockData )
                   | #loadCurrentBlock( Int )
                   | #loadAccounts( Accounts )
                   | #loadAccount( AccountData )

    rule <k> #loadSnapshot( Snapshot(LATEST_BLOCK_NUMBER, ACCOUNTS, BLOCKS) )
          => #loadAccounts( ACCOUNTS )
          ~> #loadBlocks( BLOCKS )
          ~> #loadCurrentBlock( LATEST_BLOCK_NUMBER ) ... </k>
          <accounts>     _ => .Bag </accounts>
          <blockStorage> _ => .Map </blockStorage>
          <blockHashes>  _ => .Map </blockHashes>

    rule <k> #loadBlocks( .Blocks ) => .K ... </k>
    rule <k> #loadBlocks( BLOCK_DATA , REST )
          => #loadBlock( BLOCK_DATA )
          ~> #loadBlocks( REST ) ... </k>

    rule <k> #loadBlock( BLOCK_DATA ) => .K ... </k>
        <blockStorage> BLOCK_STORAGE =>
                       BLOCK_STORAGE[ #getBlockNumber( BLOCK_DATA ) <- BLOCK_DATA ]
        </blockStorage>
        <blockHashes>  BLOCK_HASHES  =>
                       BLOCK_HASHES[ #hashBlockData( BLOCK_DATA ) <- #getBlockNumber( BLOCK_DATA ) ]
        </blockHashes>

    rule <k> #loadCurrentBlock( BLOCK_NUMBER ) => .K ... </k>
        <blockStorage> BLOCK_STORAGE </blockStorage>
        <block>
            <number> _ => BLOCK_NUMBER +Int 1 </number>
            <previousHash> _ => #hashBlockData( {BLOCK_STORAGE[ BLOCK_NUMBER ]}:>BlockData  ) </previousHash>
            ...
        </block>

    rule <k> #loadAccounts( .Accounts ) => .K ... </k>

    rule <k> #loadAccounts( ACCOUNT_DATA , REST )
          => #loadAccount( ACCOUNT_DATA )
          ~> #loadAccounts( REST ) ... </k>

    rule <k> #loadAccount( AccountData(
            ACCT_ID,
            ACCT_BALANCE,
            ACCT_STORAGE,
            ACCT_CODE,
            ACCT_NONCE
         ))
        => .K ... </k>
        <accounts>
            ( .Bag => <account>
                    <acctID>  ACCT_ID      </acctID>
                    <balance> ACCT_BALANCE </balance>
                    <storage> ACCT_STORAGE </storage>
                    <code>    ACCT_CODE    </code>
                    <nonce>   ACCT_NONCE   </nonce>
                    ...
                </account>
            )
            ...
        </accounts>

    // Intermediate representations

    syntax Snapshot ::= Snapshot(
            Int,
            Accounts,
            Blocks
        )
        | #parseSnapshot( JSON ) [function]

    syntax AccountData ::= AccountData(
            Int,   // acctID
            Int,   // balance
            Map,   // storage
            Bytes, // code
            Int    // nonce
        )
        | #parseAccount( JSON ) [function]

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
            JSON // ommersBlockHeaders
        ) | #parseBlock( JSON ) [function]

    syntax Map ::= #parseStorage( JSON )         [function]
                 | #parseStorageAux( JSON, Map ) [function]

    syntax Accounts ::= List{AccountData, ","}
                      | "[" Accounts "]" [bracket]
                      | #parseAccounts( JSON ) [function]
    syntax Blocks   ::= List{BlockData, ","}
                      | "[" Blocks "]" [bracket]
                      | #parseBlocks( JSON ) [function]

    syntax Int ::= #getBlockNumber( BlockData ) [function]
    rule #getBlockNumber( BlockData( _, _, _, _, _, _, _, _, BN, _, _, _, _, _, _, _, _, _, _, _, _, _) ) => BN

    rule #parseSnapshot( SNAPSHOT_JSON )
        => #let BEST_BLOCK_NUMBER = #getInt( "best_block_number", SNAPSHOT_JSON, 0 ) #in
           #let ACCOUNTS_JSON     = #getJSON( "accounts", SNAPSHOT_JSON ) #in
           #let BLOCKS_JSON       = #getJSON( "blocks",   SNAPSHOT_JSON ) #in
           Snapshot(
               BEST_BLOCK_NUMBER,
               #parseAccounts( ACCOUNTS_JSON ),
               #parseBlocks( BLOCKS_JSON )
           )

    rule #parseBlocks( [ .JSONs ] ) => .Blocks
    rule #parseBlocks( [ FIRST, REST ] ) => #parseBlock( FIRST ) , #parseBlocks( [ REST ] )

    rule #parseBlock( BLOCK_JSON ) =>
        #let BLOCK_HEADER = #getJSON( "header", BLOCK_JSON ) #in
        BlockData(
            #getWord( "parentHash",       BLOCK_HEADER, 0 ),
            #getWord( "sha3Uncles",       BLOCK_HEADER, 0 ),
            #getWord( "miner",            BLOCK_HEADER, 0 ),
            #getWord( "stateRoot",        BLOCK_HEADER, 0 ),
            #getWord( "transactionsRoot", BLOCK_HEADER, 0 ),
            #getWord( "receiptsRoot",     BLOCK_HEADER, 0 ),
            #getBytes( "logsBloom",       BLOCK_HEADER, .Bytes ),
            #getWord( "difficulty",       BLOCK_HEADER, 0 ),
            #getWord( "number",           BLOCK_HEADER, 0 ),
            #getWord( "gasLimit",         BLOCK_HEADER, pow24 ),
            #getWord( "gasUsed",          BLOCK_HEADER, 0 ),
            #getWord( "timestamp",        BLOCK_HEADER, 0 ),
            #getBytes( "extraData",       BLOCK_HEADER, .Bytes ),
            #getWord( "mixHash",          BLOCK_HEADER, 0 ),
            #getWord( "nonce",            BLOCK_HEADER, 0 ),
            #getWord( "baseFeePerGas",    BLOCK_HEADER, 0 ),
            #getWord( "withdrawalsRoot",  BLOCK_HEADER, 0 ),
            #getWord( "blobGasUsed",      BLOCK_HEADER, 0 ),
            #getWord( "excessBlobGas",    BLOCK_HEADER, 0 ),
            #getWord( "parentBeaconBlockRoot", BLOCK_HEADER, 0 ),
            #getWord( "requestsHash",     BLOCK_HEADER, 0 ),
            #getJSON( "ommers",           BLOCK_JSON, [ .JSONs ] )
        )

    rule #parseAccounts( { .JSONs } ) => .Accounts
    rule #parseAccounts( { FIRST, REST } ) => #parseAccount( FIRST ) , #parseAccounts( { REST } )

    rule #parseAccount( ACCT_ID_RAW : ACCT_DATA )
        => #let ACCT_ID       = #parseAddr( ACCT_ID_RAW ) #in
           #let ACCT_BALANCE  = #getWord( "balance", ACCT_DATA, 0 ) #in
           #let ACCT_CODE     = #getBytes( "code",   ACCT_DATA, .Bytes ) #in
           #let ACCT_STORAGE  = #parseStorage( #getJSON( "storage", ACCT_DATA ) ) #in
           #let ACCT_NONCE    = #getInt( "nonce",   ACCT_DATA, 0 ) #in
           AccountData(
               ACCT_ID,
               ACCT_BALANCE,
               ACCT_STORAGE,
               ACCT_CODE,
               ACCT_NONCE
           )

    rule #parseStorage( ST_JSON ) => #parseStorageAux( ST_JSON, .Map )

    rule #parseStorageAux( { .JSONs }, ACCU ) => ACCU
    rule #parseStorageAux( { KEY : VAL, REST }, ACCU ) => 
         #parseStorageAux( { REST }, ACCU[ #parseWord( KEY ) <- #parseWord( VAL ) ] )

```
###############################################################################
# Input/Output

## Sending RPC Responses

This section defines rules to write RPCResponses to a file.

```k

      syntax String ::= "#responseFile" [function, total]
      rule [[ #responseFile => IO_DIR +String "/response.json" ]]
        <ioDir> IO_DIR </ioDir>

      rule <k> RPCResponse( JSON_RESPONSE )
            => #writeFile(#responseFile, JSON2String({
                  "jsonrpc" : "2.0",
                  "id"      : REQ_ID,
                  "result"  : JSON_RESPONSE
            }))
            ... </k>
            <rpcRequestID> REQ_ID </rpcRequestID>
            
      rule <k> RPCRawResponse( RESPONSE:String )
            => #writeFile(#responseFile, RESPONSE)
            ...
           </k>

```

## Loading RPCRequests

This section defines rules to read a RPCRequests from a file.

```k
    syntax KItem ::= "#loadRpcRequest"
    
    syntax String ::= "#requestFile" [function, total]
    rule [[ #requestFile => IO_DIR +String "/request.json" ]]
        <ioDir> IO_DIR </ioDir>

    rule <k> #loadRpcRequest
        => #let CONTENTS:IOString = #readFile( #requestFile )
            #in #rpcLoad( String2JSON( {CONTENTS}:>String ) )
        ...
        </k>

```
## Persisting a StateDump to Disk

This seciont defines rules to write a StateDump JSON object to disk.

```k

    syntax KItem ::= "#writeStateDump"
                   | "#saveStateDump"

    syntax String ::= #snapshotFile( Int ) [function, total]

    rule [[ #snapshotFile( BLOCK_NUMBER )
            => IO_DIR +String "/blocks/block_" +String Int2String( BLOCK_NUMBER ) +String ".json"
        ]]
        <ioDir> IO_DIR </ioDir>

    rule <k> #saveStateDump
          => #createStateDump
          ~> #writeStateDump
          ...
        </k>

    rule <k> #StateDump( SD )
          ~> #writeStateDump
          => #writeFile( #snapshotFile( BLOCK_NUMBER -Int 1), JSON2String( SD ) )
          ...
        </k>
        <number> BLOCK_NUMBER </number>

```
## Loading StateDump from Disk

This secion defines rules to read a StateDump JSON object from disk.

```k

    syntax KItem ::= #loadSnapshotFile( Int )

    rule <k> #loadSnapshotFile( BLOCK_NUMBER )
          => #let CONTENTS:IOString = #readFile( #snapshotFile( BLOCK_NUMBER ) )
              #in #loadSnapshot( #parseSnapshot( String2JSON( {CONTENTS}:>String ) ) )
              ...
         </k>

    syntax KItem ::= "#loadLatestSnapshot"

    rule <k> #loadLatestSnapshot
          => #loadSnapshotFile( #getInt( "latest_block_number", #loadMetadata, 0 ) )
          ...
         </k>

    syntax String ::= "#metadataFile" [function, total]
    
    rule [[ #metadataFile=> IO_DIR +String "/metadata.json" ]]
        <ioDir> IO_DIR </ioDir>

    syntax KItem ::= "#saveMetadata"
    syntax JSON ::= "#loadMetadata" [function]

    rule #loadMetadata =>
            #let CONTENTS:IOString = #readFile( #metadataFile ) #in
            String2JSON( {CONTENTS}:>String )

    rule <k> #saveMetadata
          => #writeFile(
                #metadataFile,
                JSON2String( { "latest_block_number": maxInt(0, CURRENT_BLOCK_NUMBER -Int 1) } )
            )
          ... </k>
        <number> CURRENT_BLOCK_NUMBER </number>


endmodule
```