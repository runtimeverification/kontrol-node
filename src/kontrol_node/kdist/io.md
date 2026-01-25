```k

requires "node.md"
requires "fs.md"
requires "config.md"
requires "evm.md"

module KONTROL-IO
    imports EVM
    imports KONTROL-NODE-CONFIG
    imports KONTROL-NODE
    imports FILE-SYSTEM

    configuration <simbolikVM />
        <in stream="stdin">   .List     </in>
        <out stream="stdout"> .List     </out>
        <ioDir>               "":String </ioDir>

    syntax EthereumSimulation ::= Start

    syntax Start ::= #start( String ) [symbol(start)]

    rule <k> #start( IO_DIR )
        => #unlockAccounts()
        ~> #loadStateDump( IO_DIR, 0)
        ~> #enterRequestLoop()
        ...
    </k>
    <ioDir> _ => IO_DIR </ioDir>
```
===============================================================================
Event Loop for Processing RPC Requests

```k
    syntax KItem ::= #enterRequestLoop()
                   | #checkMessage( String )


    rule <k> #enterRequestLoop()
        => #checkMessage( REQUEST )
        ~> #loadRpcRequest( IO_DIR )
        ~> #enterRequestLoop()
        ...
        </k>
        <ioDir> IO_DIR </ioDir>
        <in> ListItem( REQUEST:String ) => .List ... </in>

    rule <k> #checkMessage( "RequestReady" ) => .K ... </k>
```

===============================================================================
Sending RPC Responses

This section defines rules to write RPCResponses to stdout.

```k

      syntax KItem ::= #notify( String )

      syntax String ::= responseFile( String ) [function]
      rule responseFile( IO_DIR:String ) =>
            IO_DIR +String "/response.json"

      rule <k> RPCResponse( JSON_RESPONSE )
            => #writeFile(responseFile(IO_DIR), JSON2String({
                  "jsonrpc" : "2.0",
                  "id"      : REQ_ID,
                  "result"  : JSON_RESPONSE
            }))
            ~> #notify("ResponseReady")
            ... </k>
            <ioDir> IO_DIR </ioDir>
            <rpcRequestID> REQ_ID </rpcRequestID>
            
      rule <k> #notify( MESSAGE ) => .K ... </k>      
           <out> ... .List => ListItem( MESSAGE ) </out>

      rule <k> RPCRawResponse( RESPONSE:String )
            => #writeFile(responseFile(IO_DIR), RESPONSE)
            ~> #notify( "ResponseReady" )
            ...
           </k>
           <ioDir> IO_DIR </ioDir>

```

===============================================================================
Loading RPCRequests

This section defines rules to read a RPCRequests from a string.

```k
    syntax KItem ::= #loadRpcRequest( String )
    
    syntax String ::= requestFile( String ) [function]
    rule requestFile( IO_DIR:String ) =>
        IO_DIR +String "/request.json"

    rule <k> #loadRpcRequest( IO_DIR:String )
        => #let CONTENTS:IOString = #readFile( requestFile(IO_DIR) )
            #in #rpcLoad( String2JSON( {CONTENTS}:>String ) )
        ...
        </k>

```
===============================================================================
Persisting a StateDump to Disk

This seciont defines rules to write a StateDump JSON object to disk.

```k

    syntax KItem ::= #writeStateDump( String )
                   | #saveStateDump( String )

    syntax String ::= #stateDumpFile(
        String, // IO dir
        Int     // block number
    ) [function, total]

    rule #stateDumpFile( IO_DIR, BLOCK_NUMBER ) => IO_DIR +String "/blocks/block_" +String Int2String( BLOCK_NUMBER ) +String ".json"

    rule <k> #saveStateDump( IO_DIR )
          => #createStateDump()
          ~> #writeStateDump( IO_DIR )
        </k>

    rule <k> #StateDump( SD )
          ~> #writeStateDump( IO_DIR )
          => #writeFile( #stateDumpFile( IO_DIR, BLOCK_NUMBER), JSON2String( SD ) )
          ...
        </k>
        <number> BLOCK_NUMBER </number>

```
===============================================================================
Loading StateDump from Disk

This secion defines rules to read a StateDump JSON object from disk.

```k

    syntax KItem ::= #loadStateDump( String, Int )
    rule <k> #loadStateDump( IO_DIR, BLOCK_NUMBER )
          => #let CONTENTS:IOString = #readFile( #stateDumpFile( IO_DIR, BLOCK_NUMBER ) )
              #in #stLoad( String2JSON( {CONTENTS}:>String ) )
              ...
         </k>

endmodule
```