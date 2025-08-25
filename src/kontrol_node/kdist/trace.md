```k
requires "foundry.md"
requires "driver.md"

```

Debug Collection with KEVM
--------------------------
This module handles the tracing of EVM opcodes during an execution.

```k
module EVM-TRACING
    imports EVM
    imports FOUNDRY
    imports K-IO
    imports K-REFLECTION
    imports ETHEREUM-SIMULATION


```
The configuration of the KEVMTracing is defined as following:
- `<activeTracing>` signals if the tracing feature is active or not.
- `<traceStorage>` signals if the storage should be recorded in the `TraceItem`.
- `<traceWordStack>` signals if the storage should be recorded in the `TraceItem`.
- `<traceMemory>` signals if the storage should be recorded in the `TraceItem`.
- `<recordedTrace>` is an auxiliary cell that is used to determine if the current step has been recorded or not.
- `<traceData>` is a collection of `TraceItems`.

```k
    configuration
      <KEVMTracing>
        <activeTracing>           false      </activeTracing>
        <traceStorage>            false      </traceStorage>
        <traceWordStack>          false      </traceWordStack>
        <traceMemory>             false      </traceMemory>
        <traceNonce>              false      </traceNonce>
        <traceBalance>            false      </traceBalance>
        <recordedTrace>           false      </recordedTrace>
        <traceData>               .List      </traceData>
        <currentNonceMutations>   .List      </currentNonceMutations>
        <currentBalanceMutations> .List      </currentBalanceMutations>
        <currentStorageMutations> .List      </currentStorageMutations>
        <traceLogsFileDescriptor> .FileDescr </traceLogsFileDescriptor>
        <traceLogsFilePath>       "":String  </traceLogsFilePath>
        <writeTraceLogsToFile>    false      </writeTraceLogsToFile>
      </KEVMTracing>
```

```k
    syntax MapMutation ::= "{" Int "|" Int "|" Int "}" [symbol(node_doubleMapMutation)]
                         | "{" Int "|" Int "}"         [symbol(node_mapMutation)]
 // -----------------------------------------------------------------------------
```

The `TraceItem` is a sort used to serialize information from the configuration about the executed opcodes.

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
 // -----------------------

    syntax FILEDESCR ::= Int | ".FileDescr"
 // --------------------------------------

    rule <k> #execute ... </k>
         <recordedTrace> true => false </recordedTrace>
      [priority(25)]

    syntax KItem ::= "#storeTraceItem" TraceItem [symbol(storeTraceItem)]
 // ---------------------------------------------------------------------
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
               #unparseKORE( TRITEM ) +String "\n"
             ) ... </k>
         <writeTraceLogsToFile>    true        </writeTraceLogsToFile>
         <traceLogsFileDescriptor> TRFILEDESCR </traceLogsFileDescriptor>
      requires TRFILEDESCR =/=K .FileDescr

 // ---------------------------------------------------------------------------------------------------------------

    syntax KItem ::= "#openTraceLogsFile"            [symbol(openTraceLogsFile)]
                   | "#closeTraceLogsFile"           [symbol(closeTraceLogsFile)]
                   | "#storeTraceLogsFileDescriptor" [symbol(storeTraceLogsFileDescriptor)]
 // ---------------------------------------------------------------------------------------
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

endmodule
 ```