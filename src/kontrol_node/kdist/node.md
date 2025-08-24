```k
requires "foundry.md"
requires "driver.md"
requires "no_code_size_checks.md"

module KONTROL-NODE
    imports FOUNDRY
    imports ETHEREUM-SIMULATION
    imports NO-CODE-SIZE-CHECKS
    imports JSON
    imports K-IO
    imports K-REFLECTION

    syntax RPCRequest ::= ".RPCRequest" [symbol(EmptyRPCRequest)]
 // -------------------------------------------------------------

    syntax RPCResponse ::= String | Int
                         | ".RPCResponse" [symbol(EmptyRPCResponse)]
 // ----------------------------------------------------------------

    syntax MapMutation ::= "{" Int "|" Int "|" Int "}" [symbol(node_doubleMapMutation)]
                         | "{" Int "|" Int "}"         [symbol(node_mapMutation)]
 // ----------------------------------------------------------------

    configuration <simbolikVM>
                    <foundry/>
                    <rpcResponse> .RPCResponse </rpcResponse>
                    <accountKeys> .Map </accountKeys>
                    <timeFreeze> true </timeFreeze>
                    <timeDiff> 0 </timeDiff>
                    <currentTxID> 0 </currentTxID>
                    <currentBlockHash> 0 </currentBlockHash>
                    <txReceipts>
                      <txReceipt multiplicity ="*" type="Map">
                        <txHash>          "":String  </txHash>
                        <txCumulativeGas> 0          </txCumulativeGas>
                        <logSet>          .List      </logSet>
                        <bloomFilter>     .Bytes     </bloomFilter>
                        <txStatus>        0          </txStatus>
                        <txID>            0          </txID>
                        <sender>          .Account   </sender>
                        <txBlockNumber>   0          </txBlockNumber>
                        <contractAddress> .Account   </contractAddress>
                      </txReceipt>
                    </txReceipts>
                    <traceLogsFileDescriptor> .FileDescr </traceLogsFileDescriptor>
                    <traceLogsFilePath> "":String </traceLogsFilePath>
                    <writeTraceLogsToFile> false </writeTraceLogsToFile>
                  </simbolikVM>
                  <KEVMTracing2>
                    <currentNonceMutations>   .List </currentNonceMutations>          
                    <traceNonce>              false </traceNonce>
                    <currentBalanceMutations> .List </currentBalanceMutations>          
                    <traceBalance>            false </traceBalance>
                    <currentStorageMutations> .List </currentStorageMutations>
                  </KEVMTracing2>
```

  Transaction debugging
  ---------------------
  Once debug_traceTransaction get up and running in a PR, these changes below should be moved to Kontrol:trace.md.

```k
    syntax TraceItem ::= "{" 
          Int        // program counter 
      "|" OpCode     // opcode
      "|" WordStack  // stack
      "|" Bytes      // memory
      "|" List       // storage changes <- CHANGED
      "|" List       // nonce changes <- NEW
      "|" List       // balance changes <- NEW
      "|" Int        // call depth
      "|" Int        // gas
      "|" Account    // coinbase
      "|" Int        // gas price
      "|" Int        // difficulty
      "|" Int        // block number
      "|" Int        // block timestamp
      "|" Account    // target address
      "|" Account    // message sender
      "|" Int        // message value
      "|" Account    // transaction origin
      "|" StatusCode // status
    "}" [symbol(traceItem)]
```

JSON encoding of debug traces

```k
    syntax JSON ::= traceToJson(List)               [function, symbol(traceToJson)]
                  | traceItemToJson(TraceItem)      [function, symbol(traceItemToJson)]
                  | opcodeToJson(OpCode)            [function, symbol(opcodeToJson)]
                  | wordstackToJson(WordStack)      [function, symbol(wordstackToJson)]
                  | bytesToJson(Bytes)              [function, symbol(bytesToJson)]
                  | mapMutationToJson(MapMutation)  [function, symbol(mapMutationToJson)]
                  | mapMutationsToJson(List)        [function, symbol(mapMutationsToJson)]
                  | accountToJson(Account)          [function, symbol(accountToJson)]
                  | statusToJson(StatusCode)        [function, symbol(statusToJson)]
    syntax JSONs ::= wordstackToJsons(WordStack)    [function, symbol(wordstackToJsons)]

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
    rule opcodeToJson( W ) => "INVALID" [owise]

    rule wordstackToJson( WS ) => [ wordstackToJsons( WS ) ]
    rule wordstackToJsons( .WordStack ) => .List
    rule wordstackToJsons( W:WS ) => W,WS

    rule bytesToJson( BYTES ) => Bytes2String( BYTES ) 

    rule mapMutationToJson( { A | B | C } ) => [ A, B, C]
    rule mapMutationToJson( { A | B } ) => [A, B]

    rule mapMutationsToJson( .List ) => .List
    rule mapMutationsToJson( UPDATE:REST ) => ListItem( mapMutationToJson( UPDATE ) ) mapMutationsToJson( REST )

    rule accountToJson( .Account ) => null
    rule accountToJson( ID ) => ID

    rule statusToJson( STATUS ) => StatusCode2String( STATUS )

    rule traceItemToJson (
      { PC
      | OPCODE
      | WORDSTACK
      | MEMORY
      | STORAGE_CHANGES
      | NONCE_CHANGES
      | BALANCE_CHANGES
      | CALL_DEPTH
      | GAS_LEFT
      | COINBASE
      | GAS_PRICE
      | DIFFICULTY
      | BLOCK_NUMBER
      | TIMESTAMP
      | TARGET_ADDRESS
      | MESSAGE_SENDER
      | MESSAGE_VALUE
      | TX_ORIGIN
      | STATUS_CODE
      } ) => {
        "pc": PC,
        "opcode": opcodeToJson( OPCODE ),
        "stack": wordstackToJson( WORDSTACK ),
        "memory": bytestoJson( MEMORY ),
        "storage": mapMutationsToJson( STORAGE_CHANGES ),
        "nonce_changes": mapMutationsToJson( NONCE_CHANGES ),
        "balance_changes": mapMutationsToJson( BALANCE_CHANGES),
        "call_depth": CALL_DEPTH,
        "gas_left": GAS_LEFT,
        "coinbase": accountToJson( COINBASE ),
        "gasprice": GAS_PRICE,
        "difficulty": DIFFICULTY,
        "blocknumber": BLOCK_NUMBER,
        "timestamp": TIMESTAMP,
        "target_address": accountToJson( TARGET_ADDRESS ),
        "msg_sender": accountToJson( MESSAGE_SENDER ),
        "msg_value": MESSAGE_VALUE,
        "tx_origin": accountToJson( TX_ORIGIN ),
        "status_code": statusToJson( STATUS_CODE )
      }

    rule traceToJson( .List ) => []
    rule traceToJson( TI:REST ) => ListItem( traceItemToJson( TI ) ) traceToJson( REST )
```

Writing traces to a file.

```k
    syntax KItem ::= "#storeTraceItem" TraceItem
    rule <k> (.K => #storeTraceItem { PCOUNT
                                    | OPC
                                    | #if DSTK ==K true #then WS      #else .WordStack #fi
                                    | #if DMEM ==K true #then MEM     #else .Bytes     #fi
                                    | STORCH
                                    | NONCECH
                                    | BALCH
                                    | CD
                                    | GA
                                    | COINB
                                    | GASPR
                                    | DIFF
                                    | NUM
                                    | TIMEST
                                    | ACCT
                                    | SENDER
                                    | MSGVAL
                                    | TXORIG
                                    | STATUS
                                    })
             ~> #next [ OPC ] ...
         </k>
         <activeTracing>           true             </activeTracing>
         <traceWordStack>          DSTK             </traceWordStack>
         <traceMemory>             DMEM             </traceMemory>
         <recordedTrace>           false => true    </recordedTrace>
         <currentNonceMutations>   NONCECH => .List </currentNonceMutations>          
         <currentBalanceMutations> BALCH => .List   </currentBalanceMutations>          
         <currentStorageMutations> STORCH => .List  </currentStorageMutations>
         <pc>                      PCOUNT           </pc>
         <wordStack>               WS               </wordStack>
         <callDepth>               CD               </callDepth>
         <localMem>                MEM              </localMem>
         <id>                      ACCT             </id>
         <gas>                     GA               </gas>
         <coinbase>                COINB            </coinbase>
         <gasPrice>                GASPR            </gasPrice>
         <difficulty>              DIFF             </difficulty>
         <number>                  NUM              </number>
         <timestamp>               TIMEST           </timestamp>
         <caller>                  SENDER           </caller>
         <callValue>               MSGVAL           </callValue>
         <origin>                  TXORIG           </origin>
         <statusCode>              STATUS           </statusCode>
      [priority(24)]

    rule <k> #storeTraceItem TRITEM => .K ... </k>
         <writeTraceLogsToFile> false </writeTraceLogsToFile>
         <traceData>
           ...
           .List => ListItem(TRITEM)
         </traceData>

    rule <k> #storeTraceItem TRITEM => #write (TRFILEDESCR, 
               JSON2String( traceToJson( TRITEM) ) +String "\n"
             ) ... </k>
         <writeTraceLogsToFile>    true        </writeTraceLogsToFile>
         <traceLogsFileDescriptor> TRFILEDESCR </traceLogsFileDescriptor>
      requires TRFILEDESCR =/=K .FileDescr

 // ---------------------------------------------------------------------------------------------------------------

syntax KItem ::= "#openTraceLogsFile"  [symbol(openTraceLogsFile)]
               | "#closeTraceLogsFile" [symbol(closeTraceLogsFile)]
               | "#storeTraceLogsFileDescriptor" [symbol(storeTraceLogsFileDescriptor)]

syntax FILEDESCR ::= Int
                   | ".FileDescr"

rule <k> #openTraceLogsFile => #open(TRFILEPATH, "w") ~> #storeTraceLogsFileDescriptor ... </k>
     <traceLogsFilePath>       TRFILEPATH                  </traceLogsFilePath>
     <writeTraceLogsToFile> true </writeTraceLogsToFile>

rule <k> #openTraceLogsFile => .K ... </k>
     <writeTraceLogsToFile> false </writeTraceLogsToFile>

rule <k> TRFILEDESCR ~> #storeTraceLogsFileDescriptor => .K ... </k>
     <traceLogsFileDescriptor> _ => TRFILEDESCR </traceLogsFileDescriptor>

rule <k> #closeTraceLogsFile => #close(TRFILEDESCR) ... </k>
     <traceLogsFileDescriptor> TRFILEDESCR => .FileDescr </traceLogsFileDescriptor>
  requires TRFILEDESCR =/=K .FileDescr

rule <k> #closeTraceLogsFile => .K ... </k> [owise]
 // ---------------------------------------------------------------------------------------------------------------

    // accounts are stored as subcells in the <accounts> cell with multiplicity="*" and type="Map"
    // due to this, Map hooks cannot be used
    // instead, mutations on the state of accounts has to be traced individually with tracing rules of higher priority
    // both <nonce> and <balance> is moft often mutated directly by rules
    // these rules sometimes do not re-execute themselves, which is why an inserted K production can be
    //  used to enforce tracing to happen only once per mutation
    // rules that are re-executed or re-insert themselves into <k> must be overwritten entirely
    // rules that are not re-implemented entirely still re-implement the mutation formulars
    // therefore, these overridden rules are subject to potentially changed evm-semantics rules
    // ideally, new rules are introduced in the future in evm-semantics that moduralize mutations of nonce and balance 
    //  that would allow for tracing rules that do not re-implement evm-semantics specifications

    // evm.md:1483 [sstore] `STORE`
    rule [sstore]:
         <k> SSTORE INDEX NEW => .K ... </k>
         <traceStorage> true </traceStorage>
         <id> ACCT </id>
         <account>
           <acctID> ACCT </acctID>
           <storage> STORAGE => STORAGE [ INDEX <- NEW ] </storage>
           ...
         </account>
         <currentStorageMutations> ... .List => ListItem({ ACCT | INDEX | NEW }) </currentStorageMutations>
      [preserves-definedness,priority(49)]

 // ---------------------------------------------------------------------------------------------------------------
    // cheatcodes.md:1282 `#setStorage` 
    rule <k> #setStorage ACCTID LOC VALUE => .K ... </k>
         <traceStorage> true </traceStorage>
         <account>
           <acctID> ACCTID </acctID>
           <storage> STORAGE => STORAGE [ LOC <- VALUE ] </storage>
             ...
         </account>
         <currentStorageMutations> ... .List => ListItem({ ACCTID | LOC | VALUE }) </currentStorageMutations>
      [priority(49)]

 // ---------------------------------------------------------------------------------------------------------------
    // TODO: `#addAuthority` will change nonce starting with a newer revision of evm-semantics


 // ---------------------------------------------------------------------------------------------------------------
    // evm.md:1830 `#mkCreate ACCTFROM ACCTTO VALUE INITCODE`
    rule <k> #mkCreate ACCTFROM ACCTTO VALUE INITCODE
          => #touchAccounts ACCTFROM ACCTTO ~> #accessAccounts ACCTFROM ACCTTO ~> #loadProgram INITCODE ~> #initVM ~> #execute
         ...
         </k>
         <traceNonce> true </traceNonce>
         <useGas> USEGAS </useGas>
         <schedule> SCHED </schedule>
         <id> _ => ACCTTO </id>
         <gas> GAVAIL => #if USEGAS #then GCALL #else GAVAIL #fi </gas>
         <callGas> GCALL => #if USEGAS #then 0 #else GCALL #fi </callGas>
         <caller> _ => ACCTFROM </caller>
         <callDepth> CD => CD +Int 1 </callDepth>
         <callData> _ => .Bytes </callData>
         <callValue> _ => VALUE </callValue>
         <account>
           <acctID> ACCTTO </acctID>
           <nonce> NONCE => #if Gemptyisnonexistent << SCHED >> #then NONCE +Int 1 #else NONCE #fi </nonce>
           ...
         </account>
         <createdAccounts> ACCTS => ACCTS |Set SetItem(ACCTTO) </createdAccounts>
         <currentNonceMutations> ... .List => ListItem({ACCTTO | #if Gemptyisnonexistent << SCHED >> #then NONCE +Int 1 #else NONCE #fi }:MapMutation) </currentNonceMutations>
      [priority(49)]

 // ---------------------------------------------------------------------------------------------------------------
    // evm.md:1850 `#incrementNonce ACCT`
    rule <k> #incrementNonce ACCT => .K ... </k>
         <traceNonce> true </traceNonce>
         <account>
           <acctID> ACCT </acctID>
           <nonce> NONCE => NONCE +Int 1 </nonce>
           ...
         </account>
         <currentNonceMutations> ... .List => ListItem({ ACCT | NONCE +Int 1 }:MapMutation) </currentNonceMutations>
      [priority(49)]

 // ---------------------------------------------------------------------------------------------------------------
    // state-utils.md:131 `loadAccount ACCT { "nonce" : (NONCE:Int), REST => REST }`
    rule <k> loadAccount ACCT { "nonce" : (NONCE:Int), REST => REST } ... </k>
         <traceNonce> true </traceNonce>
         <account> <acctID> ACCT </acctID> <nonce> _ => NONCE </nonce> ... </account>
         <currentNonceMutations> ... .List => ListItem({ ACCT | NONCE }:MapMutation) </currentNonceMutations>
      [priority(49)]

 // ---------------------------------------------------------------------------------------------------------------
    // cheatcodes.md:1254 `#setNonce ACCTID NONCE`
    rule <k> #setNonce ACCTID NONCE => .K ... </k>
         <traceNonce> true </traceNonce>
         <account>
             <acctID> ACCTID </acctID>
             <nonce> _ => NONCE </nonce>
             ...
         </account>
         <currentNonceMutations> ... .List => ListItem({ ACCTID | NONCE }:MapMutation) </currentNonceMutations>
      [priority(49)]


 // ---------------------------------------------------------------------------------------------------------------
    // driver.md:80 `#deductBlobGas`
    rule <k> #deductBlobGas => .K ... </k>
         <traceBalance> true </traceBalance>
         <schedule> SCHED </schedule>
         <excessBlobGas> EXCESS_BLOB_GAS </excessBlobGas>
         <origin> ACCTFROM </origin>
         <account>
           <acctID> ACCTFROM </acctID>
           <balance> BAL => BAL -Int Cblobfee(SCHED, EXCESS_BLOB_GAS, size(TVH)) </balance>
           ...
         </account>
         <txPending> ListItem(TXID:Int) ... </txPending>
         <message>
           <msgID>             TXID         </msgID>
           <txVersionedHashes> TVH          </txVersionedHashes>
           <txType>            Blob         </txType>
           ...
         </message>
         <currentBalanceMutations> ... .List => ListItem({ ACCTFROM | BAL -Int Cblobfee(SCHED, EXCESS_BLOB_GAS, size(TVH)) }:MapMutation) </currentBalanceMutations>
      requires Ghasblobbasefee << SCHED >>
      [priority(49)]

 // ---------------------------------------------------------------------------------------------------------------
    // evm.md:579 `#finalizeWithdrawals`
    rule <k> #finalizeWithdrawals ... </k>
         <traceBalance> true </traceBalance>
         <withdrawalsPending> ListItem(WDID) LS => LS </withdrawalsPending>
         <withdrawal>
           <withdrawalID> WDID </withdrawalID>
           <address> ACCT </address>
           <amount> VALUE </amount>
           ...
         </withdrawal>
         <account>
           <acctID> ACCT </acctID>
           <balance> B => B +Int #gweiToWei(VALUE) </balance>
           ...
         </account>
         <currentBalanceMutations> ... .List => ListItem({ ACCT | B +Int #gweiToWei(VALUE) }:MapMutation) </currentBalanceMutations>
      [priority(49)]


 // ---------------------------------------------------------------------------------------------------------------
    // evm.md:640 `#finalizeTx(false => true, GFLOOR)`
    rule <k> #finalizeTx(false => true, GFLOOR) ... </k>
         <traceBalance> true </traceBalance>
         <useGas> true </useGas>
         <schedule> SCHED </schedule>
         <baseFee> BFEE </baseFee>
         <origin> ORG </origin>
         <coinbase> MINER </coinbase>
         <gas> GAVAIL </gas>
         <gasUsed> GUSED => GUSED +Gas maxInt(GLIMIT -Int GAVAIL, GFLOOR) </gasUsed>
         <blobGasUsed> BLOB_GAS_USED => #if TXTYPE ==K Blob #then BLOB_GAS_USED +Int Ctotalblob(SCHED, size(TVH)) #else BLOB_GAS_USED #fi </blobGasUsed>
         <gasPrice> GPRICE </gasPrice>
         <refund> 0 </refund>
         <account>
           <acctID> ORG </acctID>
           <balance> ORGBAL => ORGBAL +Int minInt(GAVAIL, GLIMIT -Int GFLOOR) *Int GPRICE </balance>
           ...
         </account>
         <account>
           <acctID> MINER </acctID>
           <balance> MINBAL => MINBAL +Int maxInt(GLIMIT -Int GAVAIL, GFLOOR) *Int (GPRICE -Int BFEE) </balance>
           ...
         </account>
         <txPending> ListItem(MSGID:Int) REST => REST </txPending>
         <message>
           <msgID> MSGID </msgID>
           <txGasLimit> GLIMIT </txGasLimit>
           <txVersionedHashes> TVH </txVersionedHashes>
           <txType> TXTYPE </txType>
           ...
         </message>
         <currentBalanceMutations> ... .List => 
            ListItem({ ORG | ORGBAL +Int minInt(GAVAIL, GLIMIT -Int GFLOOR) *Int GPRICE }:MapMutation) 
            ListItem({ MINER | MINBAL +Int maxInt(GLIMIT -Int GAVAIL, GFLOOR) *Int (GPRICE -Int BFEE) }:MapMutation) 
         </currentBalanceMutations>
      requires ORG =/=Int MINER
      [priority(49)]

 // ---------------------------------------------------------------------------------------------------------------
    // evm.md:671 `#finalizeTx(false => true, GFLOOR)`
    rule <k> #finalizeTx(false => true, GFLOOR) ... </k>
         <traceBalance> true </traceBalance>
         <useGas> true </useGas>
         <schedule> SCHED </schedule>
         <baseFee> BFEE </baseFee>
         <origin> ACCT </origin>
         <coinbase> ACCT </coinbase>
         <gas> GAVAIL </gas>
         <gasUsed> GUSED => GUSED +Gas maxInt(GLIMIT -Int GAVAIL, GFLOOR)  </gasUsed>
         <blobGasUsed> BLOB_GAS_USED => #if TXTYPE ==K Blob #then BLOB_GAS_USED +Int Ctotalblob(SCHED, size(TVH)) #else BLOB_GAS_USED #fi </blobGasUsed>
         <gasPrice> GPRICE </gasPrice>
         <refund> 0 </refund>
         <account>
           <acctID> ACCT </acctID>
           <balance> BAL => BAL +Int GLIMIT *Int GPRICE -Int maxInt(GLIMIT -Int GAVAIL, GFLOOR) *Int BFEE </balance>
           ...
         </account>
         <txPending> ListItem(MSGID:Int) REST => REST </txPending>
         <message>
           <msgID> MSGID </msgID>
           <txGasLimit> GLIMIT </txGasLimit>
           <txVersionedHashes> TVH </txVersionedHashes>
           <txType> TXTYPE </txType>
           ...
         </message>
         <currentBalanceMutations> ... .List => ListItem({ ACCT | BAL +Int GLIMIT *Int GPRICE -Int maxInt(GLIMIT -Int GAVAIL, GFLOOR) *Int BFEE }:MapMutation) </currentBalanceMutations>
      [priority(49)]

 // ---------------------------------------------------------------------------------------------------------------
    // evm.md:848 `#finalizeBlock`
    rule <k> #finalizeBlock
          => #if Ghaswithdrawals << SCHED >> #then #finalizeWithdrawals #else .K #fi
          ~> #rewardOmmers(OMMERS)
          ~> #filterLogs 0
          ~> #finalizeBlockBlobs
         ...
         </k>
         <traceBalance> true </traceBalance>
         <schedule> SCHED </schedule>
         <ommerBlockHeaders> [ OMMERS ] </ommerBlockHeaders>
         <coinbase> MINER </coinbase>
         <account>
           <acctID> MINER </acctID>
           <balance> MINBAL => MINBAL +Int Rb < SCHED > </balance>
           ...
         </account>
         <log> LOGS </log>
         <logsBloom> _ => #bloomFilter(LOGS) </logsBloom>
         <currentBalanceMutations> ... .List => ListItem({ MINER | MINBAL +Int Rb < SCHED > }:MapMutation) </currentBalanceMutations>
      [priority(49)]

 // ---------------------------------------------------------------------------------------------------------------
    // evm.md:870 `#rewardOmmers([ _ , _ , OMMER , _ , _ , _ , _ , _ , OMMNUM , _ ] , REST)`
    rule <k> #rewardOmmers([ _ , _ , OMMER , _ , _ , _ , _ , _ , OMMNUM , _ ] , REST) => #rewardOmmers(REST) ... </k>
         <traceBalance> true </traceBalance>
         <schedule> SCHED </schedule>
         <coinbase> MINER </coinbase>
         <number> CURNUM </number>
         <account>
           <acctID> MINER </acctID>
           <balance> MINBAL => MINBAL +Int Rb < SCHED > /Int 32 </balance>
          ...
         </account>
         <account>
           <acctID> OMMER </acctID>
           <balance> OMMBAL => OMMBAL +Int Rb < SCHED > +Int (OMMNUM -Int CURNUM) *Int (Rb < SCHED > /Int 8) </balance>
          ...
         </account>
         <currentBalanceMutations> ... .List =>
            ListItem({ MINER | MINBAL +Int Rb < SCHED > /Int 32 }:MapMutation)
            ListItem({ OMMER | OMMBAL +Int Rb < SCHED > +Int (OMMNUM -Int CURNUM) *Int (Rb < SCHED > /Int 8) }:MapMutation)
         </currentBalanceMutations>
      [priority(49)]


 // ---------------------------------------------------------------------------------------------------------------
    // evm.md:1049 `#transferFunds ACCTFROM ACCTTO VALUE`
    rule <k> #transferFunds ACCTFROM ACCTTO VALUE => .K ... </k>
         <traceBalance> true </traceBalance>
         <account>
           <acctID> ACCTFROM </acctID>
           <balance> ORIGFROM => ORIGFROM -Word VALUE </balance>
           ...
         </account>
         <account>
           <acctID> ACCTTO </acctID>
           <balance> ORIGTO => ORIGTO +Word VALUE </balance>
           ...
         </account>
         <currentBalanceMutations> ... .List =>
            ListItem({ ACCTFROM | ORIGFROM -Word VALUE }:MapMutation)
            ListItem({ ACCTTO | ORIGTO +Word VALUE }:MapMutation)
         </currentBalanceMutations>
      requires ACCTFROM =/=K ACCTTO andBool VALUE <=Int ORIGFROM
      [preserves-definedness, priority(49)]


 // ---------------------------------------------------------------------------------------------------------------
    // evm.md:1993 `SELFDESTRUCT ACCT`
    rule <k> SELFDESTRUCT ACCT => #touchAccounts ACCT ~> #accessAccounts ACCT ~> #end EVMC_SUCCESS ... </k>
         <traceBalance> true </traceBalance>
         <schedule> SCHED </schedule>
         <id> ACCT </id>
         <selfDestruct> SDS => SDS |Set SetItem(ACCT) </selfDestruct>
         <account>
           <acctID> ACCT </acctID>
           <balance> _ => 0 </balance>
           ...
         </account>
         <output> _ => .Bytes </output>
         <createdAccounts> CA </createdAccounts>
         <currentBalanceMutations> ... .List => ListItem({ ACCT | 0 }:MapMutation) </currentBalanceMutations>
      requires ((notBool Ghaseip6780 << SCHED >>) orBool ACCT in CA)
      [priority(49)]

 // ---------------------------------------------------------------------------------------------------------------
    // state-utils.md:125 `loadAccount ACCT`
    rule <k> loadAccount ACCT { "balance" : (BAL:Int), REST => REST } ... </k>
         <traceBalance> true </traceBalance>
         <account> <acctID> ACCT </acctID> <balance> _ => BAL </balance> ... </account>
         <currentBalanceMutations> ... .List => ListItem({ ACCT | BAL }:MapMutation) </currentBalanceMutations>
      [priority(49)]

 // ---------------------------------------------------------------------------------------------------------------
    // cheatcodes.md:1214 `#setBalance ACCTID NEWBAL`
    rule <k> #setBalance ACCTID NEWBAL => .K ... </k>
         <traceBalance> true </traceBalance>
         <account>
           <acctID> ACCTID </acctID>
           <balance> _ => NEWBAL </balance>
           ...
         </account>
         <currentBalanceMutations> ... .List => ListItem({ ACCTID | NEWBAL }:MapMutation) </currentBalanceMutations>
      [priority(49)]

    

```
  Transaction Signing and execution
  ---------------------------------

  The next block of K code contains the set of functions used to implement `eth_sendTransaction`.
  The information send with the request is used to load a new `<message>` cell, sign, validate, and execute it.
  Once these steps are performed, a receipt is generated.

```k
    syntax RPCRequest ::= "#eth_sendTransaction" TxType Account Account Int Int Int Int Bytes [symbol(eth_sendTransaction)]
 // -----------------------------------------------------------------------------------------------------------------------
    rule <k> #eth_sendTransaction TXTYPE ACCTFROM ACCTTO TXGAS TXGASPRICE TXVALUE TXNONCE TXDATA
          => #updateBlockHeader
          ~> mkTX !TXID
          ~> #loadTransaction !TXID TXTYPE ACCTFROM ACCTTO TXGAS TXGASPRICE TXVALUE TXNONCE TXDATA
          ~> #openTraceLogsFile
          ~> #runTransaction !TXID ACCTFROM
          ~> #closeTraceLogsFile
          ~> #makeTxReceipt !TXID
          ~> #finalizeBlock
          ~> #computeHeaderHash
          ... </k>
          <traceData> _ => .List </traceData>

    syntax KItem ::= "#loadTransaction" Int TxType Account Account Int Int Int Int Bytes
 // ------------------------------------------------------------------------------------
    rule <k> #loadTransaction TXID TXTYPE ACCTFROM ACCTTO TXGAS TXGASPRICE TXVALUE TXNONCE TXDATA
          => #signTX TXID ACCTFROM
          ...
         </k>
         <chainID> CID </chainID>
         <currentTxID> _ => TXID </currentTxID>
         <message>
           <msgID> TXID </msgID>
           <txNonce>    _ => TXNONCE    </txNonce>
           <txGasPrice> _ => TXGASPRICE </txGasPrice>
           <txGasLimit> _ => TXGAS      </txGasLimit>
           <to>         _ => ACCTTO     </to>
           <value>      _ => TXVALUE    </value>
           <data>       _ => TXDATA     </data>
           <txChainID>  _ => CID        </txChainID>
           <txType>     _ => TXTYPE     </txType>
           ...
         </message>
         <account> <acctID> ACCTFROM </acctID> <nonce> TXNONCE </nonce> ... </account>



    // ECDSASign returns [r,s,recid]
    // previously of EIP155, v is computed as:  v = recid + 27
    // post of EIP155, v is computed as :       v = 2 * CHAIN_ID + recid + 35

    syntax KItem ::= "#signTX" Int Int
                   | "#signTX" Int String
 // -------------------------------------
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

    rule <k> #signTX TXID SIG:String => .K ... </k>
         <chainID> B </chainID>
         <message>
           <msgID> TXID </msgID>
           <sigR> _ => #parseHexBytes( substrString( SIG, 0, 64 ) )           </sigR>
           <sigS> _ => #parseHexBytes( substrString( SIG, 64, 128 ) )         </sigS>
           <sigV> _ => 2 *Int B +Int #parseHexWord( substrString( SIG, 128, 130 ) ) +Int 35 </sigV>
           ...
         </message>

    rule <k> #signTX TXID ACCTFROM:Int => .K ... </k>
         <accountKeys> KEYMAP                      </accountKeys>
         <mode>        NORMAL                      </mode>
         <txPending>   ListItem(TXID) => .List ... </txPending>
         <txOrder>     ListItem(TXID) => .List ... </txOrder>
         <rpcResponse> _ => -1 </rpcResponse> // TODO: Come up with error code values for this cell
      requires notBool ACCTFROM in_keys(KEYMAP)

    syntax KItem ::= "#runTransaction" Int Account
 // ----------------------------------------------
    rule <k> #runTransaction TXID:Int ACCTFROM
          => #setup_G0 TXID
          ~> #validateTx TXID
          ~> #updateTimestamp
          ~> #executeTx TXID
          ...
          </k>
         <origin> _ => ACCTFROM </origin>

    syntax KItem ::= "#setup_G0" Int
 // --------------------------------
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
 // ----------------------------------
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
 // -----------------------------------
    rule <k> #updateTimestamp => .K ... </k> <timestamp> TS => TS +Int TD </timestamp> <timeDiff> TD </timeDiff>

    syntax KItem ::= "#executeTx" Int
 // ---------------------------------
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
         <currentBalanceMutations> ... .List => #if TRBAL #then ListItem({ ACCTFROM | BAL -Int (GLIMIT *Int GPRICE) }:MapMutation) #else .List #fi </currentBalanceMutations>

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
         <currentNonceMutations> ... .List => #if TRNONCE #then ListItem({ ACCTFROM | NONCE +Int 1 }:MapMutation) #else .List #fi </currentNonceMutations>
         <currentBalanceMutations> ... .List => #if TRBAL #then ListItem({ ACCTFROM | BAL -Int (GLIMIT *Int GPRICE) }:MapMutation) #else .List #fi </currentBalanceMutations>
      requires ACCTTO =/=K .Account

    syntax KItem ::= "#makeTxReceipt" Int
 // -------------------------------------
    rule <k> #makeTxReceipt TXID => .K ... </k>
         <rpcResponse> _ =>  Keccak256(#rlpEncode( [ TN, TP, TG, #addrBytes(TT), TV, TD, TW, TR, TS ] )) </rpcResponse>
         <txReceipts>
           ( .Bag
          => <txReceipt>
               <txHash> Keccak256(#rlpEncode( [ TN, TP, TG, #addrBytes(TT), TV, TD, TW, TR, TS ] )) </txHash>
               <txCumulativeGas> CGAS                           </txCumulativeGas>
               <logSet>          LOGS                           </logSet>
               <bloomFilter>     #bloomFilter(LOGS)             </bloomFilter>
               <txStatus>        bool2Word(SC ==K EVMC_SUCCESS) </txStatus>
               <txID>            TXID                           </txID>
               <sender>          ACCT                           </sender>
               <txBlockNumber>   BN                             </txBlockNumber>
               <contractAddress>
                 #if TT ==K .Account #then #newAddr(ACCT, TN) #else .Account #fi
               </contractAddress>
             </txReceipt>
           )
           ...
         </txReceipts>
         <message>
           <msgID>      TXID </msgID>
           <txNonce>    TN  </txNonce>
           <txGasPrice> TP  </txGasPrice>
           <txGasLimit> TG  </txGasLimit>
           <to>         TT  </to>
           <value>      TV  </value>
           <sigV>       TW  </sigV>
           <sigR>       TR  </sigR>
           <sigS>       TS  </sigS>
           <data>       TD  </data>
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
    syntax KItem ::= "#updateParentHash"
                   | "#incrementBlockNumber"
                   | "#clearGas"
                   | "#clearTxLists"
              //   | "#updateTrieRoots"
              //   | "#updateStateRoot"
              //   | "#updateTransactionsRoot"
              //   | "#updateReceiptsRoot"
              //   | "#initStateTrie"
              //   | "#updateStateTrie"
              //   | #updateStateTrie ( JSONs )
 // -------------------------------------------

    rule <k> #updateParentHash => .K ... </k>
         <previousHash> _ => HP </previousHash>
         <currentBlockHash> HP </currentBlockHash>

    rule <k> #incrementBlockNumber => .K ... </k> <number> BN => BN +Int 1 </number>

    rule <k> #clearTxLists => .K ... </k>
         <txPending> _ => .List </txPending>
         <txOrder>   _ => .List </txOrder>

    rule <k> #clearGas => .K ... </k> <gas> _ => 0 </gas>
```

  Helper Funcs
  ------------

```k
    syntax KItem ::= "#computeHeaderHash" [symbol(computeHeaderHash)]
 // -----------------------------------------------------------------
    rule <k> #computeHeaderHash => .K ... </k>
         <currentBlockHash> _ => #blockHeaderHash(HP, HO, HC, HR, HT, HE, HB, HD, HI, HL, HG, HS, HX, HM, HN) </currentBlockHash>
         <previousHash>     HP </previousHash>
         <ommersHash>       HO </ommersHash>
         <coinbase>         HC </coinbase>
         <stateRoot>        HR </stateRoot>
         <transactionsRoot> HT </transactionsRoot>
         <receiptsRoot>     HE </receiptsRoot>
         <logsBloom>        HB </logsBloom>
         <difficulty>       HD </difficulty>
         <number>           HI </number>
         <gasLimit>         HL </gasLimit>
         <gasUsed>          HG </gasUsed>
         <timestamp>        HS </timestamp>
         <extraData>        HX </extraData>
         <mixHash>          HM </mixHash>
         <blockNonce>       HN </blockNonce>

    syntax KItem ::= "#updateBlockHeader" [symbol(updateBlockHeader)]
 // -----------------------------------------------------------------
    rule <k> #updateBlockHeader
          => #updateParentHash
          ~> #startBlock
          ~> #incrementBlockNumber
          ~> #clearTxLists
          ~> #clearGas ... </k>

    syntax KItem ::= "#setAcctBalance" Int Int
 // ------------------------------------------
    rule <k> #setAcctBalance KEY BAL => .K ... </k>
         <traceBalance> TRBAL </traceBalance>
         <accounts>
           <account>
             <acctID> KEY </acctID>
             <balance> _ => BAL </balance>
             ...
           </account>
           ...
         </accounts>
         <currentBalanceMutations> ... .List => #if TRBAL #then ListItem({ KEY | BAL }:MapMutation) #else .List #fi </currentBalanceMutations>
endmodule

```