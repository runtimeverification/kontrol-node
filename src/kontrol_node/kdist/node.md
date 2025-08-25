```k
requires "foundry.md"
requires "driver.md"
requires "no_code_size_checks.md"

module KONTROL-NODE
    imports FOUNDRY
    imports ETHEREUM-SIMULATION
    imports NO-CODE-SIZE-CHECKS
    imports K-IO
    imports K-REFLECTION

    syntax RPCRequest ::= ".RPCRequest" [symbol(EmptyRPCRequest)]
 // -------------------------------------------------------------

    syntax RPCResponse ::= String | Int
                         | ".RPCResponse" [symbol(EmptyRPCResponse)]
 // ----------------------------------------------------------------

    syntax MapMutation ::= "{" Int "|" Int "|" Int "}" [symbol(node_intDoubleMapMutation)]
                         | "{" Int "|" Int "}"         [symbol(node_intMapMutation)]
                         | "{" Int "|" Bytes "}"       [symbol(node_bytesMapMutation)]

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

                    <localMemoryChanged>      true  </localMemoryChanged>

                    <injectedTracesCallStack> false </injectedTracesCallStack>
                    <recordedMkCallCreate>    false </recordedMkCallCreate>
                    <contextSwitch>           true  </contextSwitch>
                    <traceCallData>           false </traceCallData>
                    <traceReturnData>         false </traceReturnData>
                    <tracesCallStack>         .List </tracesCallStack>
                    <tracesCallState>
                      <isInitCode> false </isInitCode>
                    </tracesCallState>

                    <traceCurrentProgram> false </traceCurrentProgram>
                    <programChanged> true </programChanged>

                    <traceDeployedCode> false </traceDeployedCode>
                    <currentDeployedCodeMutations> .List </currentDeployedCodeMutations>

                    <traceInitCode> false </traceInitCode>
                    <currentInitCodeMutations> .List </currentInitCodeMutations>
                    <recordedCreate> false </recordedCreate>

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
      "|" DataChange // memory
      "|" List       // storage changes
      "|" List       // nonce changes
      "|" List       // balance changes
      "|" DataChange // call data change
      "|" DataChange // return data change
      "|" DataChange // program change
      "|" List       // deployed code changes
      "|" List       // init code changes
      "|" Int        // call depth
      "|" Int        // gas
      "|" Account    // coinbase
      "|" Int        // gas price
      "|" Int        // difficulty
      "|" Int        // block number
      "|" Int        // block timestamp
      "|" Account    // target address
      "|" Account    // code address
      "|" Account    // message sender
      "|" Int        // message value
      "|" Account    // transaction origin
      "|" Bool       // is init code
      "|" StatusCode // status
    "}" [symbol(traceItem)]

    syntax KItem ::= "#storeTraceItem" TraceItem
 // ---------------------------------------------------------------------------------------------------------------
    rule <k> (.K => #storeTraceItem { PCOUNT
                                    | OPC
                                    | #if DSTK ==K true #then WS      #else .WordStack #fi
                                    | #if (DMEM andBool MEMCH)          ==K true #then MEM  #else .DataChange #fi
                                    | STORCH
                                    | NONCECH
                                    | BALCH
                                    | #if (DCADA andBool CONTEXTSWITCH) ==K true #then CADA #else .DataChange #fi
                                    | #if (DREDA andBool CONTEXTSWITCH) ==K true #then REDA #else .DataChange #fi
                                    | #if PROGCHANGED                   ==K true #then PROG #else .DataChange #fi
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
         <traceWordStack>               DSTK                   </traceWordStack>
         <traceMemory>                  DMEM                   </traceMemory>
         <traceCallData>                DCADA                  </traceCallData>
         <traceReturnData>              DREDA                  </traceReturnData>
         <recordedTrace>                false => true          </recordedTrace>
         <recordedMkCallCreate>         _ => false             </recordedMkCallCreate>
         <recordedCreate>               _ => false             </recordedCreate>
         <localMemoryChanged>           MEMCH => false         </localMemoryChanged>
         <currentNonceMutations>        NONCECH => .List       </currentNonceMutations>          
         <contextSwitch>                CONTEXTSWITCH => false </contextSwitch>
         <currentBalanceMutations>      BALCH => .List         </currentBalanceMutations>          
         <currentStorageMutations>      STORCH => .List        </currentStorageMutations>
         <programChanged>               PROGCHANGED => false   </programChanged>
         <currentDeployedCodeMutations> DEPLCODECH => .List    </currentDeployedCodeMutations>
         <currentInitCodeMutations>     INITCODECH => .List    </currentInitCodeMutations>
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

    rule <k> #storeTraceItem TRITEM => .K ... </k>
         <writeTraceLogsToFile> false </writeTraceLogsToFile>
         <traceData>
           ...
           .List => ListItem(TRITEM)
         </traceData>

    rule <k> #storeTraceItem TRITEM => #write (TRFILEDESCR, 
               #unparseKORE( TRITEM ) +String "\n"
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
     <traceLogsFilePath> TRFILEPATH </traceLogsFilePath>
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
    // both <nonce> and <balance> are most often mutated directly by rules
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
         <codeAddr> _ => ACCTTO </codeAddr>
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

 // ---------------------------------------------------------------------------------------------------------------
    syntax DataChange ::= ".DataChange" [symbol(UnchangedData)]
                        | Bytes
 
    // trace `isInitcode`
    // create a second callstack <tracesCallStack> with <isInitcode> subcell
    //  hook into callstack changes by overriding `#pushCallStack`/`#popCallStack`
    //  and insert new productions `#pushTracesCallStack`/`#popTracesCallStack`
    // init <isInitcode> to false and update state on `#mkCreate/#mkCall/#mkSystemCall`

    syntax KItem ::= "#pushTracesCallStack"
                   | "#popTracesCallStack"

    // `#pushCallStack` does not append new KItems after itself
    // therefore this kind of hook is safe
    rule <k> #pushCallStack ~> (.K => #pushTracesCallStack) ... </k>
         <injectedTracesCallStack> false => true </injectedTracesCallStack>
      [priority(49)]

    // `#popCallStack` does not append new KItems after itself
    // therefore this kind of hook is safe
    rule <k> #popCallStack ~> (.K => #popTracesCallStack) ... </k>
         <injectedTracesCallStack> false => true </injectedTracesCallStack>
      [priority(49)]
    
    // track with <contextSwitch> that call data and return data has changed and needs to be included in the next trace
    rule <k> #pushTracesCallStack => .K ... </k>
         <injectedTracesCallStack> true => false </injectedTracesCallStack>
         <tracesCallStack> STACK => ListItem(<tracesCallState> TRACESCALLSTATE </tracesCallState>) STACK </tracesCallStack>
         <tracesCallState> TRACESCALLSTATE </tracesCallState>
         <contextSwitch> _ => true </contextSwitch>

    // track with <contextSwitch> that call data and return data has changed and needs to be included in the next trace
    rule <k> #popTracesCallStack => .K ... </k>
         <injectedTracesCallStack> true => false </injectedTracesCallStack>
         <tracesCallStack> ListItem(<tracesCallState> TRACESCALLSTATE </tracesCallState>) REST => REST </tracesCallStack>
         <tracesCallState> _ => TRACESCALLSTATE </tracesCallState>
         <contextSwitch> _ => true </contextSwitch>
         <programChanged> _ => true </programChanged>
         <localMemoryChanged> _ => true </localMemoryChanged>

    rule <k> #mkCreate _ _ _ _ ... </k>
         <recordedMkCallCreate> false => true </recordedMkCallCreate>
         <isInitCode>           _ => true     </isInitCode>
      [priority(48)]

    rule <k> #mkCall _ _ _ _ _ _ _ ... </k>
         <recordedMkCallCreate> false => true </recordedMkCallCreate>
         <isInitCode>           _ => false    </isInitCode>
      [priority(48)]

    // TODO: `#mkSystemCall` is introduced in a newer revision of evm-semantics
    // rule <k> #mkSystemCall _ _ </k>
    //      <recordedMkCallCreate> false => true </recordedMkCallCreate>
    //      <isInitCode>           _ => false    </isInitCode>
    //   [priority(49)]

 // ---------------------------------------------------------------------------------------------------------------
    // trace <program> changes by `#loadProgram`
    // we override and re-implement the original rule to additionally record program changes
    // the <program> cell is also changed at `#popTracesCallStack`
    rule [program.load]:
         <k> #loadProgram BYTES => .K ... </k>
         <traceCurrentProgram> true </traceCurrentProgram>
         <program> _ => BYTES </program>
         <jumpDests> _ => #computeValidJumpDests(BYTES) </jumpDests>
         <programChanged> false => true </programChanged>
      [priority(49)]
 // ---------------------------------------------------------------------------------------------------------------
    // trace deployed code to accounts by overriding and re-implementing rules from evm-semantics
    rule <k> #finishCodeDeposit ACCT OUT
          => #popCallStack ~> #dropWorldState
          ~> #refund GAVAIL ~> ACCT ~> #push
         ...
         </k>
         <traceDeployedCode> true </traceDeployedCode>
         <gas> GAVAIL </gas>
         <account>
           <acctID> ACCT </acctID>
           <code> _ => OUT </code>
           ...
         </account>
         <currentDeployedCodeMutations> ... .List => ListItem({ ACCT | OUT }:MapMutation) </currentDeployedCodeMutations>
      [priority(49)]

    rule <k> loadAccount ACCT { "code" : (CODE:Bytes), REST => REST } ... </k>
         <account> <acctID> ACCT </acctID> <code> _ => CODE </code> ... </account>
         <currentDeployedCodeMutations> ... .List => ListItem({ ACCT | CODE }:MapMutation) </currentDeployedCodeMutations>
      [priority(49)]

    // trace program changes by cheatcodes as well
    rule <k> #setCode ACCTID CODE => .K ... </k>
         <traceDeployedCode> true </traceDeployedCode>
         <account>
           <acctID> ACCTID </acctID>
           <code> _ => #if #asWord(CODE) ==Int 0 #then .Bytes #else CODE #fi </code>
           ...
         </account>
         <currentDeployedCodeMutations> ... .List => ListItem({ ACCTID | #if #asWord(CODE) ==Int 0 #then .Bytes #else CODE #fi }:MapMutation) </currentDeployedCodeMutations>
      [priority(49)]

    rule <k> #etchAccountIfEmpty ACCT => .K ... </k>
         <traceDeployedCode> true </traceDeployedCode>
         <accounts>
           <account>
             <acctID> ACCT </acctID>
             <code> CODE => #bufStrict(1,0) </code>
             ...
           </account>
           ...
         </accounts>
         <currentDeployedCodeMutations> ... .List => ListItem({ ACCT | #bufStrict(1,0) }:MapMutation) </currentDeployedCodeMutations>
      requires lengthBytes(CODE) ==Int 0
      [priority(49)]

 // ---------------------------------------------------------------------------------------------------------------
    // trace init program code changes
    // init programs are passed to `#create` and `#mkCreate`
    // as a `#create` is always followed by `#mkCreate`, we can make use of a call
    // that is set on `#create` and reset on `#mkCreate` without relying on re-implementing 
    // the respective rules for tracing
    rule <k> #create _ ACCTTO _ INITCODE ... </k>
         <traceInitCode> true </traceInitCode>
         <currentInitCodeMutations> ... .List => ListItem({ ACCTTO | INITCODE }:MapMutation) </currentInitCodeMutations>
         <recordedCreate> false => true </recordedCreate>
      [priority(49)]

 // ---------------------------------------------------------------------------------------------------------------
    // trace memory changes to reduce the size of traces
    // when memory change, we trace the entire memory contents
    // the <localMemory> cell is also changed at `#popTracesCallStack`
    rule <k> MSTORE _ _ ... </k>
         <traceMemory> true </traceMemory>
         <localMemoryChanged> false => true </localMemoryChanged>
      [priority(49)]

    rule <k> MSTORE8 _ _ ... </k>
         <traceMemory> true </traceMemory>
         <localMemoryChanged> false => true </localMemoryChanged>
      [priority(49)]

    rule <k> MCOPY _ _ _ ... </k>
         <traceMemory> true </traceMemory>
         <localMemoryChanged> false => true </localMemoryChanged>
      [priority(49)]

    rule <k> CODECOPY _ _ _ ... </k>
         <traceMemory> true </traceMemory>
         <localMemoryChanged> false => true </localMemoryChanged>
      [priority(49)]

    rule <k> CALLDATACOPY _ _ _ ... </k>
         <traceMemory> true </traceMemory>
         <localMemoryChanged> false => true </localMemoryChanged>
      [priority(49)]

    rule <k> RETURNDATACOPY _ _ _ ... </k>
         <traceMemory> true </traceMemory>
         <localMemoryChanged> false => true </localMemoryChanged>
      [priority(49)]

    rule <k> EXTCODECOPY _ _ _ _ ... </k>
         <traceMemory> true </traceMemory>
         <localMemoryChanged> false => true </localMemoryChanged>
      [priority(49)]

    rule <k> #initVM ... </k>
         <traceMemory> true </traceMemory>
         <localMemoryChanged> false => true </localMemoryChanged>
      [priority(49)]

    rule <k> #setLocalMem _ _ _ ... </k>
         <traceMemory> true </traceMemory>
         <localMemoryChanged> false => true </localMemoryChanged>
      [priority(49)]

    rule <k> clearTX ... </k>
         <traceMemory> true </traceMemory>
         <localMemoryChanged> false => true </localMemoryChanged>
      [priority(49)]

  // ---------------------------------------------------------------------------------------------------------------
    // the `#setMockCall` rules in kontrol are unsound and cause execution issues when run using the llvm-backend
    // TODO: remove this once the fixes (using [owise]) were upstreamed to kontrol
    rule <k> #setMockCall MOCKADDRESS MOCKCALLDATA MOCKRETURN => .K ... </k>
         <mockCall>
            <mockAddress> MOCKADDRESS </mockAddress>
            <mockValues>  MOCKVALUES => MOCKVALUES [ MOCKCALLDATA <- MOCKRETURN ] </mockValues>
         </mockCall>
      [priority(49)]

    rule <k> #setMockCall MOCKADDRESS MOCKCALLDATA MOCKRETURN => .K ... </k>
         <mockCalls>
           ( .Bag
            => <mockCall>
                  <mockAddress> MOCKADDRESS </mockAddress>
                  <mockValues> .Map [ MOCKCALLDATA <- MOCKRETURN ] </mockValues>
               </mockCall>
           )
           ...
         </mockCalls>
      [owise,priority(49)]

    // same issue with `#setMockFunction`
    // TODO: remove this once the fixes (using [owise]) were upstreamed to kontrol
    rule <k> #setMockFunction MOCKADDRESS MOCKTARGET MOCKCALLDATA => .K ... </k>
         <mockFunction>
            <mockFunctionAddress> MOCKADDRESS </mockFunctionAddress>
            <mockFunctionValues>  MOCKVALUES => MOCKVALUES [ MOCKCALLDATA <- MOCKTARGET ] </mockFunctionValues>
         </mockFunction>
      [priority(49)]

   rule <k> #setMockFunction MOCKADDRESS MOCKTARGET MOCKCALLDATA => .K ... </k>
         <mockFunctions>
           ( .Bag
            => <mockFunction>
                  <mockFunctionAddress> MOCKADDRESS </mockFunctionAddress>
                  <mockFunctionValues> .Map [ MOCKCALLDATA <- MOCKTARGET ] </mockFunctionValues>
               </mockFunction>
           )
           ...
         </mockFunctions>
      [owise,priority(49)]

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