# JSON encoding of debug traces

```k
requires "foundry.md"
requires "driver.md"
requires "trace.md"
requires "fs.md"
requires "config.md"
requires "json-utils.md"

module TRACE-JSON
    imports JSON-UTILS
    imports EVM
    imports FOUNDRY
    imports EVM-TRACING
    imports JSON
    imports K-IO
    imports FILE-SYSTEM
    imports KONTROL-NODE-CONFIG

    syntax JSON ::= traceItemToJson(TraceItem)           [function, total, symbol(traceItemToJson)]
                  | opcodeToJson(OpCode)                 [function, total, symbol(opcodeToJson)]
                  | wordstackToJson(WordStack)           [function, total, symbol(wordstackToJson)]
                  | memoryToJson(DataChange)             [function, total, symbol(memoryToJson)]
                  | bytesToJson(Bytes)                   [function, total, symbol(bytesToJson)]
                  | intMapToJson(Map)                    [function, total, symbol(intMapToJson)]
                  | bytesMapToJson(Map)                  [function, total, symbol(bytesMapToJson)]
                  | storageMapToJson(Map)                [function, total, symbol(storageMapToJson)]
                  | accountToJson(Account)               [function, total, symbol(accountToJson)]
                  | statusToJson(StatusCode)             [function, total, symbol(statusToJson)]
                  | dataChangeToJson(DataChange)         [function, total, symbol(dataChangeToJson)]
 // ------------------------------------------------------------------------------------------------
    syntax JSONs ::= wordstackToJsons(WordStack, JSONs)  [function, total, symbol(wordstackToJsons)]
                  | memoryToJsons(Bytes, JSONs)          [function, total, symbol(memoryToJsons)]
                  | intMapToJsons(Map)                   [function, total, symbol(intMapToJsons)]
                  | bytesMapToJsons(Map)                 [function, total, symbol(bytesMapToJsons)]
                  | storageMapToJsons(Map)               [function, total, symbol(storageMapToJsons)]
 // -------------------------------------------------------------------------------------------------


    rule opcodeToJson( STOP ) => "STOP"
    rule opcodeToJson( ADD ) => "ADD"
    rule opcodeToJson( MUL ) => "MUL"
    rule opcodeToJson( SUB ) => "SUB"
    rule opcodeToJson( DIV ) => "DIV"
    rule opcodeToJson( SDIV ) => "SDIV"
    rule opcodeToJson( MOD ) => "MOD"
    rule opcodeToJson( SMOD ) => "SMOD"
    rule opcodeToJson( ADDMOD ) => "ADDMOD"
    rule opcodeToJson( MULMOD ) => "MULMOD"
    rule opcodeToJson( EXP ) => "EXP"
    rule opcodeToJson( SIGNEXTEND ) => "SIGNEXTEND"
    rule opcodeToJson( LT ) => "LT"
    rule opcodeToJson( GT ) => "GT"
    rule opcodeToJson( SLT ) => "SLT"
    rule opcodeToJson( SGT ) => "SGT"
    rule opcodeToJson( EQ ) => "EQ"
    rule opcodeToJson( ISZERO ) => "ISZERO"
    rule opcodeToJson( AND ) => "AND"
    rule opcodeToJson( EVMOR ) => "EVMOR"
    rule opcodeToJson( XOR ) => "XOR"
    rule opcodeToJson( NOT ) => "NOT"
    rule opcodeToJson( BYTE ) => "BYTE"
    rule opcodeToJson( SHL ) => "SHL"
    rule opcodeToJson( SHR ) => "SHR"
    rule opcodeToJson( SAR ) => "SAR"
    rule opcodeToJson( SHA3 ) => "SHA3"
    rule opcodeToJson( ADDRESS ) => "ADDRESS"
    rule opcodeToJson( BALANCE ) => "BALANCE"
    rule opcodeToJson( ORIGIN ) => "ORIGIN"
    rule opcodeToJson( CALLER ) => "CALLER"
    rule opcodeToJson( CALLVALUE ) => "CALLVALUE"
    rule opcodeToJson( CALLDATALOAD ) => "CALLDATALOAD"
    rule opcodeToJson( CALLDATASIZE ) => "CALLDATASIZE"
    rule opcodeToJson( CALLDATACOPY ) => "CALLDATACOPY"
    rule opcodeToJson( CODESIZE ) => "CODESIZE"
    rule opcodeToJson( CODECOPY ) => "CODECOPY"
    rule opcodeToJson( GASPRICE ) => "GASPRICE"
    rule opcodeToJson( EXTCODESIZE ) => "EXTCODESIZE"
    rule opcodeToJson( EXTCODECOPY ) => "EXTCODECOPY"
    rule opcodeToJson( RETURNDATASIZE ) => "RETURNDATASIZE"
    rule opcodeToJson( RETURNDATACOPY ) => "RETURNDATACOPY"
    rule opcodeToJson( EXTCODEHASH ) => "EXTCODEHASH"
    rule opcodeToJson( BLOCKHASH ) => "BLOCKHASH"
    rule opcodeToJson( COINBASE ) => "COINBASE"
    rule opcodeToJson( TIMESTAMP ) => "TIMESTAMP"
    rule opcodeToJson( NUMBER ) => "NUMBER"
    rule opcodeToJson( PREVRANDAO ) => "PREVRANDAO"
    rule opcodeToJson( DIFFICULTY ) => "DIFFICULTY"
    rule opcodeToJson( GASLIMIT ) => "GASLIMIT"
    rule opcodeToJson( CHAINID ) => "CHAINID"
    rule opcodeToJson( SELFBALANCE ) => "SELFBALANCE"
    rule opcodeToJson( BASEFEE ) => "BASEFEE"
    rule opcodeToJson( BLOBHASH ) => "BLOBHASH"
    rule opcodeToJson( BLOBBASEFEE ) => "BLOBBASEFEE"
    rule opcodeToJson( POP ) => "POP"
    rule opcodeToJson( MLOAD ) => "MLOAD"
    rule opcodeToJson( MSTORE ) => "MSTORE"
    rule opcodeToJson( MSTORE8 ) => "MSTORE8"
    rule opcodeToJson( SLOAD ) => "SLOAD"
    rule opcodeToJson( SSTORE ) => "SSTORE"
    rule opcodeToJson( JUMP ) => "JUMP"
    rule opcodeToJson( JUMPI ) => "JUMPI"
    rule opcodeToJson( PC ) => "PC"
    rule opcodeToJson( MSIZE ) => "MSIZE"
    rule opcodeToJson( GAS ) => "GAS"
    rule opcodeToJson( JUMPDEST ) => "JUMPDEST"
    rule opcodeToJson( TLOAD ) => "TLOAD"
    rule opcodeToJson( TSTORE ) => "TSTORE"
    rule opcodeToJson( MCOPY ) => "MCOPY"
    rule opcodeToJson( PUSHZERO ) => "PUSHZERO"
    rule opcodeToJson( PUSH(1) ) => "PUSH1"
    rule opcodeToJson( PUSH(2) ) => "PUSH2"
    rule opcodeToJson( PUSH(3) ) => "PUSH3"
    rule opcodeToJson( PUSH(4) ) => "PUSH4"
    rule opcodeToJson( PUSH(5) ) => "PUSH5"
    rule opcodeToJson( PUSH(6) ) => "PUSH6"
    rule opcodeToJson( PUSH(7) ) => "PUSH7"
    rule opcodeToJson( PUSH(8) ) => "PUSH8"
    rule opcodeToJson( PUSH(9) ) => "PUSH9"
    rule opcodeToJson( PUSH(10) ) => "PUSH10"
    rule opcodeToJson( PUSH(11) ) => "PUSH11"
    rule opcodeToJson( PUSH(12) ) => "PUSH12"
    rule opcodeToJson( PUSH(13) ) => "PUSH13"
    rule opcodeToJson( PUSH(14) ) => "PUSH14"
    rule opcodeToJson( PUSH(15) ) => "PUSH15"
    rule opcodeToJson( PUSH(16) ) => "PUSH16"
    rule opcodeToJson( PUSH(17) ) => "PUSH17"
    rule opcodeToJson( PUSH(18) ) => "PUSH18"
    rule opcodeToJson( PUSH(19) ) => "PUSH19"
    rule opcodeToJson( PUSH(20) ) => "PUSH20"
    rule opcodeToJson( PUSH(21) ) => "PUSH21"
    rule opcodeToJson( PUSH(22) ) => "PUSH22"
    rule opcodeToJson( PUSH(23) ) => "PUSH23"
    rule opcodeToJson( PUSH(24) ) => "PUSH24"
    rule opcodeToJson( PUSH(25) ) => "PUSH25"
    rule opcodeToJson( PUSH(26) ) => "PUSH26"
    rule opcodeToJson( PUSH(27) ) => "PUSH27"
    rule opcodeToJson( PUSH(28) ) => "PUSH28"
    rule opcodeToJson( PUSH(29) ) => "PUSH29"
    rule opcodeToJson( PUSH(30) ) => "PUSH30"
    rule opcodeToJson( PUSH(31) ) => "PUSH31"
    rule opcodeToJson( PUSH(32) ) => "PUSH32"
    rule opcodeToJson( DUP(1) ) => "DUP1"
    rule opcodeToJson( DUP(2) ) => "DUP2"
    rule opcodeToJson( DUP(3) ) => "DUP3"
    rule opcodeToJson( DUP(4) ) => "DUP4"
    rule opcodeToJson( DUP(5) ) => "DUP5"
    rule opcodeToJson( DUP(6) ) => "DUP6"
    rule opcodeToJson( DUP(7) ) => "DUP7"
    rule opcodeToJson( DUP(8) ) => "DUP8"
    rule opcodeToJson( DUP(9) ) => "DUP9"
    rule opcodeToJson( DUP(10) ) => "DUP10"
    rule opcodeToJson( DUP(11) ) => "DUP11"
    rule opcodeToJson( DUP(12) ) => "DUP12"
    rule opcodeToJson( DUP(13) ) => "DUP13"
    rule opcodeToJson( DUP(14) ) => "DUP14"
    rule opcodeToJson( DUP(15) ) => "DUP15"
    rule opcodeToJson( DUP(16) ) => "DUP16"
    rule opcodeToJson( SWAP(1) ) => "SWAP1"
    rule opcodeToJson( SWAP(2) ) => "SWAP2"
    rule opcodeToJson( SWAP(3) ) => "SWAP3"
    rule opcodeToJson( SWAP(4) ) => "SWAP4"
    rule opcodeToJson( SWAP(5) ) => "SWAP5"
    rule opcodeToJson( SWAP(6) ) => "SWAP6"
    rule opcodeToJson( SWAP(7) ) => "SWAP7"
    rule opcodeToJson( SWAP(8) ) => "SWAP8"
    rule opcodeToJson( SWAP(9) ) => "SWAP9"
    rule opcodeToJson( SWAP(10) ) => "SWAP10"
    rule opcodeToJson( SWAP(11) ) => "SWAP11"
    rule opcodeToJson( SWAP(12) ) => "SWAP12"
    rule opcodeToJson( SWAP(13) ) => "SWAP13"
    rule opcodeToJson( SWAP(14) ) => "SWAP14"
    rule opcodeToJson( SWAP(15) ) => "SWAP15"
    rule opcodeToJson( SWAP(16) ) => "SWAP16"
    rule opcodeToJson( LOG(0) ) => "LOG0"
    rule opcodeToJson( LOG(1) ) => "LOG1"
    rule opcodeToJson( LOG(2) ) => "LOG2"
    rule opcodeToJson( LOG(3) ) => "LOG3"
    rule opcodeToJson( LOG(4) ) => "LOG4"
    rule opcodeToJson( CREATE ) => "CREATE"
    rule opcodeToJson( CALL ) => "CALL"
    rule opcodeToJson( CALLCODE ) => "CALLCODE"
    rule opcodeToJson( RETURN ) => "RETURN"
    rule opcodeToJson( DELEGATECALL ) => "DELEGATECALL"
    rule opcodeToJson( CREATE2 ) => "CREATE2"
    rule opcodeToJson( STATICCALL ) => "STATICCALL"
    rule opcodeToJson( REVERT ) => "REVERT"
    rule opcodeToJson( INVALID ) => "INVALID"
    rule opcodeToJson( SELFDESTRUCT ) => "SELFDESTRUCT"
    rule opcodeToJson( _ ) => "UNDEFINED" [owise]

    rule wordstackToJson( WS ) => [ wordstackToJsons( WS, .JSONs ) ] [priority(50)]
    rule wordstackToJsons( .WordStack, ACC ) => ACC
    rule wordstackToJsons( W:WS, ACC ) => wordstackToJsons(WS, (intToHex( W ), ACC) )

    rule intMapToJson( M:Map ) => { intMapToJsons(M) }
    rule intMapToJsons( .Map) => .JSONs
    rule intMapToJsons( (ACC:Int |-> VAL:Int) REST:Map ) => intToHex( ACC) : intToHex( VAL ), intMapToJsons( REST )
    
    rule bytesMapToJson( M:Map ) => { bytesMapToJsons( M ) }
    rule bytesMapToJsons( .Map) => .JSONs
    rule bytesMapToJsons( (ACC:Int |-> VAL:Bytes) REST:Map ) => intToHex( ACC) : bytesToJson( VAL ), bytesMapToJsons( REST )

    rule storageMapToJson( M:Map ) => { storageMapToJsons(M ) }
    rule storageMapToJsons( .Map ) => .JSONs
    rule storageMapToJsons( (ACC:Int |-> CONTRACT_STORAGE:Map) REST:Map ) => intToHex( ACC ) : intMapToJson( CONTRACT_STORAGE), storageMapToJsons( REST )

    // split memory into 32 bytes chunks

    syntax JSONs ::= prepend( JSON, JSONs ) [function, total]
    rule prepend( X, XS ) => X, XS

    rule memoryToJson(.DataChange) => null
    rule memoryToJson( MEM:Bytes )      => [ .JSONs ]
      requires lengthBytes(MEM) ==Int 0

    rule memoryToJson(MEM:Bytes)
      => [ memoryToJsons(MEM, maxInt(0, ((lengthBytes(MEM) -Int 1) /Int 32) *Int 32), .JSONs) ]
      requires lengthBytes(MEM) >Int 0

    rule memoryToJsons(MEM, OFFSET, ACC)
      => memoryToJsons(
          MEM,
          OFFSET -Int 32,
          prepend(
            Bytes2Hex(
              padRightBytes(
                substrBytes(MEM, OFFSET, minInt(OFFSET +Int 32, lengthBytes(MEM))),
                32,
                0
              )
            ),
            ACC
          )
        )
      requires OFFSET >=Int 32

    rule memoryToJsons(MEM, OFFSET, ACC)
      => Bytes2Hex(
          padRightBytes(
            substrBytes(MEM, OFFSET, minInt(OFFSET +Int 32, lengthBytes(MEM))),
            32,
            0
          )
        ) , ACC
      [owise]

    rule accountToJson( .Account ) => null
    rule accountToJson( ACC ) => ACC [owise]

    rule statusToJson( STATUS ) => StatusCode2String( STATUS )

    rule dataChangeToJson( .DataChange ) => null
    rule dataChangeToJson( BYTES ) => bytesToJson( BYTES) [owise]

    rule traceItemToJson (
      { VAR_PC
      | VAR_OPCODE
      | VAR_WORDSTACK
      | VAR_MEMORY
      | VAR_STORAGE_CHANGES
      | VAR_NONCE_CHANGES
      | VAR_BALANCE_CHANGES
      | VAR_CALLDATA_CHANGE
      | VAR_RETURNDATA_CHANGE
      | VAR_PROGRAM_CHANGE
      | VAR_CODE_CHANGE
      | VAR_INIT_CODE_CHANGE
      | VAR_CALL_DEPTH
      | VAR_GAS_LEFT
      | VAR_COINBASE
      | VAR_GAS_PRICE
      | VAR_DIFFICULTY
      | VAR_BLOCK_NUMBER
      | VAR_TIMESTAMP
      | VAR_TARGET_ADDRESS
      | VAR_CODE_ADDRESS
      | VAR_MESSAGE_SENDER
      | VAR_MESSAGE_VALUE
      | VAR_TX_ORIGIN
      | VAR_IS_INIT_CODE
      | VAR_STATUS_CODE
      } ) => {
        "pc": VAR_PC,
        "op": opcodeToJson( VAR_OPCODE ),
        "stack": wordstackToJson( VAR_WORDSTACK ),
        "memoryChange": memoryToJson( VAR_MEMORY ),
        "storageChanges": storageMapToJson( VAR_STORAGE_CHANGES ),
        "nonceChanges": intMapToJson( VAR_NONCE_CHANGES ),
        "balanceChanges": intMapToJson( VAR_BALANCE_CHANGES),
        "callDataChange": dataChangeToJson( VAR_CALLDATA_CHANGE),
        "returnDataChange": dataChangeToJson( VAR_RETURNDATA_CHANGE),
        "programChange": dataChangeToJson( VAR_PROGRAM_CHANGE),
        "deployedCodeChanges": bytesMapToJson( VAR_CODE_CHANGE),
        "initCodeChanges": bytesMapToJson( VAR_INIT_CODE_CHANGE),
        "depth": VAR_CALL_DEPTH +Int 1,
        "gas": VAR_GAS_LEFT,
        "coinbase": accountToJson( VAR_COINBASE ),
        "gasCost": VAR_GAS_PRICE,
        "difficulty": VAR_DIFFICULTY,
        "blockNumber": VAR_BLOCK_NUMBER,
        "blockTimestamp": VAR_TIMESTAMP,
        "targetAddress": accountToJson( VAR_TARGET_ADDRESS ),
        "codeAddress": accountToJson( VAR_CODE_ADDRESS),
        "msgSender": accountToJson( VAR_MESSAGE_SENDER ),
        "msgValue": VAR_MESSAGE_VALUE,
        "txOrigin": accountToJson( VAR_TX_ORIGIN ),
        "isInitCode": VAR_IS_INIT_CODE,
        "statusCode": statusToJson( VAR_STATUS_CODE )
      }

    // IO

    rule <k> #execute ... </k>
         <recordedTrace> true => false </recordedTrace>
      [priority(25)]

    syntax KItem ::= "#storeTraceItem" TraceItem

    rule <k> (.K => #storeTraceItem { PCOUNT
                                    | OPC
                                    | WS
                                    | MEM
                                    | STORCH
                                    | NONCECH
                                    | BALCH
                                    | CADA
                                    | REDA
                                    | #if PROGCHANGED ==K true #then PROG #else .DataChange #fi
                                    | DEPLCODECH
                                    | INITCODECH
                                    | CD
                                    | GA
                                    | COINB
                                    | GASPR
                                    | DIFF
                                    | NUM
                                    | TIMEST
                                    | ACCT
                                    | CODEADDR
                                    | SENDER
                                    | MSGVAL
                                    | TXORIG
                                    | ISINIT
                                    | STATUS
                                    })
             ~> #next [ OPC ] ...
         </k>
         <activeTracing>                true                   </activeTracing>
         <recordedTrace>                false       => true    </recordedTrace>
         <recordedMkCallCreate>         _           => false   </recordedMkCallCreate>
         <recordedCreate>               _           => false   </recordedCreate>
         <localMemoryChanged>           _           => false   </localMemoryChanged>
         <currentNonceMutations>        NONCECH     => .Map    </currentNonceMutations>          
         <contextSwitch>                _           => false   </contextSwitch>
         <currentBalanceMutations>      BALCH       => .Map    </currentBalanceMutations>          
         <currentStorageMutations>      STORCH      => .Map    </currentStorageMutations>
         <programChanged>               PROGCHANGED => false   </programChanged>
         <currentDeployedCodeMutations> DEPLCODECH  => .Map    </currentDeployedCodeMutations>
         <currentInitCodeMutations>     INITCODECH  => .Map    </currentInitCodeMutations>
         <callData>                     CADA                   </callData>
         <output>                       REDA                   </output>
         <pc>                           PCOUNT                 </pc>
         <wordStack>                    WS                     </wordStack>
         <callDepth>                    CD                     </callDepth>
         <localMem>                     MEM                    </localMem>
         <program>                      PROG                   </program>
         <id>                           ACCT                   </id>
         <codeAddr>                     CODEADDR               </codeAddr>
         <gas>                          GA                     </gas>
         <coinbase>                     COINB                  </coinbase>
         <gasPrice>                     GASPR                  </gasPrice>
         <difficulty>                   DIFF                   </difficulty>
         <number>                       NUM                    </number>
         <timestamp>                    TIMEST                 </timestamp>
         <caller>                       SENDER                 </caller>
         <callValue>                    MSGVAL                 </callValue>
         <origin>                       TXORIG                 </origin>
         <isInitCode>                   ISINIT                 </isInitCode>
         <statusCode>                   STATUS                 </statusCode>
      [priority(24)]

    syntax String ::= #traceFile( String, Int ) [function, total]

    rule #traceFile( IO_DIR, MSG_ID ) => IO_DIR +String "/transactions/trace_" +String Int2String( MSG_ID ) +String ".json"

    rule <k> #storeTraceItem TRITEM
          => #appendFile(
                #traceFile( IO_DIR, MSG_ID ),
                JSON2String( traceItemToJson( TRITEM ) ) +String "\n"
             ) ...
         </k>
         <ioDir> IO_DIR </ioDir>
         <msgID> MSG_ID </msgID>

endmodule
```