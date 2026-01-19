
This module defines rules for loading JSON-RPC request data from disk.
It assumes that the input file contains a JSON array of RPCRequest objects.


```k
requires "fs.md"
requires "json.md"
requires "config.md"


module RPC-JSON
      imports FILE-SYSTEM
      imports JSON
      imports KONTROL-NODE-CONFIG

      syntax String ::= #requestsFile( String ) [function, total]

      rule #requestsFile( IO_DIR ) => IO_DIR +String "/requests.json"

      syntax KItem ::= #loadRpcRequests( String )

```

===============================================================================
Load an array of JSON RPC Requests into the corrent configuration.

```k
      syntax KItem ::= #rpcLoad( JSON )         // public
                  | #rpcLoadRequest( JSON )     // internal
                  | #rpcLoadParams( Int, JSON ) // internal
                  | #processTx( Int )           // public, this term is placed on-top of the K-cell when a TX is
                                                // fully loaded into the configuration and ready to be 
                                                // processed

      rule <k> #rpcLoad( [ .JSONs ] ) => .K ... </k>
      rule <k> #rpcLoad( [ FIRST, REST ] ) => #rpcLoadRequest( FIRST ) ~> #rpcLoad( [ REST ] ) ... </k>
        requires REST =/=K .JSONs

      rule <k> #rpcLoadRequest( { .JSONs } ) => .K ... </k>
      rule <k> #rpcLoadRequest( { PROP, REST } ) => #rpcLoadRequest(PROP) ~> #rpcLoadRequest({ REST }) ... </k>
        requires REST =/=K .JSONs

      rule <k> #rpcLoadRequest( "jsonrpc": "2.0"         ) => .K ... </k>
      rule <k> #rpcLoadRequest( "method" : "eth_sendTransaction") => .K ...</k>
      rule <k> #rpcLoadRequest( "id"     : REQ_ID:Int    ) => .K ... </k> <rpcRequestId> _ => REQ_ID </rpcRequestId>
      rule <k> #rpcLoadRequest( "params" : PARAMS:JSON   ) => mkTX !TX_ID ~> #rpcLoadParams( !TX_ID, PARAMS ) ... </k>
      <currentTxID> _ => !TX_ID </currentTxID>

      rule <k> #rpcLoadParams( TX_ID, { .JSONs } ) => #processTx(TX_ID) ... </k>
      rule <k> #rpcLoadParams( TX_ID, { FIRST, REST } ) => #rpcLoadParams( TX_ID, FIRST ) ~> #rpcLoadParams( TX_ID, REST ) ... </k>
            requires REST =/=K .JSONs

      rule <k> #rpcLoadParams( TX_ID, "from": FROM ) => .K </k>
            <message>
                  <msgID>     TX_ID          </msgID>
                  <txChainID>  _ => CHAIN_ID </txChainID>
                  <txNonce>    _ => TXNONCE  </txNonce>
                  <txType>     _ => Legacy   </txType>
                  ...
            </message>
            <origin> _ => ACCT_ID </origin>
            <chainID> CHAIN_ID </chainID>
            <account> <acctID> ACCT_ID </acctID> <nonce> TXNONCE </nonce> ... </account>
        requires ACCT_ID ==Int #parseAddr( FROM )

      rule <k> #rpcLoadParams( TX_ID, "to": TO ) => .K </k>
            <message>
                  <msgID> TX_ID </msgID>
                  <txGasLimit> _ => #parseAddr( TO ) </txGasLimit>
                  ...
            </message>
            
      rule <k> #rpcLoadParams( TX_ID, "gas": GAS_LIMIT ) => .K </k>
            <message>
                  <msgID> TX_ID </msgID>
                  <txGasLimit> _ => #parseWord( GAS_LIMIT ) </txGasLimit>
                  ...
            </message>

      rule <k> #rpcLoadParams( TX_ID, "gasPrice": GAS_PRICE ) => .K </k>
            <message>
                  <msgID> TX_ID </msgID>
                  <txGasPrice> _ => #parseWord( GAS_PRICE ) </txGasPrice>
                  ...
            </message>
      rule <k> #rpcLoadParams( TX_ID, "value": VALUE ) => .K </k>
            <message>
                  <msgID> TX_ID </msgID>
                  <value> _ => #parseWord( VALUE ) </value>
                  ...
            </message>

      rule <k> #rpcLoadParams( TX_ID, "data": DATA ) => .K </k>
            <message>
                  <msgID> TX_ID </msgID>
                  <data> _ => #parseByteStack( DATA ) </data>
                  ...
            </message>
```

===============================================================================
Loading RPCRequests from Disk

This secion defines rules to read a RPCRequests from disk.

```k

      rule <k> #loadRpcRequests( IO_DIR )
            => #let CONTENTS:IOString = #readFile( #requestsFile( IO_DIR ) )
                  #in #rpcLoad( String2JSON( {CONTENTS}:>String ) )
                  ...
            </k>


endmodule
```