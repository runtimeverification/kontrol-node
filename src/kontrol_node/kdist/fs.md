
```k
module FILE-SYSTEM
    imports STRING
    imports INT
    imports K-IO

    syntax IOString ::= #readFile( String )     [function, strict, impure]

    syntax K ::= #writeFile( String, String ) [function, strict, impure]
               | #appendFile( String, String) [function, strict, impure]

    rule #readFile( FILE )
          => #let HANDLE = #open( FILE, "r" ) #in
             #let RESULT = #read(HANDLE, 0) #in
             #let _ = #close(HANDLE) #in
             RESULT

    rule #writeFile( FILE, CONTENTS )
          => #let HANDLE = #open( FILE, "W") #in
             #let RESULT = #write(HANDLE, CONTENTS) #in
             #let _ = #close(HANDLE) #in
             RESULT

    rule #appendFile( FILE, CONTENTS )
          => #let HANDLE = #open( FILE, "a" ) #in
             #let RESULT = #write(HANDLE, CONTENTS) #in
             #let _ = #close(HANDLE) #in
             RESULT

endmodule
```