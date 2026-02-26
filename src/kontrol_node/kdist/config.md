```k

requires "foundry.md"
requires "driver.md"

module KONTROL-NODE-CONFIG
    imports FOUNDRY
    imports ETHEREUM-SIMULATION

    configuration <simbolikVM>
            <foundry/>
            <ioDir>                   "":String </ioDir>
            <rpcRequestID>            0         </rpcRequestID>
            <rpcRequestBatchIndex>    -1        </rpcRequestBatchIndex>
            <accountKeys>             .Map      </accountKeys>
            <timeFreeze>              true      </timeFreeze>
            <currentTxID>             0         </currentTxID>

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
            <traceCallData>           true  </traceCallData>
            <traceReturnData>         true  </traceReturnData>
            <tracesCallStack>         .List </tracesCallStack>
            <tracesCallState>
                <isInitCode>          false </isInitCode>
            </tracesCallState>

            <traceCurrentProgram>          true  </traceCurrentProgram>
            <programChanged>               true  </programChanged>

            <traceDeployedCode>            true  </traceDeployedCode>
            <currentDeployedCodeMutations> .Map  </currentDeployedCodeMutations>

            <traceInitCode>                true  </traceInitCode>
            <currentInitCodeMutations>     .Map  </currentInitCodeMutations>
            <recordedCreate>               false </recordedCreate>

            // Block-related
            <txReceipts>
                <txReceipt multiplicity ="*" type="Map">
                    <txMsg>           0          </txMsg>
                    <txBlockNumber>   0          </txBlockNumber>
                    <txHash>          0          </txHash>
                    <txCumulativeGas> 0          </txCumulativeGas>
                    <txLogs>          .List      </txLogs>
                    <txLogsBloom>     .Bytes     </txLogsBloom>
                    <txStatus>        0          </txStatus>
                </txReceipt>
            </txReceipts>
            <blockStorage> .Map </blockStorage>
            <blockHashes>  .Map </blockHashes>
        </simbolikVM>

endmodule
```