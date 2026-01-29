Utilities for working with JSON values

```k
requires "json.md"
requires "serialization.md"

module JSON-UTILS
    imports JSON
    imports SERIALIZATION

    // From JSON to K

    syntax JSON ::= #getJSON ( JSONKey, JSON )       [function]
                  | #getJSON ( JSONKey, JSON, JSON ) [function]

    rule #getJSON( KEY, { KEY : J, _     }, _ ) => J
    rule #getJSON(   _, { .JSONs         }, DEF_VAL ) => DEF_VAL
    rule #getJSON( KEY, { KEY2 : _, REST }, DEF_VAL ) => #getJSON( KEY, { REST }, DEF_VAL )
        requires KEY =/=String KEY2

    rule #getJSON( KEY, J ) => #getJSON( KEY, J, null )

    syntax Int ::= #getInt(JSONKey, JSON) [function]
                 | #getInt(JSONKey, JSON, Int) [function]
    rule #getInt( KEY, J ) => {#getJSON( KEY, J )}:>Int
    rule #getInt( KEY, J, DEF_VAL ) => {#getJSON( KEY, J, DEF_VAL )}:>Int

    syntax String ::= #getString(JSONKey, JSON) [function]
                    | #getString(JSONKey, JSON, String) [function]
    rule #getString( KEY, J ) => {#getJSON( KEY, J )}:>String
    rule #getString( KEY, J, DEF_VAL ) => {#getJSON( KEY, J, DEF_VAL )}:>String

    syntax Int ::= #getWord(JSONKey, JSON, Int) [function]
    rule #getWord( KEY, J, DEF_VAL ) => #let RAW = #getJSON( KEY, J ) #in
                                        #if RAW ==K null #then DEF_VAL #else #parseWord( {RAW}:>String ) #fi

    syntax Int ::= #getAddr(JSONKey, JSON, Int) [function]
    rule #getAddr( KEY, J, DEF_VAL ) => #let RAW = #getJSON( KEY, J ) #in
                                        #if RAW ==K null #then DEF_VAL #else #parseAddr( {RAW}:>String ) #fi

    syntax Bytes ::= #getBytes(JSONKey, JSON, Bytes) [function]
    rule #getBytes( KEY, J, DEF_VAL ) => #let RAW = #getJSON( KEY, J ) #in
                                        #if RAW ==K null #then DEF_VAL #else #parseByteStack( {RAW}:>String ) #fi

    // From K to JSON

    syntax String ::= intToHex(Int)     [function, total]
                    | bytesToHex(Bytes) [function, total]

    rule bytesToHex( BYTES ) => "0x" +String Bytes2Hex( BYTES ) 
    rule intToHex( A:Int ) => "0x" +String Base2String(A, 16)
        requires A >=Int 0
    rule intToHex( A:Int ) => "-0x" +String Base2String( absInt(A), 16) [owise]

endmodule
```