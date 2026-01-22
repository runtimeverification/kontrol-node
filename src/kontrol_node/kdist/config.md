```k

requires "foundry.md"
requires "driver.md"

module KONTROL-NODE-CONFIG
    imports FOUNDRY
    imports ETHEREUM-SIMULATION

    configuration <simbolikVM>
            <foundry/>
            <ioDir>                   "":String </ioDir>
            <rpcRequestId>            0         </rpcRequestId>
            <accountKeys>             .Map      </accountKeys>
            <timeFreeze>              true      </timeFreeze>
            <timeDiff>                0         </timeDiff>
            <currentTxID>             0         </currentTxID>
            <currentBlockHash>        0         </currentBlockHash>

            // Tracing
            <activeTracing>           true  </activeTracing>          // signals if the tracing is gloablly enabled
            <traceNonce>              true  </traceNonce>             // signals if nonce tracing is enabled
            <traceBalance>            true  </traceBalance>           // signals if balance tracing enabled

            <recordedTrace>           false </recordedTrace>           // auxiliary cell that is used to determine if the current step has been recorded or not.

            <currentNonceMutations>   .Map </currentNonceMutations>   // Buffer nonce changes
            <currentBalanceMutations> .Map </currentBalanceMutations> // Buffer balance changes
            <currentStorageMutations> .Map </currentStorageMutations> // Buffer storage changes
            <localMemoryChanged>      true  </localMemoryChanged>     // Buffer memory changes


            <injectedTracesCallStack> false </injectedTracesCallStack>
            <recordedMkCallCreate>    false </recordedMkCallCreate>
            <contextSwitch>           true  </contextSwitch>
            <traceCallData>           false </traceCallData>
            <traceReturnData>         false </traceReturnData>
            <tracesCallStack>         .List </tracesCallStack>
            <tracesCallState>
                <isInitCode>          false </isInitCode>
            </tracesCallState>

            <traceCurrentProgram>          false </traceCurrentProgram>
            <programChanged>               true  </programChanged>

            <traceDeployedCode>            false </traceDeployedCode>
            <currentDeployedCodeMutations> .Map  </currentDeployedCodeMutations>

            <traceInitCode>                false </traceInitCode>
            <currentInitCodeMutations>     .Map  </currentInitCodeMutations>
            <recordedCreate>               false </recordedCreate>

            // Block-related
            <stateTrie> .MerkleTree </stateTrie>
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
                </txReceipt>
            </txReceipts>
        </simbolikVM>

endmodule
```