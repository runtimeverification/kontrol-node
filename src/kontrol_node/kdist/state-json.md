# JSON encoding of state snapshots

There is no standardized way for encoding state snapshots.
This encoding aims for compatbility with Anvil's `anvil_dumpState` format.

```k
requires "foundry.md"
requires "driver.md"

module STATE-JSON
  
    imports EVM
    imports FOUNDRY
    imports EVM-TRACING
    imports JSON
    imports STRING
    imports K-IO


```
This section builds a JSON datastructure representing
the StateDump from the configuration.

```k
    syntax JSON  ::= ( JSON )  [bracket]
    syntax JSONs ::= ( JSONs ) [bracket]
    syntax JSON  ::= accountsCellToJSON( AccountsCell )          [function, total, symbol(accountsCellToJSON)]
                   | accountCellToJSON( AccountCell )            [function, total, symbol(accountCellToJSON)]
                   | codeToJson(Bytes)                           [function, total, symbol(codeToJson)]
                   | storageToJSON(Map)                          [function, total, symbol(accStorageToJson)]

    syntax JSONs ::= accountsCellToJSONs( AccountsCell, JSONs )  [function, total, symbol(accountsCellToJSONs)]
                   | storageToJSONs( Map, JSONs )                [function, total, symbol(accStorageToJSONs)]

    syntax String ::= intToHex(Int)    [function, total]

    // Duplicated in trace-json.md where this is called intToHex
    rule intToHex( A:Int ) => "0x" +String Base2String(A, 16)
      requires A >=Int 0
    rule intToHex( A:Int ) => "-0x" +String Base2String( absInt(A), 16) [owise]

    // Duplicated in trace-json.md where this is called bytesToJson
    rule codeToJson( BYTES ) => "0x" +String Bytes2Hex( BYTES ) 

    // Duplicated in trace-json.md where this is called intMapToJson
    rule storageToJSON( ST ) => { storageToJSONs( ST, .JSONs ) }
    rule storageToJSONs( .Map, ACCU ) => ACCU
    rule storageToJSONs( (KEY |-> VAL) ST, ACCU) => storageToJSONs( ST, ( intToHex(KEY) : intToHex(VAL), ACCU ) )

    rule accountCellToJSON (
        <account>
            <acctID>            ACC_ID            </acctID>
            <balance>           ACC_BALANCE       </balance>
            <code>              ACC_CODE          </code>
            <storage>           ACC_STORAGE       </storage>
            <nonce>             ACC_NONCE         </nonce>
            ...
        </account>
    ) => Int2String(ACC_ID) : {
        "balance": ACC_BALANCE,
        "code": codeToJson( ACC_CODE ),
        "storage": storageToJSON( ACC_STORAGE ),
        "nonce" : ACC_NONCE
    }

    rule accountsCellToJSON( ACCS ) => { accountsCellToJSONs( ACCS, .JSONs ) }
    rule accountsCellToJSONs( <accounts> <account> ACC </account> ACCS:Bag </accounts>, ACCU)
            => accountsCellToJSONs( <accounts> ACCS </accounts>, (accountCellToJSON( <account> ACC </account> ) , ACCU) ) 
    rule accountsCellToJSONs( <accounts> .Bag </accounts>, ACCU ) => ACCU [owise]

    syntax KItem ::= #createStateDump()
                   | #StateDump( JSON )

    rule <k> #createStateDump()
        => #StateDump({
            "bestBlockNumber": BLOCK_NUMBER,
            "block": {
                "number": BLOCK_NUMBER,
                "beneficiary": BLOCK_COINBASE,
                "timestamp": BLOCK_TIMESTAMP,
                "gas_limit": BLOCK_GAS_LIMIT,
                "basefee": BLOCK_BASE_FEE,
                "difficulty": BLOCK_DIFFICULTY,
                "prevrandao": "0x0000000000000000000000000000000000000000000000000000000000000000",
                "blob_excess_gas_and_price": BLOCK_EXCESS_BLOB_GAS
            },
            "accounts": accountsCellToJSON( <accounts> ACCOUNTS </accounts> )
        }) ...
    </k>
    <block>
        <number>        BLOCK_NUMBER          </number>
        <coinbase>      BLOCK_COINBASE        </coinbase>
        <timestamp>     BLOCK_TIMESTAMP       </timestamp>
        <gasLimit>      BLOCK_GAS_LIMIT       </gasLimit>
        <baseFee>       BLOCK_BASE_FEE        </baseFee>
        <difficulty>    BLOCK_DIFFICULTY      </difficulty>
        <excessBlobGas> BLOCK_EXCESS_BLOB_GAS </excessBlobGas>
        ...
    </block>
    <accounts> ACCOUNTS </accounts>
```

Write the StateDump to disc.

```k
    syntax KItem ::= #storeStateDump()

    rule <k> #StateDump( ST)
          ~> #storeStateDump()
          => #write (
               STFILEDESCR, 
               JSON2String( ST ) +String "\n"
             ) ...
        </k>
        <stateDumpFileDescriptor> STFILEDESCR </stateDumpFileDescriptor>
      requires STFILEDESCR =/=K .FileDescr

```

Opening and closing files.

```k
    syntax KItem ::= #openStateDumpFile()
                   | #storeStateDumpFileDescriptor()
                   | #closeStateDumpFile()

    rule <k> #openStateDumpFile()
          => #open(SDFILEPATH, "w")
          ~> #storeStateDumpFileDescriptor() ...
        </k>
        <stateDumpFilePath> SDFILEPATH </stateDumpFilePath>

    rule <k> STFILEDESCR ~> #storeStateDumpFileDescriptor() => .K ... </k>
        <stateDumpFileDescriptor> _ => STFILEDESCR </stateDumpFileDescriptor>

    rule <k> #closeStateDumpFile()
          => #close(STFILEDESCR) ...
        </k>
        <stateDumpFileDescriptor> STFILEDESCR => .FileDescr </stateDumpFileDescriptor>
      requires STFILEDESCR =/=K .FileDescr
      
endmodule
```