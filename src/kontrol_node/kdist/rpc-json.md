
This module defines rules for loading JSON RPC requests from disk,
and writing JSON RPC responses to disk. When a request is loaded 
it is immediately dispatched for execution.

```k
requires "fs.md"
requires "json.md"
requires "config.md"
requires "plugin/krypto.md"
requires "json-utils.md"


module RPC-JSON
      imports KRYPTO
      imports FILE-SYSTEM
      imports JSON
      imports KONTROL-NODE-CONFIG
      imports SERIALIZATION
      imports JSON-UTILS

      syntax KItem ::= #loadRpcRequests( String )
                     | #saveRpcResponse( String )
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
                                | EthGetTransactionReceipt( String ) // tx hash
                                | EthGetTransactionByHash( String ) // tx hash
                                | EthGetCode( Int, Int ) // address, block number
                                | EthGetBlockByNumber( Int )
                                | EthGetBlockByHash( String )
                                | EthGetTransactionCount( Int, Int ) // address, block number
                                | EthGetStorageAt( Int, Int, Int ) // address, slot, block number
                                | AnvilStateDump()
                                | DebugTraceTransaction( String ) // tx hash
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

      rule #rpcLoadParams( "eth_getTransactionReceipt", [ TX_HASH:String ] )
            => EthGetTransactionReceipt( TX_HASH )

      rule #rpcLoadParams( "eth_getTransactionByHash", [ TX_HASH:String ] )
            => EthGetTransactionByHash( TX_HASH )

      rule #rpcLoadParams( "eth_getCode", [ ADDR:String, BLOCK_NUM:String ] )
            => #let ADDR_INT = #parseAddr( ADDR ) #in
               #let BLOCK_INT = #parseBlockNum( BLOCK_NUM ) #in
               EthGetCode( ADDR_INT, BLOCK_INT )

      rule #rpcLoadParams( "eth_getBlockByNumber", [ BLOCK_NUM:String ] )
            => #let BLOCK_INT = #parseBlockNum( BLOCK_NUM ) #in
               EthGetBlockByNumber( BLOCK_INT )

      rule #rpcLoadParams( "eth_getBlockByHash", [ BLOCK_HASH:String ] )
            => EthGetBlockByHash( BLOCK_HASH )

      rule #rpcLoadParams( "eth_getTransactionCount", [ ADDR:String, BLOCK_NUM:String ] )
            => #let ADDR_INT = #parseAddr( ADDR ) #in
               #let BLOCK_INT = #parseBlockNum( BLOCK_NUM ) #in
               EthGetTransactionCount( ADDR_INT, BLOCK_INT )

      rule #rpcLoadParams( "eth_getStorageAt", [ ADDR:String, SLOT:String, BLOCK_NUM:String ] )
            => #let ADDR_INT = #parseAddr( ADDR ) #in
               #let SLOT_INT = #parseWord( SLOT ) #in
               #let BLOCK_INT = #parseBlockNum( BLOCK_NUM ) #in
               EthGetStorageAt( ADDR_INT, SLOT_INT, BLOCK_INT )

      rule #rpcLoadParams( "anvil_stateDump", [ ] )
            => AnvilStateDump()

      rule #rpcLoadParams( "debug_traceTransaction", [ TX_HASH:String ] )
            => DebugTraceTransaction( TX_HASH )

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