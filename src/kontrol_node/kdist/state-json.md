# JSON encoding of state snapshots

This module defines rules to save and load vm machine snapshots in a JSON
format from disk. Since there is no standardized way for encoding state
snapshots, we aim for compatbility with Anvil's `anvil_dumpState` format.

Notice, that Anvil's format doesn't is incomplete, for example it does not
contain the chain_id.

```k
requires "foundry.md"
requires "driver.md"
requires "fs.md"
requires "json.md"
requires "config.md"

module STATE-JSON
    imports EVM
    imports FOUNDRY
    imports EVM-TRACING
    imports JSON
    imports STRING
    imports MAP
    imports K-IO
    imports FILE-SYSTEM
    imports SERIALIZATION
    imports KONTROL-NODE-CONFIG

    syntax KItem ::= #saveStateDump( String )
                   | #loadStateDump( String, Int )

```

===============================================================================
JSON ENCODING

This section defines rule to create a StateDump JSON object from the current
K configuration.

```k

    syntax KItem ::= #createStateDump()         // Internal use only, create a StateDump from the current configuration
                   | #stLoad( JSON )            // Internal use only, populate a StateDump into the current configuration (reverse of #createStateDump)
                   | #StateDump( JSON )         // Internal use only, wrap a StateDump JSON object to disambiguate it from other KItems containing JSON data
                   | #writeStateDump( String )  // Internal use only, write a StateDump to disk

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
    ) => intToHex(ACC_ID) : {
        "balance": intToHex( ACC_BALANCE ),
        "code": codeToJson( ACC_CODE ),
        "storage": storageToJSON( ACC_STORAGE ),
        "nonce" : ACC_NONCE
    }

    rule accountsCellToJSON( ACCS ) => { accountsCellToJSONs( ACCS, .JSONs ) }
    rule accountsCellToJSONs( <accounts> <account> ACC </account> ACCS:Bag </accounts>, ACCU)
            => accountsCellToJSONs( <accounts> ACCS </accounts>, (accountCellToJSON( <account> ACC </account> ) , ACCU) ) 
    rule accountsCellToJSONs( <accounts> .Bag </accounts>, ACCU ) => ACCU [owise]

    rule <k> #createStateDump()
        => #StateDump({
            "bestBlockNumber": BLOCK_NUMBER,
            "block": {
                "number": intToHex( BLOCK_NUMBER ),
                "beneficiary": intToHex( BLOCK_COINBASE ),
                "timestamp": intToHex( BLOCK_TIMESTAMP ),
                "gas_limit": BLOCK_GAS_LIMIT,
                "basefee": BLOCK_BASE_FEE,
                "difficulty": intToHex( BLOCK_DIFFICULTY ),
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

===============================================================================
JSON DECODING

This secion defines rules to load a StateDump JSON object into the current
K configuration.

It's very similar to the [state-utils.md](https://github.com/runtimeverification/evm-semantics/blob/master/kevm-pyk/src/kevm_pyk/kproj/evm-semantics/state-utils.md)
module defined in `evm-semantics`, but targets specifically the Anvil's
StateDump format - not the ethereum/test format.

```k

    syntax KItem ::= #stLoad( JSON )
                   | #stLoadBlock( JSON )
                   | #stLoadBlob( JSON )
                   | #stLoadAccounts( JSON )
                   | #stLoadAccount( Int, JSON )
                   | #stLoadStorage( Int, Map )

    // ------------
    // StateDump root object

    // Finished decoding StateDump
    rule <k> #stLoad( { .JSONs } ) => .K ... </k>
 
    // Break up the StateDump into it's compnents
    rule <k> #stLoad( { KEY : VALUE , REST } ) => #stLoad( KEY : VALUE ) ~> #stLoad( { REST } )... </k>

    // Handle components
    rule <k> #stLoad( "best_block_number" : _        ) => .K ... </k> // TODO: Do we need this?
    rule <k> #stLoad( "block"             : BLOCK    ) => #stLoadBlock( BLOCK ) ... </k>
    rule <k> #stLoad( "accounts"          : ACCOUNTS ) => #stLoadAccounts( ACCOUNTS ) ... </k>

    // Discard all other components
    rule <k> #stLoad( _:String : _VAL ) => .K ...</k> [owise]

    // ------------
    // Block

    // Finished block
    rule <k> #stLoadBlock( { .JSONs } ) => .K ... </k>

    // Break up a block into it's components
    rule <k> #stLoadBlock( { KEY : VALUE, REST } ) => #stLoadBlock( KEY : VALUE ) ~> #stLoadBlock( { REST } ) ... </k>

    // Handle components
    rule <k> #stLoadBlock( "number"      : VAL ) => .K ... </k> <number>     _ => #parseWord( VAL ) </number>
    rule <k> #stLoadBlock( "beneficiary" : VAL ) => .K ... </k> <coinbase>   _ => #parseWord( VAL ) </coinbase>
    rule <k> #stLoadBlock( "timestamp"   : VAL ) => .K ... </k> <timestamp>  _ => #parseWord( VAL ) </timestamp>
    rule <k> #stLoadBlock( "gas_limit"   : VAL ) => .K ... </k> <gasLimit>   _ => VAL </gasLimit>
    rule <k> #stLoadBlock( "basefee"     : VAL ) => .K ... </k> <baseFee>    _ => VAL </baseFee>
    rule <k> #stLoadBlock( "difficulty"  : VAL ) => .K ... </k> <difficulty> _ => #parseWord( VAL ) </difficulty>
    rule <k> #stLoadBlock( "blob_excess_gas_and_price": VAL ) => #stLoadBlob( VAL )... </k>

    // Discard all other components
    rule <k> #stLoadBlock( _:String : _VAL ) => .K ...</k> [owise] 

    // ------------
    // Blob

    // Finished blob
    rule <k> #stLoadBlob( { .JSONs } )=> .K ... </k>

    // Break up a blob into it's components
    rule <k> #stLoadBlob( { KEY : VALUE, REST } ) => #stLoadBlob( KEY : VALUE ) ~> #stLoadBlob( { REST } ) ... </k>

    // Handle components
    rule <k> #stLoadBlob( "excess_blob_gas" : VAL ) => .K ... </k> <excessBlobGas> _ => VAL </excessBlobGas>
    rule <k> #stLoadBlob( "blob_gasprice"   : VAL ) => .K ... </k> <blobGasUsed>   _ => VAL </blobGasUsed>
    
    // Discard all other components
    rule <k> #stLoadBlob( _:String : _VAL) => .K ...</k> [owise] 

    // ------------
    // Accounts

    rule <k> #stLoadAccounts( { .JSONs } ) => .K ... </k>
    rule <k> #stLoadAccounts( { KEY : VALUE, REST } ) => #stLoadAccounts( KEY : VALUE ) ~> #stLoadAccounts( { REST } ) ... </k>

    rule <k> #stLoadAccounts( ACCT_ID : ACCT_DATA )
          => #newAccount( #parseAddr( ACCT_ID ) )
          ~> #stLoadAccount( #parseAddr( ACCT_ID ), ACCT_DATA ) ...
         </k>

    // ------------
    // Account

    // Finished account
    rule <k> #stLoadAccount( _, { .JSONs } ) => .K ... </k>

    // Break up an account into it's components
    rule <k> #stLoadAccount( ACCT_ID, { KEY : VALUE, REST } )
          => #stLoadAccount(ACCT_ID, KEY : VALUE)
          ~> #stLoadAccount(ACCT_ID, { REST } )
          ... </k>

    // Handle components
    rule <k> #stLoadAccount(ACCT_ID, "nonce" : VAL) => .K ... </k>
         <account>
            <acctID> ACCT_ID  </acctID>
            <nonce>  _ => VAL </nonce>
            ...
        </account>
    rule <k> #stLoadAccount(ACCT_ID, "balance" : VAL) => .K ... </k>
         <account>
            <acctID>  ACCT_ID  </acctID>
            <balance> _ => #parseWord( VAL ) </balance>
            ...
        </account>
    rule <k> #stLoadAccount(ACCT_ID, "code" : VAL) => .K ... </k>
         <account>
            <acctID> ACCT_ID  </acctID>
            <code>   _ => parseByteStack( VAL ) </code>
            ... 
         </account>
    rule <k> #stLoadAccount( ACCT_ID, "storage" : VAL) => #stLoadStorage( ACCT_ID, #parseMap( VAL ) ) ... </k>
    
    // Discard all other components
    rule <k> #stLoadAccount( _, _ : _VAL ) => .K ...</k> [owise]

    // ------------
    // Account Storage

    rule <k> #stLoadStorage( ACCT_ID, ST ) => .K ... </k>
         <account>
            <acctID> ACCT_ID </acctID>
            <storage>     _ => ST </storage>
            <origStorage> _ => ST </origStorage>
            ...
        </account>

```

===============================================================================
Persisting a StateDump to Disk

This seciont defines rules to write a StateDump JSON object to disk.

```k

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

    rule <k> #loadStateDump( IO_DIR, BLOCK_NUMBER )
          => #let CONTENTS:IOString = #readFile( #stateDumpFile( IO_DIR, BLOCK_NUMBER ) )
              #in #stLoad( String2JSON( {CONTENTS}:>String ) )
              ...
         </k>


endmodule
```