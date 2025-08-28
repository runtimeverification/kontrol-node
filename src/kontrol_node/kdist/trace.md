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
    imports ETHEREUM-SIMULATION


```
The configuration of the KEVMTracing is defined as following:
- `<activeTracing>` signals if the tracing feature is active or not.
- `<traceStorage>` signals if the storage should be recorded in the `TraceItem`.
- `<traceWordStack>` signals if the storage should be recorded in the `TraceItem`.
- `<traceMemory>` signals if the storage should be recorded in the `TraceItem`.
- `<recordedTrace>` is an auxiliary cell that is used to determine if the current step has been recorded or not.
- `<traceData>` is a collection of `TraceItem`s.

```k
    configuration
      <KEVMTracing>
        <activeTracing>           false       </activeTracing>
        <traceStorage>            false       </traceStorage>
        <traceWordStack>          false       </traceWordStack>
        <traceMemory>             false       </traceMemory>
        <recordedTrace>           false       </recordedTrace>
        <traceData>               .List       </traceData>
        <traceLogsFileDescriptor> .FileDescr  </traceLogsFileDescriptor>
        <traceLogsFilePath>       "":String   </traceLogsFilePath>
        <writeTraceLogsToFile>    false       </writeTraceLogsToFile>

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
      </KEVMTracing>
```

```k
    syntax MapMutation ::= "{" Int "|" Int "|" Int "}" [symbol(node_intDoubleMapMutation)]
                         | "{" Int "|" Int "}"         [symbol(node_intMapMutation)]
                         | "{" Int "|" Bytes "}"       [symbol(node_bytesMapMutation)]

   syntax KItem ::= "#openTraceLogsFile"            [symbol(openTraceLogsFile)]
                  | "#closeTraceLogsFile"           [symbol(closeTraceLogsFile)]
                  | "#storeTraceLogsFileDescriptor" [symbol(storeTraceLogsFileDescriptor)]

   
   syntax FILEDESCR ::= Int | ".FileDescr"
 // ----------------------------------------------------------------------------------
```

The `TraceItem` is a sort used to serialize information from the configuration about the executed opcodes.

```k

    syntax TraceItem ::= "{" 
          Int          // program counter 
      "|" OpCode       // opcode
      "|" WordStack    // stack
      "|" DataChange   // memory
      "|" List // storage changes
      "|" List // nonce changes
      "|" List // balance changes
      "|" DataChange   // call data change
      "|" DataChange   // return data change
      "|" DataChange   // program change
      "|" List // deployed code changes
      "|" List // init code changes
      "|" Int          // call depth
      "|" Int          // gas
      "|" Account      // coinbase
      "|" Int          // gas price
      "|" Int          // difficulty
      "|" Int          // block number
      "|" Int          // block timestamp
      "|" Account      // target address
      "|" Account      // code address
      "|" Account      // message sender
      "|" Int          // message value
      "|" Account      // transaction origin
      "|" Bool         // is init code
      "|" StatusCode   // status
    "}" [symbol(traceItem)]

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
         <currentStorageMutations> ... .List => ListItem({ ACCT | INDEX | NEW }:MapMutation) </currentStorageMutations>
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
         <currentStorageMutations> ... .List => ListItem({ ACCTID | LOC | VALUE }:MapMutation) </currentStorageMutations>
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

endmodule
 ```