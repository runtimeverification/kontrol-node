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
    // ----------------------------------------------

    rule <k> #start( IO_DIR )
        => #unlockAccounts()
        ~> #loadLatestSnapshot
        ~> #loadRpcRequest
        ...
    </k>
    <ioDir> _ => IO_DIR </ioDir>
    <block>
        <gasLimit> _ => 30000000 </gasLimit>
        ...
    </block>

```

Unlocked test accounts. These are the same ten accounts used by most dev tools.
Mnemonic: test test test test test test test test test test test junk

```k

    syntax KItem ::= #unlockAccounts()
    // -------------------------------

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

    syntax Int ::= "DEFAULTSENDER" [function, symbol(DEFAULTSENDER)]
    // -------------------------------------------------------------
    rule DEFAULTSENDER => #parseAddr("0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266")

    syntax Int ::= "#getLatestBlockNumber" [function, symbol(getLatestBlockNumber)]
    // ----------------------------------------------------------------------------

    rule [[ #getLatestBlockNumber => BLOCK_NUMBER -Int 1 ]]
        <number> BLOCK_NUMBER </number>
        requires 0 <Int BLOCK_NUMBER
    rule #getLatestBlockNumber => 0 [owise]

    syntax Int ::= "#getLatestTxID" [function, symbol(getLatestTxID)]
    // --------------------------------------------------------------

    rule #getLatestTxID => #getLatestBlockNumber // We're auto mining one block per tx

    syntax Int ::= "#getNextTxID" [function, symbol(getNextTxID)]
    // ----------------------------------------------------------

    rule #getNextTxID => #getLatestTxID +Int 1

    syntax Int   ::= #txHash( Int )      [function, symbol(txHash)]
    syntax Bytes ::= #txHashBytes( Int ) [function, symbol(txHashBytes)]
    // -----------------------------------------------------------------

    rule [[ #txHashBytes( TX_ID ) => Keccak256raw( #rlpEncode( [TN, TP, TG, #addrBytes(TT), TV, TD, TW, TR, TS] ) ) ]]
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

    rule #txHash( TX_ID ) => Bytes2Int( #txHashBytes( TX_ID ), BE, Unsigned )

    syntax Account ::= #sender( msgId: Int ) [function, symbol(sender)]
    // ----------------------------------------------------------------

    rule [[ #sender( MSG_ID ) => #sender( #getTxData( MSG_ID ), MSG_SIGV, MSG_SIGR, MSG_SIGS, CHAIN_ID ) ]]
        <chainID> CHAIN_ID </chainID>
        <message>
            <msgID> MSG_ID </msgID>
            <sigV>  MSG_SIGV </sigV>
            <sigR>  MSG_SIGR </sigR>
            <sigS>  MSG_SIGS </sigS>
            ...
        </message>

```
###############################################################################
# Requests

## eth_chainId

```k
    rule <k> RPCRequest( REQ_ID, EthChainId() )  => RPCResponse( CHAIN_ID ) ... </k>
         <rpcRequestID> _ => REQ_ID </rpcRequestID>
         <chainID> CHAIN_ID </chainID>
```

###############################################################################
## eth_sendTransaction

When eth_sendTransaction is called, we sign it, apply the intrinsic gas costs,
execute it, mine a block including it, and return the transaction hash.
Additionally, we eagerly compute the transaction trace and and save it to disk.
Similarly, we save a state snapshot after the block was mined.

```k
    syntax KItem ::= #ethSendTransactionResponse( Int ) [symbol(ethSendTransactionResponse)]
                   | "#resetCallState"                  [symbol(resetCallState)]
    // ---------------------------------------------------------------------------

    rule <k> #resetCallState => .K ... </k>
         <statusCode>                   _ => .StatusCode </statusCode>
         <origin>                       _ => .Account    </origin>
         <recordedTrace>                _ => false       </recordedTrace>
         <injectedTracesCallStack>      _ => false       </injectedTracesCallStack>
         <recordedMkCallCreate>         _ => false       </recordedMkCallCreate>
         <contextSwitch>                _ => true        </contextSwitch>
         <currentNonceMutations>        _ => .Map        </currentNonceMutations>
         <currentBalanceMutations>      _ => .Map        </currentBalanceMutations>
         <currentStorageMutations>      _ => .Map        </currentStorageMutations>
         <localMemoryChanged>           _ => true        </localMemoryChanged>
         <programChanged>               _ => true        </programChanged>
         <tracesCallStack>              _ => .List       </tracesCallStack>
         <isInitCode>                   _ => false       </isInitCode>
         <currentDeployedCodeMutations> _ => .Map        </currentDeployedCodeMutations>
         <currentInitCodeMutations>     _ => .Map        </currentInitCodeMutations>
         <stepCount>                    _ => 0           </stepCount>
         <callState>
            <program>    _ => .Bytes     </program>
            <jumpDests>  _ => .Bytes     </jumpDests>
            <id>         _ => .Account   </id>
            <caller>     _ => .Account   </caller>
            <callData>   _ => .Bytes     </callData>
            <callValue>  _ => 0          </callValue>
            <wordStack>  _ => .WordStack </wordStack>
            <localMem>   _ => .Bytes     </localMem>
            <pc>         _ => 0          </pc>
            <gas>        _ => 0:Gas      </gas>
            <memoryUsed> _ => 0          </memoryUsed> 
            <callGas>    _ => 0:Gas      </callGas>
            <static>     _ => false      </static>
            <callDepth>  _ => 0          </callDepth>
            <codeAddr>   _ => .Account   </codeAddr>
         </callState>
         

    rule <k> RPCRequest( REQ_ID, EthSendTransaction( FROM, TO, GAS_LIMIT, GAS_PRICE, VALUE, DATA ) )
            => #loadAccount( FROM )
            ~> #signTx
            ...
        </k>
        <rpcRequestID> _ => REQ_ID </rpcRequestID>
        <origin>       _ => FROM   </origin>
        <schedule>     SCHED       </schedule>
        <callState>
            <callGas> _ => G0(SCHED, DATA, (TO ==K .Account) ) </callGas>
            <caller>  _ => FROM </caller>
            ...
        </callState>
        <network>
            <chainID>  CHAIN_ID </chainID>
            <account>
                <acctID> FROM     </acctID>
                <nonce>  TXNONCE  </nonce>
                ...
            </account>
            <txOrder>   ... (.List => ListItem(#getNextTxID )) </txOrder>
            <txPending> ... (.List => ListItem(#getNextTxID )) </txPending>
            <messages>
                ( .Bag => 
                    <message>
                        <msgID>      #getNextTxID    </msgID>
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
        => #resetCallState
        ~> RPCErrorResponse(-32603, "Could not sign transaction: account not found")
        ...
        </k>

    rule <k> #signTxSuccess
        => #applyIntrinsicGas
        ...
        </k>

    rule <k> #intrinsicGasError( _ERR_CODE )
        => #resetCallState
        ~> RPCErrorResponse(-32603, "Intrinsic gas error")
        ...
        </k>

    rule <k> #intrinsicGasSuccess
        => #executeTx
        ~> #finishTx
        ~> #finalizeTx(false, Ctxfloor(SCHED, DATA))
        ~> #makeTxReceipt( TX_ID )
        ~> #finalizeBlock
        ~> #mineBlock
        ~> #saveStateDump
        ~> #saveMetadata
        ~> #resetCallState
        ~> #ethSendTransactionResponse( TX_ID )
        ...
        </k>
        <txPending> ListItem( TX_ID ) ... </txPending>
        <schedule>    SCHED  </schedule>
        <message>
            <msgID> TX_ID </msgID>
            <data>  DATA  </data>
            ...
        </message>

    rule <k> #ethSendTransactionResponse( TXID )
        => RPCResponse( uint256ToHex( TX_HASH ) )
        ... </k>
        <txReceipt>
            <txMsg>   TXID    </txMsg>
            <txHash>  TX_HASH </txHash>
            ...
        </txReceipt>
```
###############################################################################
## eth_getTransactionReceipt

```k
    rule <k> RPCRequest( REQ_ID, EthGetTransactionReceipt( _TX_HASH ) )
          => RPCResponse( null ) ...
         </k>
         <rpcRequestID> _ => REQ_ID </rpcRequestID>
        [owise]

    rule <k> RPCRequest( REQ_ID, EthGetTransactionReceipt( TX_HASH ) )
        => RPCResponse({
                "type"              : "0x0",
                "transactionHash"   : uint256ToHex( TX_HASH ),
                "transactionIndex"  : "0x0", // kontrol-node always includes exactly one tx per block
                "blockHash"         : uint256ToHex( #hashBlockNumber( BLOCK_NUMBER ) ),
                "blockNumber"       : intToHex( BLOCK_NUMBER ),
                "from"              : accountToHex( #sender( TXID ) ),
                "to"                : accountToHex( TO ),
                "cumulativeGasUsed" : intToHex( CGAS ), // There is only one tx per block, so cumulative gas used is the same as gas used
                "gasUsed"           : intToHex( CGAS ), 
                "contractAddress"   : #if TO ==K .Account #then addrToHex( #newAddr({#sender( TXID )}:>Int, TX_NONCE) ) #else null #fi,
                "logs"              : [ .JSONs ], // TODO
                "logsBloom"         : bytesToHex( .Bytes , 256), // TODO: compute actual bloom filter'
                "status"            : intToHex( TX_STATUS ),
                "effectiveGasPrice" : intToHex( GAS_PRICE )
            })
            ...
        </k>
        <rpcRequestID> _ => REQ_ID </rpcRequestID>
        <txReceipt>
            <txMsg>           TXID                           </txMsg>
            <txBlockNumber>   BLOCK_NUMBER                   </txBlockNumber>
            <txHash>          TX_HASH                        </txHash>
            <txCumulativeGas> CGAS                           </txCumulativeGas>
            <txLogs>          _                              </txLogs>
            <txLogsBloom>     _                              </txLogsBloom>
            <txStatus>        TX_STATUS                      </txStatus>
        </txReceipt>
        <message>
            <msgID>        TXID                           </msgID>
            <txNonce>      TX_NONCE                       </txNonce>
            <to>           TO                             </to>
            <txGasPrice>   GAS_PRICE                      </txGasPrice>
            ...
        </message>
```

###############################################################################
## eth_getTransactionByHash

```k
    rule <k> RPCRequest( REQ_ID, EthGetTransactionByHash( _TX_HASH ) )
          => RPCResponse( null ) ...
         </k>
         <rpcRequestID> _ => REQ_ID </rpcRequestID>
        [owise]

    rule <k> RPCRequest( REQ_ID, EthGetTransactionByHash( TX_HASH ) )
        => RPCResponse({
                "type"             : "0x0",
                "nonce"            : intToHex( TX_NONCE ),
                "to"               : accountToHex( TO ),
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
            <txMsg>  TXID    </txMsg>
            <txHash> TX_HASH </txHash>
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

    rule <k> RPCRequest( REQ_ID, EthGetCode( _ADDR, _BLOCK_NUM ) )
          => RPCResponse( "0x" ) ...
         </k>
         <rpcRequestID> _ => REQ_ID </rpcRequestID>
        [owise]

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

    rule <k> RPCRequest( REQ_ID, EthGetBalance( _ADDR, _BLOCK_NUM ) )
        => RPCResponse( intToHex( 0 ) )
        ...
        </k>
        <rpcRequestID> _ => REQ_ID </rpcRequestID> [owise]
```

###############################################################################
## eth_getBlockByNumber

```k
    syntax KItem ::= #ethGetBlockResponse( BlockData ) [symbol(ethGetBlockResponse)]
    // -----------------------------------------------------------------------------

    rule <k> RPCRequest( REQ_ID, EthGetBlockByNumber( BLOCK_NUMBER, _HYDRATED_TXS ) ) // TODO: hydrated txs
          => #ethGetBlockResponse( #getBlockData( BLOCK_NUMBER ) ) ...
         </k>
         <rpcRequestID> _ => REQ_ID </rpcRequestID>
         <blockStorage> BLOCK_STORAGE:Map </blockStorage>
        requires BLOCK_NUMBER in_keys(BLOCK_STORAGE)

    rule <k> RPCRequest( REQ_ID, EthGetBlockByNumber( _BLOCK_NUMBER, _HYDRATED_TXS ) )
           => RPCResponse( null ) ...
         </k>
         <rpcRequestID> _ => REQ_ID </rpcRequestID> [owise]

    rule <k> #ethGetBlockResponse( ( BlockData(
            PH, HO, HC, HR, HT, HE, HB, HD, BN, HL, HG, HS, HX, HM, HN, BF, WR, BG, EG, BR, RR, OBH
         )) )
            => RPCResponse({
                "hash"             : uint256ToHex(#hashBlockData( BlockData(
                    PH, HO, HC, HR, HT, HE, HB, HD, BN, HL, HG, HS, HX, HM, HN, BF, WR, BG, EG, BR, RR, OBH
                ))),
                "parentHash"       : uint256ToHex( PH ),
                "sha3Uncles"       : uint256ToHex( HO ),
                "miner"            : addrToHex( HC ),
                "stateRoot"        : uint256ToHex( HR ),
                "transactionsRoot" : uint256ToHex( HT ),
                "receiptsRoot"     : uint256ToHex( HE ),
                "logsBloom"        : bytesToHex( HB ),
                "difficulty"       : intToHex( HD ),
                "totalDifficulty"  : intToHex( HD ),
                "number"           : intToHex( BN ),
                "gasLimit"         : intToHex( HL ),
                "gasUsed"          : intToHex( HG ),
                "timestamp"        : intToHex( HS ),
                "extraData"        : bytesToHex( HX ),
                "mixHash"          : uint256ToHex( HM ),
                "nonce"            : intToHex( HN ),
                "size"             : "0x0", // TODO: Is this number of txs, bytes of rlp encoding, something else?
                "baseFeePerGas"    : intToHex( BF ),
                "blobGasUsed"      : intToHex( BG ),
                "excessBlobGas"    : intToHex( EG ),
                "transactions"     : [ .JSONs ], // TODO
                "uncles"           : [ .JSONs ]  // TODO
            })
            ... </k>
```

###############################################################################
## eth_getBlockByHash

```k

    rule <k> RPCRequest( REQ_ID, EthGetBlockByHash( BLOCK_HASH, _HYDRATED_TXS ) )
          => #ethGetBlockResponse( #getBlockDataByHash( BLOCK_HASH ) ) ...
         </k>
         <rpcRequestID> _ => REQ_ID </rpcRequestID>
         <blockStorage> BLOCK_STORAGE:Map </blockStorage>
         <blockHashes>  BLOCK_HASHES:Map </blockHashes>
         requires BLOCK_HASH in_keys(BLOCK_HASHES)
          andBool (BLOCK_HASHES[ BLOCK_HASH ] orDefault -1) in_keys(BLOCK_STORAGE)

    rule <k> RPCRequest( REQ_ID, EthGetBlockByHash( _BLOCK_HASH, _HYDRATED_TXS ) )
          => RPCResponse( null ) ...
         </k>
         <rpcRequestID> _ => REQ_ID </rpcRequestID> [owise]
```

###############################################################################
## eth_getTransactionCount

```k
    rule <k> RPCRequest( REQ_ID, EthGetTransactionCount( _ADDR, _BLOCK_NUM ) )
          => RPCResponse( intToHex( 0 ) )
          ...
         </k>
         <rpcRequestID> _ => REQ_ID </rpcRequestID>
        [owise]

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

    rule <k> RPCRequest( REQ_ID, EthGetStorageAt( _ADDR, _SLOT, _BLOCK_NUM ) )
          => RPCResponse( intToHex( 0 ) ) ...
         </k>
         <rpcRequestID> _ => REQ_ID </rpcRequestID>
        [owise]

```

###############################################################################
## anvil_dumpState

```k

    rule <k> RPCRequest( REQ_ID, AnvilDumpState() )
          => #appendFile( #responseFile, #batchSep +String
              "{ \"jsonrpc\": \"2.0\"" +String
              ", \"id\": " +String Int2String(REQ_ID) +String
              ", \"result\": " )
          ~> #appendFileToFile( #responseFile, #snapshotFile( #getLatestBlockNumber ) )
          ~> #appendFile( #responseFile, "}" )
          ...
        </k>
        <rpcRequestID> _ => REQ_ID </rpcRequestID>

```

###############################################################################
## anvil_setBalance

```k
    rule <k> RPCRequest( REQ_ID, AnvilSetBalance(ADDR, NEW_BALANCE))
        => #saveStateDump
        ~> RPCResponse( null )
        ...
        </k>
        <rpcRequestID> _ => REQ_ID </rpcRequestID>
        <account>
            <acctID> ADDR </acctID>
            <balance> _ => NEW_BALANCE </balance>
            ...
        </account>

    rule <k> RPCRequest( REQ_ID, AnvilSetBalance(ADDR, NEW_BALANCE))
        => #saveStateDump
        ~> RPCResponse( null )
        ...
        </k>
        <rpcRequestID> _ => REQ_ID </rpcRequestID>
        <accounts>
            ( .Bag => 
                <account>
                    <acctID> ADDR </acctID>
                    <balance> NEW_BALANCE </balance>
                    ...
                </account>
            )
            ...
        </accounts> [owise]

```

###############################################################################
## debug_traceTransaction

At the point the debug_traceTransaction method is called, the transaction has already been
processed and its trace stored on disk. We just need to read the trace and return it.
Since the trace can be large, we avoid loading it into memory as a JSON object, and 
just build the response string directly.

```k

    rule <k> RPCRequest( REQ_ID, DebugTraceTransaction( _TX_HASH ) )
          => RPCResponse( null ) ...
         </k>
         <rpcRequestID> _ => REQ_ID </rpcRequestID>
        [owise]

    rule <k> RPCRequest( REQ_ID, DebugTraceTransaction( TX_HASH ) )
            => #appendFile( #responseFile, #batchSep +String
                "{ \"jsonrpc\": \"2.0\"" +String
                ", \"id\": " +String Int2String(REQ_ID) +String
                ", \"result\": " +String
                    "{ \"failed\":" +String #if TX_STATUS ==Int 1 #then "false" #else "true" #fi +String
                    ", \"gas\":" +String Int2String( TX_CUMULATIVE_GAS ) +String
                    ", \"returnValue\": \"\"" +String
                    ", \"structLogs\": [" )
            ~> #appendFileToFile( #responseFile, #traceFile( TXID ) )
            ~> #appendFile( #responseFile, "] } }" )
            ...
        </k>
        <rpcRequestID> _ => REQ_ID </rpcRequestID>
        <txReceipt>
            <txMsg>  TXID    </txMsg>
            <txHash> TX_HASH </txHash>
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

    syntax KItem ::= "#signTx"        [symbol(signTx)]
                   | #signTx(String)  [symbol(signTxWithSig)]
                   | "#signTxSuccess" [symbol(signTxSuccess)]
                   | "#signTxError"   [symbol(signTxError)]
    // --------------------------------------------------------
    
    // Sign a transaction with an account managed by this node   
    rule <k> #signTx
          => #signTx(ECDSASign( 
                Keccak256raw(#rlpEncodeTxData(LegacySignedTxData(TN, TP, TG, TT, TV, TD, B))),
                KEY
          )) ... </k>
        <origin> ACCTFROM </origin>
        <accountKeys> ... ACCTFROM |-> KEY ... </accountKeys>
        <mode> NORMAL </mode>
        <txPending> ListItem( TXID ) ... </txPending>
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

    // Error signing a transaction with an unknown account
    rule <k> #signTx => #signTxError ... </k>
         <origin>      ACCTFROM                    </origin>
         <accountKeys> KEYMAP                      </accountKeys>
         <mode>        NORMAL                      </mode>
         <txPending> ListItem(TXID) REST1 => REST1 </txPending>
         <txOrder>   ListItem(TXID) REST2 => REST2 </txOrder>
      requires notBool ACCTFROM in_keys(KEYMAP)
  
    // Sign a transaction with a given signature
    rule <k> #signTx(SIG:String) => #signTxSuccess ... </k>
         <chainID> B </chainID>
         <txPending> ListItem( TXID ) ... </txPending>
         <message>
           <msgID> TXID </msgID>
           <sigR> _ => #parseHexBytes( substrString( SIG, 0, 64 ) )           </sigR>
           <sigS> _ => #parseHexBytes( substrString( SIG, 64, 128 ) )         </sigS>
           <sigV> _ => 2 *Int B +Int #parseHexWord( substrString( SIG, 128, 130 ) ) +Int 35 </sigV>
           ...
         </message>

    syntax KItem ::= "#applyIntrinsicGas"                        [symbol(applyIntrinsicGas)]
                   | "#intrinsicGasSuccess"                      [symbol(intrinsicGasSuccess)]
                   | #intrinsicGasError( ExceptionalStatusCode ) [symbol(intrinsicGasError)]
    // -------------------------------------------------------------------------------------

    // Revert if insufficient gas
    rule <k> #applyIntrinsicGas
          => #intrinsicGasError( #if BAL <Int GLIMIT *Int GPRICE #then EVMC_BALANCE_UNDERFLOW #else EVMC_OUT_OF_GAS #fi)
          ...
         </k>
         <txPending> ListItem( TXID ) REST1 => REST1 </txPending>
         <txOrder>   ListItem( TXID ) REST2 => REST2 </txOrder>
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
    rule <k> #applyIntrinsicGas
          => #intrinsicGasSuccess ... </k>
         <origin> ACCTFROM </origin>
         <callGas> G0_INIT => GLIMIT -Int G0_INIT </callGas>
         <txPending> ListItem( TXID ) ... </txPending>
         <account>
           <acctID> ACCTFROM </acctID>
           <balance> BAL => BAL -Int (GLIMIT *Int GPRICE)</balance>
           ...
         </account>
         <message>
           <msgID>      TXID   </msgID>
           <txGasPrice> GPRICE </txGasPrice>
           <txGasLimit> GLIMIT </txGasLimit>
           ...
         </message>
         <traceBalance> TRBAL </traceBalance>
         <currentBalanceMutations>
            CBM => #if TRBAL #then CBM[ ACCTFROM <- BAL -Int (GLIMIT *Int GPRICE) ] #else CBM #fi
        </currentBalanceMutations>
      requires GLIMIT >=Int G0_INIT
       andBool BAL >=Int GLIMIT *Int GPRICE

    syntax KItem ::= "#executeTx" [symbol(executeTx)]
    // ---------------------------------------------------

    // Execute a contract creation transaction
    rule <k> #executeTx
          => #accessAccounts ACCTFROM #newAddr(ACCTFROM, NONCE) #precompiledAccountsSet(SCHED)
          ~> #loadAccessList(TA)
          ~> #create ACCTFROM #newAddr(ACCTFROM, NONCE) VALUE CODE
         ...
         </k>
         <schedule> SCHED </schedule>
         <gasPrice> _ => #effectiveGasPrice(TXID) </gasPrice>
         <origin> ACCTFROM </origin>
         <callDepth> _ => -1 </callDepth>
         <txPending> ListItem(TXID:Int) ... </txPending>
         <message>
            <msgID>      TXID     </msgID>
            <to>         .Account </to>
            <value>      VALUE    </value>
            <data>       CODE     </data>
            <txAccess>   TA       </txAccess>
            ...
         </message>
         <account>
            <acctID> ACCTFROM </acctID>
            <nonce> NONCE </nonce>
            ...
         </account>
         

    // Exeucte a contract call transaction
    rule <k> #executeTx
          => #accessAccounts ACCTFROM ACCTTO #precompiledAccountsSet(SCHED)
          ~> #loadAccessList(TA)
          ~> #call ACCTFROM ACCTTO ACCTTO VALUE VALUE DATA false
         ...
         </k>
         <traceNonce> TRNONCE </traceNonce>
         <schedule> SCHED </schedule>
         <origin> ACCTFROM </origin>
         <gasPrice> _ => #effectiveGasPrice(TXID) </gasPrice>
         <txPending> ListItem(TXID) ... </txPending>
         <callDepth> _ => -1 </callDepth>
         <message>
            <msgID>      TXID   </msgID>
            <to>         ACCTTO </to>
            <value>      VALUE  </value>
            <data>       DATA   </data>
            <txAccess>   TA     </txAccess>
            ...
         </message>
         <account>
            <acctID> ACCTFROM </acctID>
            <nonce> NONCE => NONCE +Int 1 </nonce>
            ...
         </account>
         <currentNonceMutations> CNM => #if TRNONCE #then CNM[ ACCTFROM <- NONCE +Int 1 ] #else CNM #fi </currentNonceMutations>
      requires ACCTTO =/=K .Account

```

###############################################################################
# Transaction Receipts

```k
    syntax KItem ::= #makeTxReceipt( Int ) [symbol(makeTxReceipt)]
    // -----------------------------------------------------------

    rule <k> #makeTxReceipt( TXID ) => .K ... </k>
         <txReceipts>
           ( .Bag =>
            <txReceipt>
                <txMsg>           TXID                           </txMsg>
                <txBlockNumber>   BN                             </txBlockNumber>
                <txHash>          #txHash( TXID )                </txHash>
                <txCumulativeGas> CGAS                           </txCumulativeGas>
                <txLogs>          LOGS                           </txLogs>
                <txLogsBloom>     .Bytes /* TODO */              </txLogsBloom>
                <txStatus>        bool2Word(SC ==K EVMC_SUCCESS) </txStatus>
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

```


###############################################################################
# Block Mining


The productions below are used to perform the mining of blocks, advancing the blockchain state.

```k
    syntax KItem ::= "#mineBlock"      [symbol(mineBlock)]
                   | "#computeRoots"   [symbol(computeRoots)]
                   | "#storeBlockData" [symbol(storeBlockData)]
    // --------------------------------------------------------

    syntax BlockData ::= #getBlockData( Int )        [function, symbol(getBlockData)]
                       | #getBlockDataByHash( Int )  [function, symbol(getBlockDataByHash)]
                       | "#getCurrentBlockData"      [function, symbol(getCurrentBlockData)]
    syntax Int       ::= #hashBlockData( BlockData ) [function, symbol(hashBlockData)]
                       | #hashBlockNumber( Int )     [function, symbol(hashBlockNumber)]
    // ---------------------------------------------------------------------------------

    rule <k> #mineBlock => #computeRoots ~> #storeBlockData ... </k>

    rule <k> #computeRoots => .K ... </k>
         <network>
                <txOrder> TXLIST </txOrder>
                ...
          </network>
          <block>
                <stateRoot>        _  => #parseHexWord( Keccak256( #rlpEncodeMerkleTree( #stateRoot ) ) ) </stateRoot>
                <transactionsRoot> _  => #parseHexWord( Keccak256( #rlpEncodeMerkleTree( #transactionsRoot( TXLIST ) ) ) ) </transactionsRoot>
                <receiptsRoot>     _  => #parseHexWord( Keccak256( #rlpEncodeMerkleTree( #receiptsRoot( TXLIST ) ) ) ) </receiptsRoot>
                ...
          </block>

    rule <k> #storeBlockData => #startBlock ... </k>
          <network>
                <txOrder>    _ => .List </txOrder>
                <txPending>  _ => .List </txPending>
                ...
          </network>
          <block>
                <number>           BN => BN +Int 1 </number>
                <timestamp>        TS => TS +Int 1 </timestamp>
                <previousHash>     _  => #hashBlockData( #getCurrentBlockData ) </previousHash>
                <stateRoot>        _ => 0 </stateRoot>
                <transactionsRoot> _ => 0 </transactionsRoot>
                <receiptsRoot>     _ => 0 </receiptsRoot>
                <logsBloom>        _ => .Bytes </logsBloom>
                ...
          </block>
          <blockStorage> M => M[ BN                                     <- #getCurrentBlockData ] </blockStorage>
          <blockHashes>  H => H[ #hashBlockData( #getCurrentBlockData ) <- BN                   ] </blockHashes>

    rule [[ #getCurrentBlockData => BlockData(
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

    rule [[ #getBlockDataByHash( BLOCK_HASH ) => {#getBlockData({BLOCK_HASHES[ BLOCK_HASH ]}:>Int)}:>BlockData ]]
        <blockStorage> BLOCK_STORAGE:Map </blockStorage>
        <blockHashes>  BLOCK_HASHES:Map </blockHashes>
        requires BLOCK_HASH in_keys(BLOCK_HASHES)
         andBool ( BLOCK_HASHES[ BLOCK_HASH ] orDefault -1 ) in_keys(BLOCK_STORAGE)

    rule #hashBlockData(BlockData(
            PH, HO, HC, HR, HT, HE, HB, HD, BN, HL, HG, HS, HX, HM, HN, _BF, _WR, _BG, _EG, _BR, _RR, _OBH
         ))
        => #blockHeaderHash(PH, HO, HC, HR, HT, HE, HB, HD, BN, HL, gas2Int( HG ), HS, HX, HM, HN)

    rule #hashBlockNumber( BN ) => #hashBlockData( #getBlockData( BN ) )
```

###############################################################################
## State Root
----------

```k
    syntax MerkleTree ::= "#stateRoot"                                   [function, symbol(stateRoot)]
                        | #putAccountsInTrie( MerkleTree, AccountsCell ) [function, symbol(putAccountsInTrie)]
    // -------------------------------------------------------------------------------------------------------

    rule [[ #stateRoot
         => #putAccountsInTrie(
                MerkleUpdateMap(
                    .MerkleTree,
                    #unparseMap( #precompiledAccountsMap(#precompiledAccountsSet(SCHED)) )
                ),
                <accounts> ACCTSCELL </accounts>
            )
        ]]
        <accounts> ACCTSCELL </accounts>
        <schedule> SCHED </schedule>

    // Convert a * -> bytes map to * -> string map
    syntax Map ::= #unparseMap( Map ) [function, symbol(unparseMap)]
    // -------------------------------------------------------------

    rule #unparseMap( .Map ) => .Map
    rule #unparseMap( (KEY |-> VAL) REST ) => (KEY |-> #unparseDataBytes({VAL}:>Bytes)) #unparseMap( REST )

    rule #putAccountsInTrie( TREE, <accounts> .Bag </accounts> ) => TREE
    rule #putAccountsInTrie(
            (TREE => MerkleUpdate(
                TREE,
                #rlpEncodeAddress( ACCT ),
                #unparseDataBytes( #rlpEncodeFullAccount(NONCE, BAL, STORAGE, CODE) )
            )),
            <accounts>
                ( <account>
                    <acctID>  ACCT    </acctID>
                    <nonce>   NONCE   </nonce>
                    <balance> BAL     </balance>
                    <storage> STORAGE </storage>
                    <code>    CODE    </code>
                    ...
                </account> => .Bag )
                ...
            </accounts>
        )

```

###############################################################################
## Transactions Root


```k
    syntax MerkleTree ::= #transactionsRoot( List )                     [function, symbol(transactionsRoot)]
                        | #transactionsRootAux( MerkleTree, Int, List ) [function, symbol(transactionsRootAux)]
    // --------------------------------------------------------------------------------------------------------

    rule #transactionsRoot( TXLIST ) => #transactionsRootAux( .MerkleTree, 0, TXLIST )
    
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
    syntax MerkleTree ::= #receiptsRoot( List )                     [function, symbol(receiptsRoot)]
                        | #receiptsRootAux( MerkleTree, Int, List ) [function, symbol(receiptsRootAux)]
    // ------------------------------------------------------------------------------------------------

    rule #receiptsRoot( TXLIST ) => #receiptsRootAux( .MerkleTree, 0, TXLIST )

    rule #receiptsRootAux( TREE, _, .List ) => TREE
    rule [[ #receiptsRootAux(
            ( TREE => MerkleUpdate(
                TREE,
                #rlpEncodeWord(I),
                #unparseDataBytes( #rlpEncodeReceipt(TX_STATUS, TX_CUMULATIVE_GAS, TX_LOGS_BLOOM, TX_LOGS) ) )
            ),
            ( I              => I +Int 1 ),
            ( ListItem(TXID) => .List ) _
        ) ]]
        <txReceipt>
            <txMsg>           TXID              </txMsg>
            <txStatus>        TX_STATUS         </txStatus>
            <txCumulativeGas> TX_CUMULATIVE_GAS </txCumulativeGas>
            <txLogs>          TX_LOGS           </txLogs>
            <txLogsBloom>     TX_LOGS_BLOOM     </txLogsBloom>
            ...
        </txReceipt>
```

###############################################################################
# JSON RPC Intermediate Representation

This section defines an intermediate represention for JSON RPC requests.

```k
    syntax KItem ::= RPCResponse
                   | RPCRequest
    // ------------------------

    syntax RPCResponse ::= RPCResponse( JSON )             [symbol(RPCStructuredResponse)]
                         | RPCErrorResponse( Int, String ) [symbol(RPCErrorResponse)]
    // ------------------------------------------------------------------------------

    syntax RPCRequest  ::= RPCRequest( Int, RPCRequestParams) [symbol(RPCRequestWithParams)]
    // -------------------------------------------------------------------------------------

    syntax RPCRequestParams ::= EthChainId()
                              | EthSendTransaction(
                                  Account , // from
                                  Account , // to
                                  Int , // gas
                                  Int , // gas price
                                  Int , // value
                                  Bytes // input
                                  )
                              | EthGetTransactionReceipt( Int )    // tx hash
                              | EthGetTransactionByHash( Int )     // tx hash
                              | EthGetCode( Int, Int )             // address, block number
                              | EthGetBalance( Int, Int )          // address, block number
                              | EthGetBlockByNumber( Int, Bool )   // block number, hydrated txs
                              | EthGetBlockByHash( Int, Bool )     // block hash
                              | EthGetTransactionCount( Int, Int ) // address, block number
                              | EthGetStorageAt( Int, Int, Int )   // address, slot, block number
                              | AnvilDumpState()                   // TODO: add options
                              | AnvilSetBalance( Int, Int )        // address, balance
                              | DebugTraceTransaction( Int )        // tx hash
                              | UnknownMethod()
                              | InvalidRequest()
    // ----------------------------------------
```

###############################################################################
## Convert JSON RPC representation to intermedaite representation

This section defines rules to convert from the JSON representation to the
intermediate representation.

```k
    syntax KItem ::= #rpcLoad( JSON )        [symbol(rpcLoad)]
                   | #rpcLoadSingle( JSON )  [symbol(rpcLoadSingle)]
                   | #rpcLoadBatch( JSON )   [symbol(rpcLoadBatch)]
    // ------------------------------------------------------------

    syntax RPCRequest       ::= #rpcLoadRequest( JSON )         [function, symbol(rpcLoadRequest)]
    syntax RPCRequestParams ::= #rpcLoadParams( String, JSON )  [function, symbol(rpcLoadParams)]
    // ------------------------------------------------------------------------------------------

    rule <k> #rpcLoad( [ J ] )
          => #batchPrefix
          ~> #rpcLoadBatch( [ J ] )
          ~> #batchSuffix
          ... </k>
    rule <k> #rpcLoad( { J } )
          => #clearResponseFile
          ~> #rpcLoadSingle( { J }) ... </k>

    rule <k> #rpcLoad( _ ) => RPCRequest( -1, InvalidRequest() ) ... </k>[owise]

    rule <k> RPCRequest( REQ_ID, UnknownMethod() ) => RPCErrorResponse(-32601, "Method not found") ... </k>
         <rpcRequestID> _ => REQ_ID </rpcRequestID>

    rule <k> RPCRequest( REQ_ID, InvalidRequest() ) => RPCErrorResponse(-32600, "Invalid Request") ... </k>
         <rpcRequestID> _ => REQ_ID </rpcRequestID>

    // RPC requests can be batched, in this case we iterate over the list
    rule <k> #rpcLoadBatch( [ .JSONs ] ) => .K ... </k>
    rule <k> #rpcLoadBatch( [ FIRST, REST ] )
        => #rpcLoadRequest( FIRST )
        ~> #rpcLoadBatch( [ REST ] ) ... </k>
        <rpcRequestBatchIndex> BATCH_ID => BATCH_ID +Int 1 </rpcRequestBatchIndex>

    rule <k> #rpcLoadBatch( _ ) => RPCRequest(-1, InvalidRequest()) ... </k> [owise]

    // If the request is not batched, we just load a single request
    rule <k> #rpcLoadSingle( { FIRST } ) 
        => #rpcLoadRequest( { FIRST } ) ... </k>

    rule #rpcLoadRequest( { J } )
            => #let REQ_ID  = #getInt(    "id",     { J }) #in
            #let METHOD     = #getString( "method", { J }) #in
            #let PARAMS_RAW = #getJSON(   "params", { J }) #in
            #let REQ_PARAMS = #rpcLoadParams( METHOD, PARAMS_RAW ) #in
            RPCRequest(REQ_ID, REQ_PARAMS)

    rule #rpcLoadRequest( _ ) => RPCRequest(-1, InvalidRequest()) [owise]

    rule #rpcLoadParams( "eth_chainId", [ .JSONs ] )
        => EthChainId()

    rule #rpcLoadParams( "eth_sendTransaction", [ J ])
        => #let FROM       = #getAccount( "from", J, DEFAULTSENDER ) #in
            #let TO        = #getAccount( "to"  , J, .Account ) #in
            #let GAS_LIMIT = #getWord( "gas" , J, 90000 ) #in
            #let GAS_PRICE = #getWord( "gasPrice", J, 0 ) #in
            #let VALUE     = #getWord( "value", J, 0 ) #in
            #let DATA      = #getBytes( "data", J, .Bytes ) #in
            EthSendTransaction( FROM, TO, GAS_LIMIT, GAS_PRICE, VALUE, DATA )

    rule #rpcLoadParams( "eth_getTransactionReceipt", [ TX_HASH:String ] )
        => EthGetTransactionReceipt( #parseWord( TX_HASH ) )

    rule #rpcLoadParams( "eth_getTransactionByHash", [ TX_HASH:String ] )
        => EthGetTransactionByHash( #parseWord( TX_HASH ) )

    rule #rpcLoadParams( "eth_getCode", [ ADDR:String, BLOCK_NUM:String ] )
        => #let ADDR_INT = #parseAddr( ADDR ) #in
            #let BLOCK_INT = #parseBlockNumber( BLOCK_NUM ) #in
            EthGetCode( ADDR_INT, BLOCK_INT )

    rule #rpcLoadParams( "eth_getBalance", [ ADDR:String, BLOCK_NUM:String ] )
        => #let ADDR_INT = #parseAddr( ADDR ) #in
           #let BLOCK_INT = #parseBlockNumber( BLOCK_NUM ) #in 
            EthGetBalance( ADDR_INT, BLOCK_INT )

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

    rule #rpcLoadParams( "anvil_setBalance", [ ADDR:String, NEW_BALANCE:String ] )
        => #let ADDR_INT = #parseAddr( ADDR ) #in
           #let BALANCE_INT = #parseWord( NEW_BALANCE ) #in
           AnvilSetBalance( ADDR_INT, BALANCE_INT )

    rule #rpcLoadParams( "debug_traceTransaction", [ TX_HASH:String, _OPTIONS:JSON ] )
        => DebugTraceTransaction( #parseWord( TX_HASH ) )

    rule #rpcLoadParams( _, _ ) => UnknownMethod() [owise]

    // Helpers

    syntax Int ::= #parseBlockNumber( String ) [function, symbol(parseBlockNumber)]
    // ----------------------------------------------------------------------------

    rule #parseBlockNumber( "earliest" ) => 0
    rule #parseBlockNumber( "latest" ) => #getLatestBlockNumber
    rule #parseBlockNumber( "safe" ) => #getLatestBlockNumber
    rule #parseBlockNumber( "finalized" ) => #getLatestBlockNumber
    rule #parseBlockNumber( "pending" ) => #getLatestBlockNumber +Int 1
    rule #parseBlockNumber( BN ) => #parseWord( BN ) [owise]

```
###############################################################################
# State Snapshots

## JSON encoding of Snapshots

This section defines rule to create a StateDump JSON object from the current
K configuration.

`#createStateDump` creaes a StateDump JSON object from the current configuration and places it on the K cell.
`#StateDump( JSON )` is a wrapper around the StateDump JSON object to disambiguate it from other KItems containing JSON data.

```k

    syntax KItem ::= "#createStateDump" [symbol(createStateDump)]
                   | #StateDump( JSON ) [symbol(StateDump)]
    // ----------------------------------------------------

    syntax JSON  ::= ( JSON )  [bracket]
    // ---------------------------------

    syntax JSONs ::= ( JSONs ) [bracket]
    // ---------------------------------

    syntax JSON  ::= accountsToJSON( AccountsCell )          [function, total, symbol(accountsToJSON)]
                   | accountToJSON( AccountCell )            [function, total, symbol(accountToJSON)]
                   | storageToJSON(Map)                      [function, total, symbol(accStorageToJson)]
                   | blocksToJSON(Map)                       [function, total, symbol(blocksToJSON)]
                   | blockToJSON(BlockData)                  [function, symbol(blockToJSON)]
                   | receiptsToJSON()                        [function, total, symbol(receiptsToJSON)]
                   | receiptToJSON( Int )                    [function, total, symbol(receiptToJSON)]
    // ----------------------------------------------------------------------------------------------

    syntax JSONs ::= accountsToJSONs( AccountsCell, JSONs )   [function, total, symbol(accountsToJSONs)]
                   | storageToJSONs( Map, JSONs )             [function, symbol(accStorageToJSONs)]
                   | blocksToJSONs( Int, Map, JSONs )         [function, total, symbol(blocksToJSONs)]
                   | receiptsToJSONs( Int, JSONs )            [function, total, symbol(receiptsToJSONs)]
    // -------------------------------------------------------------------------------------------------

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
    ) => addrToHex(ACC_ID) : {
        "balance": intToHex( ACC_BALANCE ),
        "code": bytesToHex( ACC_CODE ),
        "storage": storageToJSON( ACC_STORAGE ),
        "nonce" : ACC_NONCE
    }

    rule accountsToJSON( ACCS ) => { accountsToJSONs( ACCS, .JSONs ) }
    rule accountsToJSONs( <accounts> <account> ACC </account> ACCS:Bag </accounts>, ACCU)
            => accountsToJSONs( <accounts> ACCS </accounts>, (accountToJSON( <account> ACC </account> ) , ACCU) ) 
    rule accountsToJSONs( <accounts> .Bag </accounts>, ACCU ) => ACCU [owise]

    rule [[ receiptToJSON ( MSG_ID )
         => {
            "blockHash":         uint256ToHex( #hashBlockNumber( BLOCK_NUMBER ) ),
            "blockNumber":       BLOCK_NUMBER,
            "info": {
                "contract_address":  #if MSG_TO ==K .Account
                                     #then addrToHex( #newAddr({#sender( MSG_ID )}:>Int, MSG_NONCE) )
                                     #else null #fi,
                "exit":              "":String, // TODO
                "from":              accountToHex( #sender( MSG_ID ) ),
                "gas_used":          TX_CUMULATIVE_GAS,
                "nonce":             MSG_NONCE,
                "out":               bytesToHex( .Bytes ), // TODO
                "to":                accountToHex( MSG_TO ),
                "traces":            [{
                    "idx": 0,
                    "trace": {
                        "data": bytesToHex( MSG_DATA ),
                        "value": intToHex( MSG_VALUE ),
                        "gas_limit": MSG_GAS_LIMIT,
                        "gas_price": MSG_GAS_PRICE
                        // TODO: We're currently using debug_traceTransaction for tracing
                        // We may consider switching to this new format in the future
                    }
                }],
                "transaction_hash":  uint256ToHex( TX_HASH ),
                "transaction_index": 0, // We currently mine a block for each tx
                "sigV":              intToHex( MSG_SIGV ),
                "sigR":              bytesToHex( MSG_SIGR ),
                "sigS":              bytesToHex( MSG_SIGS )
            },
            "receipt": {
                "cumulativeGasUsed":  intToHex( TX_CUMULATIVE_GAS ),
                "logs":               [ .JSONs ], // TODO
                "logsBloom":          bytesToHex( TX_BLOOMFILTER, 256 ),
                "status":             intToHex( TX_STATUS ),
                "type":               intToHex( #dasmTxPrefix( MSG_TYPE ) )
            }
        } ]]
        <txReceipt>
            <txMsg>           MSG_ID            </txMsg>
            <txBlockNumber>   BLOCK_NUMBER      </txBlockNumber>
            <txHash>          TX_HASH           </txHash>
            <txCumulativeGas> TX_CUMULATIVE_GAS </txCumulativeGas>
            <txLogs>          _TX_LOGS          </txLogs>
            <txLogsBloom>     TX_BLOOMFILTER    </txLogsBloom>
            <txStatus>        TX_STATUS         </txStatus>
            ...
        </txReceipt>
        <message>
            <msgID>           MSG_ID            </msgID>
            <txNonce>         MSG_NONCE         </txNonce>
            <to>              MSG_TO            </to>
            <value>           MSG_VALUE         </value>
            <txType>          MSG_TYPE          </txType>
            <txGasLimit>      MSG_GAS_LIMIT     </txGasLimit>
            <txGasPrice>      MSG_GAS_PRICE     </txGasPrice>
            <data>            MSG_DATA          </data>
            <sigV>            MSG_SIGV          </sigV>
            <sigR>            MSG_SIGR          </sigR>
            <sigS>            MSG_SIGS          </sigS>
            ...
        </message>

    rule receiptsToJSON() => [ receiptsToJSONs( 1, .JSONs ) ] [priority(50)]

    rule [[ receiptsToJSONs( MSG_ID, ACCU)
         => receiptsToJSONs( MSG_ID +Int 1, (receiptToJSON( MSG_ID ) , ACCU) ) ]]
        <txReceipt>
            <txMsg> MSG_ID </txMsg>
            ...
        </txReceipt>

    rule receiptsToJSONs( _, ACCU ) => ACCU [owise]

    rule <k> #createStateDump
        => #StateDump({
            "best_block_number": #getLatestBlockNumber,
            "block": {
                "number": intToHex( #getLatestBlockNumber ),
                "beneficiary": addrToHex( BLOCK_COINBASE ),
                "timestamp": intToHex( BLOCK_TIMESTAMP ),
                "gas_limit": BLOCK_GAS_LIMIT,
                "basefee": BLOCK_BASE_FEE,
                "difficulty": intToHex( BLOCK_DIFFICULTY ),
                "prevrandao": uint256ToHex( BLOCK_MIX_HASH ),
                "blob_excess_gas_and_price": {
                    "excess_blob_gas": BLOCK_EXCESS_BLOB_GAS,
                    "blob_gasprice": BLOCK_BLOB_GAS_USED
                }
            },
            "accounts": accountsToJSON( <accounts> ACCOUNTS </accounts> ),
            "blocks": blocksToJSON( BLOCK_STORAGE ),
            "transactions": receiptsToJSON()
        }) ...
    </k>
    <block>
        <coinbase>      BLOCK_COINBASE        </coinbase>
        <timestamp>     BLOCK_TIMESTAMP       </timestamp>
        <gasLimit>      BLOCK_GAS_LIMIT       </gasLimit>
        <baseFee>       BLOCK_BASE_FEE        </baseFee>
        <difficulty>    BLOCK_DIFFICULTY      </difficulty>
        <excessBlobGas> BLOCK_EXCESS_BLOB_GAS </excessBlobGas>
        <blobGasUsed>   BLOCK_BLOB_GAS_USED   </blobGasUsed>
        <mixHash>       BLOCK_MIX_HASH        </mixHash>
        ...
    </block>
    <accounts> ACCOUNTS </accounts>
    <blockStorage> BLOCK_STORAGE </blockStorage>

    rule blocksToJSON( BS ) => [ blocksToJSONs( 0, BS, .JSONs ) ] [priority(50)]
    rule blocksToJSONs( BN, BS, ACCU) => blockToJSON({BS[BN]}:>BlockData), blocksToJSONs( BN +Int 1, BS, ACCU )
        requires BN in_keys(BS)
    rule blocksToJSONs( _, _, ACCU ) => ACCU [owise]

    rule blockToJSON( BlockData(
            PH, HO, HC, HR, HT, HE, HB, HD, BN, HL, HG, HS, HX, HM, HN, BF, WR, BG, EG, BR, RR, OBH
         ))
        => { "header": {
                "parentHash":       uint256ToHex( PH ),
                "sha3Uncles":       uint256ToHex( HO ),
                "miner":            addrToHex( HC ),
                "stateRoot":        uint256ToHex( HR ),
                "transactionsRoot": uint256ToHex( HT ),
                "receiptsRoot":     uint256ToHex( HE ),
                "logsBloom":        bytesToHex( HB , 256),
                "difficulty":       intToHex( HD ),
                "number":           intToHex( BN ),
                "gasLimit":         intToHex( HL ),
                "gasUsed":          #if isInt(HG) #then intToHex( HG ) #else "0x0" #fi,
                "timestamp":        intToHex( HS ),
                "extraData":        bytesToHex( HX ),
                "prevrandao":       intToHex( HM ),
                "nonce":            intToHex( HN, 8 ),
                "baseFeePerGas":    intToHex( BF ),
                "withdrawalsRoot":  uint256ToHex( WR ),
                "blobGasUsed":      intToHex( BG ),
                "excessBlobGas":    intToHex( EG ),
                "parentBeaconBlockRoot": uint256ToHex( BR ),
                "requestsHash":     uint256ToHex( RR )
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

    syntax KItem ::= #loadSnapshot( Snapshot )           [symbol(loadSnapshot)]
                   | #loadBlocks( Blocks )               [symbol(loadBlocks)]
                   | #loadBlock( BlockData )             [symbol(loadBlock)]
                   | #loadCurrentBlock( Int )            [symbol(loadCurrentBlock)]
                   | #loadAccounts( Accounts )           [symbol(loadAccounts)]
                   | #loadAccount( AccountData )         [symbol(loadAccount)]
                   | #loadTransactions( Transactions )   [symbol(loadTransactions)]
                   | #loadTransaction( TransactionData ) [symbol(loadTransaction)]
    // ---------------------------------------------------------------------------

    rule <k> #loadSnapshot( Snapshot(LATEST_BLOCK_NUMBER, ACCOUNTS, BLOCKS, TRANSACTIONS) )
          => #loadAccounts( ACCOUNTS )
          ~> #loadBlocks( BLOCKS )
          ~> #loadTransactions( TRANSACTIONS )
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
        <timestamp> TS => maxInt( TS, #getBlockTimestamp( BLOCK_DATA ) +Int 1) </timestamp>

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
                    <origStorage> ACCT_STORAGE </origStorage>
                    <storage> ACCT_STORAGE </storage>
                    <code>    ACCT_CODE    </code>
                    <nonce>   ACCT_NONCE   </nonce>
                    ...
                </account>
            )
            ...
        </accounts>

    rule <k> #loadTransactions( .Transactions ) => .K ... </k>
    rule <k> #loadTransactions( TRANSACTION_DATA , REST )
          => #loadTransaction( TRANSACTION_DATA )
          ~> #loadTransactions( REST ) ... </k>

    rule <k> #loadTransaction( TransactionData(
            _BLOCK_HASH,
            BLOCK_NUMBER,
            TransactionInfo(
                _TX_CONTRACT_ADDR,
                _TX_EXIT,
                _TX_FROM,
                _TX_GAS_USED,
                TX_NONCE,
                _TX_OUT,
                TX_TO,
                [ TraceRoot( TraceData( MSG_DATA, TX_VALUE, TX_GAS_LIMIT, TX_GAS_PRICE ) ) ],
                TX_HASH,
                _TX_INDEX,
                TX_SIG_V,
                TX_SIG_R,
                TX_SIG_S
            ),
            ReceiptData(
                R_CUMULATIVE_GAS_USED,
                R_LOGS,
                R_LOGS_BLOOM,
                R_STATUS,
                R_TX_TYPE
            ) ) )
         => .K ... </k>
        <chainID> CHAIN_ID </chainID>
        <messages>
            ( .Bag => <message>
                    <msgID>   BLOCK_NUMBER </msgID>
                    <txNonce> TX_NONCE     </txNonce>
                    <txGasPrice> TX_GAS_PRICE </txGasPrice>
                    <txGasLimit> TX_GAS_LIMIT </txGasLimit>
                    <to>      TX_TO        </to>
                    <txType>  R_TX_TYPE    </txType>
                    <value>   TX_VALUE     </value>
                    <data>    MSG_DATA     </data>
                    <sigV>    TX_SIG_V     </sigV>
                    <sigR>    TX_SIG_R     </sigR>
                    <sigS>    TX_SIG_S     </sigS>
                    <txChainID> CHAIN_ID     </txChainID>
                    ...
                </message>
            ) ...
        </messages>
        <number> _ => BLOCK_NUMBER +Int 1 </number>
        <txReceipts>
            ( .Bag => <txReceipt>
                    <txMsg>           BLOCK_NUMBER     </txMsg>
                    <txBlockNumber>   BLOCK_NUMBER     </txBlockNumber>
                    <txHash>          TX_HASH          </txHash>
                    <txCumulativeGas> R_CUMULATIVE_GAS_USED </txCumulativeGas>
                    <txLogs>          R_LOGS           </txLogs>
                    <txLogsBloom>     R_LOGS_BLOOM     </txLogsBloom>
                    <txStatus>        R_STATUS         </txStatus>
                </txReceipt>
            ) ...
        </txReceipts>

    // Intermediate representations

    syntax Snapshot ::= Snapshot(
            Int,
            Accounts,
            Blocks,
            Transactions
        ) [symbol(Snapshot)]
        | #parseSnapshot( JSON ) [function, symbol(parseSnapshot)]
    // -----------------------------------------------------------

    syntax AccountData ::= AccountData(
            Int,   // acctID
            Int,   // balance
            Map,   // storage
            Bytes, // code
            Int    // nonce
        ) [symbol(AccountData)]
        | #parseAccount( JSON ) [function, symbol(parseAccount)]
    // ---------------------------------------------------------

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
        ) [symbol(BlockData)]
        | #parseBlock( JSON ) [function, symbol(parseBlock)]
    // -----------------------------------------------------

    syntax TransactionData ::= TransactionData(
            Int, // block_hash
            Int, // block_number
            TransactionInfo, // info
            ReceiptData // receipt
        ) [symbol(TransactionData)]
        | #parseTransaction( JSON ) [function, symbol(parseTransaction)]
    // -----------------------------------------------------------------

    syntax TransactionInfo ::= TransactionInfo(
            Account,    // contract_address
            String,     // exit
            Int,        // from
            Int,        // gas_used
            Int,        // nonce
            Bytes,      // out
            Account,    // to
            TraceRoots, // traces
            Int,        // transaction hash
            Int,        // transaction index
            Int,        // sigV
            Bytes,      // sigR
            Bytes       // sigS
        ) [symbol(TransactionInfo)]
        | #parseTransactionInfo( JSON ) [function, symbol(parseTransactionInfo)]
    // -------------------------------------------------------------------------

    syntax ReceiptData ::= ReceiptData(
            Int,   // cumulativeGasUsed
            List,  // logs
            Bytes, // logsBloom
            Int,   // status
            TxType
        ) [symbol(ReceiptData)]
        | #parseReceipt( JSON ) [function, symbol(parseReceipt)]
    // ---------------------------------------------------------

    syntax TraceRoot ::= TraceRoot( TraceData )  [symbol(TraceRoot)]
                       | #parseTraceRoot( JSON ) [function, symbol(parseTraceRoot)]
    // ----------------------------------------------------------------------------

    syntax TraceData ::= TraceData(
            data: Bytes,
            value: Int,
            gasLimit: Int,
            gasPrice: Int
        ) [symbol(TraceData)]
        | #parseTraceData( JSON ) [function, symbol(parseTraceData)]
    // -------------------------------------------------------------

    syntax Map ::= #parseStorage( JSON )         [function, symbol(parseStorage)]
                 | #parseStorageAux( JSON, Map ) [function, symbol(parseStorageAux)]
    // -----------------------------------------------------------------------------

    syntax Accounts ::= List{AccountData, ","}
                      | "[" Accounts "]"       [bracket]
                      | #parseAccounts( JSON ) [function, symbol(parseAccounts)]
    // -------------------------------------------------------------------------

    syntax Blocks   ::= List{BlockData, ","}
                      | "[" Blocks "]"       [bracket]
                      | #parseBlocks( JSON ) [function, symbol(parseBlocks)]
    // ---------------------------------------------------------------------

    syntax Transactions ::= List{TransactionData, ","}
                      | "[" Transactions "]"       [bracket]
                      | #parseTransactions( JSON ) [function, symbol(parseTransactions)]
    // ---------------------------------------------------------------------------------

    syntax TraceRoots ::= List{TraceRoot, ","}
                      | "[" TraceRoots "]"       [bracket]
                      | "(" TraceRoots ")"       [bracket]
                      | #parseTraceRoots( JSON ) [function, symbol(parseTraceRoots)]
    // -----------------------------------------------------------------------------

    syntax Int ::= #getBlockNumber( BlockData ) [function, symbol(getBlockNumber)]
    // ---------------------------------------------------------------------------

    rule #getBlockNumber( BlockData( _, _, _, _, _, _, _, _, BN, _, _, _, _, _, _, _, _, _, _, _, _, _) ) => BN

    syntax Int ::= #getBlockTimestamp( BlockData ) [function, symbol(getBlockTimestamp)]
    // ---------------------------------------------------------------------------------

    rule #getBlockTimestamp( BlockData( _, _, _, _, _, _, _, _, _, _, _, TS, _, _, _, _, _, _, _, _, _, _) ) => TS

    rule #parseSnapshot( SNAPSHOT_JSON )
        => #let BEST_BLOCK_NUMBER = #getInt( "best_block_number", SNAPSHOT_JSON, 0 ) #in
           #let ACCOUNTS_JSON     = #getJSON( "accounts", SNAPSHOT_JSON, { .JSONs } ) #in
           #let BLOCKS_JSON       = #getJSON( "blocks",   SNAPSHOT_JSON, [ .JSONs ] ) #in
           #let TRANSACTIONS_JSON = #getJSON( "transactions", SNAPSHOT_JSON, { .JSONs } ) #in
           Snapshot(
               BEST_BLOCK_NUMBER,
               #parseAccounts( ACCOUNTS_JSON ),
               #parseBlocks( BLOCKS_JSON ),
               #parseTransactions( TRANSACTIONS_JSON )
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
            #getWord( "prevrandao",       BLOCK_HEADER, 0 ),
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

    rule #parseTransactions( [ .JSONs ] ) => .Transactions
    rule #parseTransactions( [ FIRST, REST ] ) => #parseTransaction( FIRST ) , #parseTransactions( [ REST ] )

    rule #parseTransaction( TX_JSON )
        => #let BLOCK_HASH    = #getWord( "blockHash", TX_JSON, 0 ) #in
           #let BLOCK_NUMBER  = #getInt( "blockNumber", TX_JSON, 0 ) #in
           #let INFO          = #parseTransactionInfo( #getJSON( "info", TX_JSON ) ) #in
           #let RECEIPT       = #parseReceipt( #getJSON( "receipt", TX_JSON ) ) #in
           TransactionData(
               BLOCK_HASH,
               BLOCK_NUMBER,
               INFO,
               RECEIPT
           )

    rule #parseTransactionInfo( INFO_JSON )
        => #let TX_CONTRACT_ADDR = #getAccount( "contract_address", INFO_JSON, .Account ) #in
           #let TX_EXIT          = #getString( "exit", INFO_JSON, "" ) #in
           #let TX_FROM          = #getAddr( "from", INFO_JSON, 0 ) #in
           #let TX_GAS_USED      = #getInt( "gas_used", INFO_JSON, 0 ) #in
           #let TX_NONCE         = #getInt( "nonce", INFO_JSON, 0 ) #in
           #let TX_OUT           = #getBytes( "out", INFO_JSON, .Bytes ) #in
           #let TX_TO            = #getAccount( "to", INFO_JSON, .Account ) #in
           #let TX_TRACES        = #parseTraceRoots( #getJSON( "traces", INFO_JSON, [ .JSONs ] ) ) #in
           #let TX_HASH          = #getWord( "transaction_hash", INFO_JSON, 0 ) #in
           #let TX_INDEX         = #getInt( "transaction_index", INFO_JSON, 0 ) #in
           #let TX_SIGV          = #getWord( "sigV", INFO_JSON, 0 ) #in
           #let TX_SIGR          = #getBytes( "sigR", INFO_JSON, .Bytes ) #in
           #let TX_SIGS          = #getBytes( "sigS", INFO_JSON, .Bytes ) #in
           TransactionInfo(
               TX_CONTRACT_ADDR,
               TX_EXIT,
               TX_FROM,
               TX_GAS_USED,
               TX_NONCE,
               TX_OUT,
               TX_TO,
               TX_TRACES,
               TX_HASH,
               TX_INDEX,
               TX_SIGV,
               TX_SIGR,
               TX_SIGS
           )

    rule #parseTraceRoots( [ .JSONs ] ) => .TraceRoots
    rule #parseTraceRoots( [ FIRST, REST ] ) => #parseTraceRoot( FIRST ) , #parseTraceRoots( [ REST ] )

    rule #parseTraceRoot( TRACE_JSON )
        => #let DATA = #parseTraceData( #getJSON( "trace", TRACE_JSON ) ) #in
           TraceRoot( DATA )

    rule #parseTraceData( TRACE_JSON )
        => #let DATA_BYTES = #getBytes( "data", TRACE_JSON, .Bytes ) #in
           #let TX_VALUE   = #getWord( "value", TRACE_JSON, 0 ) #in
           #let GAS_LIMIT  = #getInt( "gas_limit", TRACE_JSON, 0 ) #in
           #let GAS_PRICE  = #getInt( "gas_price", TRACE_JSON, 0 ) #in
           TraceData( DATA_BYTES, TX_VALUE, GAS_LIMIT, GAS_PRICE )

    rule #parseReceipt( RECEIPT_JSON )
        => #let CUMULATIVE_GAS  = #getWord( "cumulativeGasUsed", RECEIPT_JSON, 0 ) #in
           #let LOG_SET         = .List /* TODO */ #in
           #let BLOOM_FILTER    = #getBytes( "logsBloom",  RECEIPT_JSON, .Bytes )  #in
           #let TX_STATUS       = #getWord( "status",      RECEIPT_JSON, 0 )       #in
           #let TX_TYPE         = #asmTxPrefix( #getWord( "type",        RECEIPT_JSON, 0 ) ) #in
           ReceiptData(
               CUMULATIVE_GAS,
               LOG_SET,
               BLOOM_FILTER,
               TX_STATUS,
               TX_TYPE
           )

```
###############################################################################
# Input/Output

## Sending RPC Responses

This section defines rules to write RPCResponses to a file.

```k

      syntax String ::= "#responseFile" [function, total, symbol(responseFile)]
      // ----------------------------------------------------------------------

      rule [[ #responseFile => IO_DIR +String "/response.json" ]]
        <ioDir> IO_DIR </ioDir>

      rule <k> RPCResponse( JSON_RESPONSE )
            => #appendFile(#responseFile, #batchSep +String JSON2String({
                  "jsonrpc" : "2.0",
                  "id"      : REQ_ID,
                  "result"  : JSON_RESPONSE
            }))
            ... </k>
            <rpcRequestID> REQ_ID </rpcRequestID>

      rule <k> RPCErrorResponse( ERROR_CODE, ERROR_MESSAGE )
            => #appendFile(#responseFile, #batchSep +String JSON2String({
                  "jsonrpc" : "2.0",
                  "id"      : #if 0 <=Int REQ_ID #then REQ_ID #else null #fi,
                  "error"   : {
                      "code": ERROR_CODE,
                      "message": ERROR_MESSAGE
                  }
            }))
            ... </k>
            <rpcRequestID> REQ_ID </rpcRequestID>

    syntax KItem ::= "#batchPrefix"       [symbol(batchPrefix)]
                   | "#batchSuffix"       [symbol(batchSuffix)]
                   | "#clearResponseFile" [symbol(clearResponseFile)]
    // --------------------------------------------------------------

    rule <k> #clearResponseFile => #writeFile(#responseFile, "") ... </k>

    rule <k> #batchPrefix => #writeFile(#responseFile, "[\n") ... </k>

    rule <k> #batchSuffix => #appendFile(#responseFile, "\n]") ... </k>

    syntax String ::= "#batchSep" [function, total, symbol(batchSep)]
    // --------------------------------------------------------------

    rule [[ #batchSep => ",\n" ]]
        <rpcRequestBatchIndex> BATCH_INDEX </rpcRequestBatchIndex>
        requires 0 <Int BATCH_INDEX
    
    rule #batchSep => "" [owise]

```

## Loading RPCRequests

This section defines rules to read a RPCRequests from a file.

```k
    syntax KItem ::= "#loadRpcRequest" [symbol(loadRpcRequest)]
    // --------------------------------------------------------
    
    syntax String ::= "#requestFile" [function, total, symbol(requestFile)]
    // --------------------------------------------------------------------

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

    syntax KItem ::= "#writeStateDump" [symbol(writeStateDump)]
                   | "#saveStateDump"  [symbol(saveStateDump)]
    // -------------------------------------------------------

    syntax String ::= #snapshotFile( Int ) [function, total, symbol(snapshotFile)]
    // ---------------------------------------------------------------------------

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
          => #writeFile( #snapshotFile( #getLatestBlockNumber ), JSON2String( SD ) )
          ...
        </k>

```
## Loading StateDump from Disk

This secion defines rules to read a StateDump JSON object from disk.

```k

    syntax KItem ::= #loadSnapshotFile( Int ) [symbol(loadSnapshotFile)]
    // -----------------------------------------------------------------

    rule <k> #loadSnapshotFile( BLOCK_NUMBER )
          => #let CONTENTS:IOString = #readFile( #snapshotFile( BLOCK_NUMBER ) )
              #in #loadSnapshot( #parseSnapshot( String2JSON( {CONTENTS}:>String ) ) )
              ...
         </k>

    syntax KItem ::= "#loadLatestSnapshot" [symbol(loadLatestSnapshot)]
    // ----------------------------------------------------------------

    rule <k> #loadLatestSnapshot
          => #loadSnapshotFile( #getInt( "latest_block_number", #loadMetadata, 0 ) )
          ...
         </k>

    syntax String ::= "#metadataFile" [function, total, symbol(metadataFile)]
    // ----------------------------------------------------------------------
    
    rule [[ #metadataFile=> IO_DIR +String "/metadata.json" ]]
        <ioDir> IO_DIR </ioDir>

    syntax KItem ::= "#saveMetadata" [symbol(saveMetadata)]
    // ----------------------------------------------------

    syntax JSON ::= "#loadMetadata" [function, symbol(loadMetadata)]
    // -------------------------------------------------------------

    rule #loadMetadata =>
            #let CONTENTS:IOString = #readFile( #metadataFile ) #in
            String2JSON( {CONTENTS}:>String )

    rule <k> #saveMetadata
          => #writeFile(
                #metadataFile,
                JSON2String( { "latest_block_number": #getLatestBlockNumber } )
            )
          ... </k>

```

```k

    syntax String ::= #traceFile( Int ) [function, total, symbol(traceFile)]
    // ---------------------------------------------------------------------

    rule [[ #traceFile( MSG_ID ) => IO_DIR +String "/transactions/trace_" +String Int2String( MSG_ID ) +String ".json" ]]
      <ioDir> IO_DIR </ioDir>

    rule <k> #storeTraceItem TRITEM
          => #appendFile(
                #traceFile( #getNextTxID ),
                #logSep +String JSON2String( traceItemToJson( TRITEM ) )
             ) ...
         </k>
         <stepCount> STEP_COUNT  => STEP_COUNT +Int 1 </stepCount>

    syntax String ::= "#logSep" [function, total, symbol(logSep)]
    // ----------------------------------------------------------

    rule [[ #logSep => ",\n" ]]
        <stepCount> STEP_COUNT </stepCount>
        requires 0 <Int STEP_COUNT

    rule #logSep => "" [owise]

endmodule
```