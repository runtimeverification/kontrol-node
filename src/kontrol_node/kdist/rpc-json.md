
This module defines rules for loading JSON RPC requests from disk,
and writing JSON RPC responses to disk. When a request is loaded 
it is immediately dispatched for execution.

```k
requires "fs.md"
requires "json.md"
requires "config.md"
requires "plugin/krypto.md"


module RPC-JSON
      imports KRYPTO
      imports FILE-SYSTEM
      imports JSON
      imports KONTROL-NODE-CONFIG
      imports SERIALIZATION


      syntax KItem ::= #loadRpcRequests( String )
                     | #saveRpcResponse( String )
                     | #processTx( Int )

```

===============================================================================
JSON RPC Intermediate Representation

This section defines an intermediate represention for JSON RPC requests.

```k
      syntax KResult ::= RPCResponse | RPCRequest

      syntax RPCResponse ::= RPCResponse( JSON )
      syntax RPCRequest  ::= RPCRequest( Int, RPCRequestParams)

      syntax RPCRequestParams ::= EthSendTransaction(
                                    Int , // from
                                    Int , // to
                                    Int , // gas
                                    Int , // gas price
                                    Int , // value
                                    Bytes // input
                                  )

```

===============================================================================
Utilities for working with JSON objects

```k
      syntax JSON ::= #getJSON ( JSONKey, JSON )      [function]

      rule #getJSON( KEY, { KEY : J, _     } ) => J
      rule #getJSON(   _, { .JSONs         } ) => null
      rule #getJSON( KEY, { KEY2 : _, REST } ) => #getJSON( KEY, { REST } )
            requires KEY =/=K KEY2

      syntax Int ::= #getInt(JSONKey, JSON) [function]
      rule #getInt( KEY, J ) => {#getJSON( KEY, J )}:>Int

      syntax String ::= #getString(JSONKey, JSON) [function]
      rule #getString( KEY, J ) => {#getJSON( KEY, J )}:>String

      syntax Int ::= #getWord(JSONKey, JSON, Int) [function]
      rule #getWord( KEY, J, DEF_VAL ) => #let RAW = #getJSON( KEY, J ) #in
                                          #if RAW ==K null #then DEF_VAL #else #parseWord( {RAW}:>String ) #fi

      syntax Int ::= #getAddr(JSONKey, JSON, Int) [function]
      rule #getAddr( KEY, J, DEF_VAL ) => #let RAW = #getJSON( KEY, J ) #in
                                          #if RAW ==K null #then DEF_VAL #else #parseAddr( {RAW}:>String ) #fi

      syntax Bytes ::= #getBytes(JSONKey, JSON, Bytes) [function]
      rule #getBytes( KEY, J, DEF_VAL ) => #let RAW = #getJSON( KEY, J ) #in
                                           #if RAW ==K null #then DEF_VAL #else #parseByteStack( {RAW}:>String ) #fi

      syntax String ::= intToHex(Int)     [function, total]
                      | bytesToHex(Bytes) [function, total]

      rule bytesToHex( BYTES ) => "0x" +String Bytes2Hex( BYTES ) 
      rule intToHex( A:Int ) => "0x" +String Base2String(A, 16)
            requires A >=Int 0
      rule intToHex( A:Int ) => "-0x" +String Base2String( absInt(A), 16) [owise]

```

===============================================================================
Convert JSON RPC representation to intermedaite representation

This section defines rules to convert from the JSON representation to the
intermediate representation.

```k
      syntax KItem ::= #rpcLoad( JSON )

      syntax RPCRequest       ::= #rpcLoadRequest( JSON )         [function]
      syntax RPCRequestParams ::= #rpcLoadParams( String, JSON )  [function]

      rule <k> #rpcLoad( [ .JSONs ] ) => .K ... </k>
      rule <k> #rpcLoad( [ FIRST, REST ] )
            => #rpcLoadRequest( FIRST )
            ~> #rpcLoad( [ REST ] ) ... </k>

      rule #rpcLoadRequest( J )
             => #let REQ_ID     = #getInt(    "id",     J) #in
                #let METHOD     = #getString( "method", J) #in
                #let PARAMS_RAW = #getJSON(   "params", J) #in
                #let REQ_PARAMS = #rpcLoadParams( METHOD, PARAMS_RAW ) #in
                RPCRequest(REQ_ID, REQ_PARAMS)

      syntax Int ::= "DEFAULTSENDER" [function]
      rule DEFAULTSENDER => #parseAddr("0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266")

      rule #rpcLoadParams( "eth_sendTransaction", [ J ])
            => #let FROM  = #getAddr( "from", J, DEFAULTSENDER ) #in
               #let TO    = #getAddr( "to"  , J, 0 ) #in
               #let GAS_LIMIT = #getWord( "gas" , J, pow24 ) #in
               #let GAS_PRICE = #getWord( "gas_price", J, 1 ) #in
               #let VALUE = #getWord( "value", J, 0 ) #in
               #let DATA  = #getBytes( "data", J, .Bytes ) #in
               EthSendTransaction( FROM, TO, GAS_LIMIT, GAS_PRICE, VALUE, DATA )
      
```

===============================================================================
Execute RPC Requests

This section defines rules to load rpc requests into the current configuration
and dispatch their execution.

```k


```

===============================================================================
JSON RPC Response

This section defines rules to create JSON RPC response objects from the current
configuration.

```k 

      syntax KItem ::= "#ethSendTransactionResponse"
                     | "#ethGetTransactionByHashResponse"
                     | "#ethGetTransactionReceiptResponse"

      rule <k> #ethSendTransactionResponse
            => RPCResponse( TX_HASH )
            ... </k>
            <currentTxID>  TXID    </currentTxID>
            <txReceipt>
                  <txHash> TX_HASH </txHash>
                  <txID>   TXID    </txID>
                  ...
            </txReceipt>

      rule <k> #ethGetTransactionByHashResponse
            => RPCResponse({
                  "type"     : "0x0",
                  "nonce"    : intToHex( TX_NONCE ),
                  "to"       : #if TX_TO ==Int 0 #then null #else intToHex( TX_TO) #fi,
                  "gas"      : intToHex( TX_GAS_LIMIT ),
                  "value"    : intToHex( TX_VALUE ),
                  "input"    : bytesToHex( TX_DATA ),
                  "gasPrice" : intToHex( TX_GAS_PRICE ),
                  "chainId"  : intToHex( TX_CHAIN_ID ),
                  "v"        : intToHex( TX_V ),
                  "r"        : bytesToHex( TX_R ),
                  "s"        : bytesToHex( TX_S )
            })
           ... </k>
           <currentTxID>        MSG_ID       </currentTxID>
           <message>
                <msgID>         MSG_ID       </msgID>
                <txNonce>       TX_NONCE     </txNonce>
                <txGasPrice>    TX_GAS_PRICE </txGasPrice>
                <txGasLimit>    TX_GAS_LIMIT </txGasLimit>
                <to>            TX_TO        </to>
                <value>         TX_VALUE     </value>
                <sigV>          TX_V         </sigV>
                <sigR>          TX_R         </sigR>
                <sigS>          TX_S         </sigS>
                <data>          TX_DATA      </data>
                <txChainID>     TX_CHAIN_ID  </txChainID>
                <txType>        Legacy       </txType>
                ...
           </message>

      rule <k> #ethGetTransactionReceiptResponse => RPCResponse({
                  "type"              : "0x0",
                  "transactionHash"   : TX_HASH,
                  "transactionIndex"  : "0x0", // kontrol-node always includes exactly one tx per block
                  "blockHash"         : intToHex( BLOCK_HASH ),
                  "blockNumber"       : intToHex( BLOCK_NUMBER ),
                  "from"              : intToHex( FROM ),
                  "to"                : intToHex( TO ),
                  "cumulativeGasUsed" : intToHex( CGAS ), // TODO: What is the difference between cumulativeGasUsed and gasUsed
                  "gasUsed"           : intToHex( CGAS ), 
                  "contractAddress"   : #if TO ==K .Account #then intToHex( #newAddr(FROM, TX_NONCE) ) #else null #fi,
                  "logs"              : [ .JSONs ], // TODO
                  "status"            : #if TX_STATUS ==K EVMC_SUCCESS #then true #else false #fi,
                  "effectiveGasPrice" : null // TODO
            }) ... </k>
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
===============================================================================
Writing RPCResponses to Disk

This section defines rules to write RPCResponses to disk.

```k

      syntax String ::= #responseFile(
            String, // IO dir
            Int     // request id
      ) [function]

      rule #responseFile( IO_DIR, REQ_ID ) => IO_DIR +String "/responses/response_" +String Int2String( REQ_ID ) +String ".json"

      rule <k> RPCResponse( JSON_RESPONSE )
            ~> #saveRpcResponse( IO_DIR )
            => #writeFile( #responseFile( IO_DIR, REQ_ID ), JSON2String( {
                  "jsonrpc" : "2.0",
                  "id"      : REQ_ID,
                  "result"  : JSON_RESPONSE
            }) )
            ...
            </k>
            <rpcRequestID> REQ_ID </rpcRequestID>

```

===============================================================================
Loading RPCRequests from Disk

This secion defines rules to read a RPCRequests from disk.

```k

      syntax String ::= #requestsFile( String ) [function, total]

      rule #requestsFile( IO_DIR ) => IO_DIR +String "/requests.json"

      rule <k> #loadRpcRequests( IO_DIR )
            => #let CONTENTS:IOString = #readFile( #requestsFile( IO_DIR ) )
                  #in #rpcLoad( String2JSON( {CONTENTS}:>String ) )
                  ...
            </k>


endmodule
```