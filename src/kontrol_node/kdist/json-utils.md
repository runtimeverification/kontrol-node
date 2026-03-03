Utilities for working with JSON values

```k
requires "json.md"
requires "serialization.md"

module JSON-UTILS
    imports JSON
    imports SERIALIZATION

    // From JSON to K

    syntax JSON ::= #getJSON ( JSONKey, JSON )       [function, symbol(getJSON)]
                  | #getJSON ( JSONKey, JSON, JSON ) [function, symbol(getJSONDefault)]
    // --------------------------------------------------------------------------------

    rule #getJSON( KEY, { KEY : J, _     }, _ ) => J
    rule #getJSON(   _, { .JSONs         }, DEF_VAL ) => DEF_VAL
    rule #getJSON( KEY, { KEY2 : _, REST }, DEF_VAL ) => #getJSON( KEY, { REST }, DEF_VAL )
        requires KEY =/=String KEY2

    rule #getJSON( KEY, J ) => #getJSON( KEY, J, null )

    syntax Int ::= #getInt(JSONKey, JSON)      [function, symbol(getInt)]
                 | #getInt(JSONKey, JSON, Int) [function, symbol(getIntDefault)]
    // -------------------------------------------------------------------------

    rule #getInt( KEY, J ) => {#getJSON( KEY, J )}:>Int
    rule #getInt( KEY, J, DEF_VAL ) => {#getJSON( KEY, J, DEF_VAL )}:>Int

    syntax String ::= #getString(JSONKey, JSON)         [function, symbol(getString)]
                    | #getString(JSONKey, JSON, String) [function, symbol(getStringDefault)]
     // ------------------------------------------------------------------------------------

    rule #getString( KEY, J ) => {#getJSON( KEY, J )}:>String
    rule #getString( KEY, J, DEF_VAL ) => {#getJSON( KEY, J, DEF_VAL )}:>String

    syntax Int ::= #getWord(JSONKey, JSON, Int) [function, symbol(getWord)]
    // --------------------------------------------------------------------

    rule #getWord( KEY, J, DEF_VAL ) => #let RAW = #getJSON( KEY, J ) #in
                                        #if RAW ==K null #then DEF_VAL #else #parseWord( {RAW}:>String ) #fi

    syntax Int ::= #getAddr(JSONKey, JSON, Int) [function, symbol(getAddr)]
    // --------------------------------------------------------------------
    
    rule #getAddr( KEY, J, DEF_VAL ) => #let RAW = #getJSON( KEY, J ) #in
                                        #if RAW ==K null #then DEF_VAL #else #parseAddr( {RAW}:>String ) #fi

    syntax Account ::= #getAccount(JSONKey, JSON, Account) [function, symbol(getAccount)]
    // ----------------------------------------------------------------------------------
    
    rule #getAccount( KEY, J, DEF_VAL ) => #let RAW = #getJSON( KEY, J ) #in
                                        #if RAW ==K null #then DEF_VAL #else #parseAddr( {RAW}:>String ) #fi

    syntax Bytes ::= #getBytes(JSONKey, JSON, Bytes) [function, symbol(getBytes)]
    // --------------------------------------------------------------------------
    
    rule #getBytes( KEY, J, DEF_VAL ) => #let RAW = #getJSON( KEY, J ) #in
                                        #if RAW ==K null #then DEF_VAL #else #parseByteStack( {RAW}:>String ) #fi

    // From K to JSON

    syntax String ::= intToHex(Int)                  [function, total, symbol(intToHex)]
                    | intToHex(Int, length: Int)     [function, total, symbol(intToHexLen)]
                    | bytesToHex(Bytes)              [function, total, symbol(bytesToHex)]
                    | bytesToHex(Bytes, length: Int) [function, total, symbol(bytesToHexLen)]
                    | addrToHex(Int)                 [function, symbol(addrToHex)]
                    | uint256ToHex(Int)              [function, symbol(uint256ToHex)]
    // ------------------------------------------------------------------------------

    rule bytesToHex( BYTES ) => "0x" +String Bytes2Hex( BYTES ) 

    rule bytesToHex( BYTES, LEN ) => "0x" +String Bytes2Hex( padLeftBytes(BYTES, LEN, 0) )

    rule intToHex( A:Int ) => "0x" +String Base2String(A, 16)
        requires A >=Int 0
    rule intToHex( A:Int ) => "-0x" +String Base2String( absInt(A), 16) [owise]

    rule intToHex( A:Int, LEN:Int ) => "0x" +String Bytes2Hex( Int2Bytes( LEN, A, BE) )
        requires A >=Int 0
    rule intToHex( A:Int, LEN:Int ) => "-0x" +String Bytes2Hex( Int2Bytes( LEN, absInt(A), BE) ) [owise]

    rule addrToHex( A:Int ) => intToHex( A, 20 )
    rule uint256ToHex( A:Int ) => intToHex( A, 32 )

    syntax JSON ::= accountToHex(Account)            [function, symbol(accountToHex)]
    // ------------------------------------------------------------------------------

    rule accountToHex( .Account ) => null
    rule accountToHex( ADDR:Int ) => addrToHex( ADDR )

endmodule
```