
```k
module FILE-SYSTEM
    imports STRING
    imports INT
    imports K-IO

    
    // When this number is too big the llvm-backend get's stuck
    // Not sure what's the biggest number accepted by the backend
    // but for the purpose of the kontrol-node 100mb should be
    // sufficient.
    syntax Int ::= "MAX_READ" [alias]
    // ------------------------------

    rule MAX_READ => 104857600 // 100mb 

    syntax IOString ::= #readFile( String )   [function, strict, impure, symbol(readFile)]
    // -----------------------------------------------------------------------------------

    syntax K ::= #writeFile( String, String ) [function, strict, impure, symbol(writeFile)]
               | #appendFile( String, String) [function, strict, impure, symbol(appendFile)]
    // -------------------------------------------------------------------------------------

    rule #readFile( FILE )
          => #let HANDLE:IOInt = #open( FILE, "r" ) #in
             #let RESULT = #read({HANDLE}:>Int, MAX_READ) #in
             #let _ = #close({HANDLE}:>Int) #in
             RESULT

    rule #writeFile( FILE, CONTENTS )
          => #let HANDLE:IOInt = #open( FILE, "w") #in
             #let RESULT = #write({HANDLE}:>Int, CONTENTS) #in
             #let _ = #close({HANDLE}:>Int) #in
             RESULT

    rule #appendFile( FILE, CONTENTS )
          => #let HANDLE:IOInt = #open( FILE, "a" ) #in
             #let RESULT = #write({HANDLE}:>Int, CONTENTS) #in
             #let _ = #close({HANDLE}:>Int) #in
             RESULT

endmodule
```