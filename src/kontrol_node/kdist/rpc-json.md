
This module defines rules for loading JSON-RPC request data from disk.
It assumes that the input file contains a JSON array of RPCRequest objects.


````k
module RPC-JSON

syntax KItem ::= RPCCommand

syntax String ::= #requestFile( STRING ) [function, total]

rule #requestFile( IO_DIR ) => IO_DIR +String "/requests.json"

syntax RPCCommand ::= #loadRpcRequestsFile()
                    | #openRpcRequestsFile()
                    | #storeRpcRequestsFileDescriptor()
                    | #parseFile()
                    | #RPCRequests( JSON )

rule <k> #loadRpcRequestsFile()
      => #openRpcRequestsFile()
      ~> #parseFile() ...
     </k>

rule <k> #openRpcRequestsFile()
      => open( #requestFile( IO_DIR) , "r" )
      ~> #storeRpcRequestsFileDescriptor()
      </k>
      <ioDir> IO_DIR </ioDir>

rule <k> FILE:FileDescriptor
      ~> storeRpcRequestsFileDescriptor() ...
     </k>
     <rpcRequestsFileDescriptor> FILE </rpcRequestsFileDescriptor>

rule <k> #parseFile()
      => #RPCRequests( String2JSON( #read( FILE, 0 ) ) ) ...
     <k>
     <rpcRequestsFileDescriptor> FILE </rpcRequestsFileDescriptor>


endmodule

```