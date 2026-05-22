
// Nombre de la gramática. ANTLR generará cantorLexer.py, cantorParser.py
// y cantorVisitor.py a partir de este archivo.
grammar cantor;

// Regla inicial: un programa es una secuencia de sentencias hasta EOF.
program
    : statement* EOF
    ;

// Una sentencia puede ser una directiva o una definición.
statement
    : mainDecl
    | importDecl
    | extendedDecl
    | definition
    ;

// main nombre_funcion
mainDecl
    : MAIN NAME
    ;

// import nombre_sin_extension
importDecl
    : IMPORT NAME
    ;

// extended
extendedDecl
    : EXTENDED
    ;

// define nombre
//     [documentacion]
//     expresion
definition
    : DEFINE NAME DOC expression
    ;

// Las alternativas con #Nombre generan metodos visitNombre en el visitor.
expression
    : PAIR NAME NAME                 # PairExpr
    | COMP NAME NAME                 # CompExpr
    | MU NAME                        # MuExpr
    | COMPAIR NAME NAME NAME         # CompairExpr
    | PRIMREC NAME NAME NAME         # PrimrecExpr
    ;

// Palabras reservadas del lenguaje.
MAIN: 'main';
IMPORT: 'import';
EXTENDED: 'extended';
DEFINE: 'define';
PAIR: 'pair';
COMP: 'comp';
MU: 'mu';
COMPAIR: 'compair';
PRIMREC: 'primrec';

// Bloque de documentacion. Acepta cualquier caracter excepto ].
DOC: '[' ~']'* ']';

// Identificadores de funciones e imports.
NAME: [a-zA-Z_][a-zA-Z_0-9]*;

// Comentarios desde # hasta final de linea.
COMMENT: '#' ~[\r\n]* -> skip;

// Espacios, tabs y saltos de linea se ignoran.
WS: [ \t\r\n]+ -> skip;

// Cualquier otro carácter produce un token inesperado y acaba en error
// sintáctico controlado por el listener del intérprete.
LEXICAL_ERROR: .;
