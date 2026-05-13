grammar cantor;

program
    : statement* EOF
    ;

statement
    : mainDecl
    | importDecl
    | extendedDecl
    | definition
    ;

mainDecl
    : MAIN NAME
    ;

importDecl
    : IMPORT NAME
    ;

extendedDecl
    : EXTENDED
    ;

definition
    : DEFINE NAME DOC expression
    ;

expression
    : PAIR NAME NAME                 # PairExpr
    | COMP NAME NAME                 # CompExpr
    | MU NAME                        # MuExpr
    | COMPAIR NAME NAME NAME         # CompairExpr
    | PRIMREC NAME NAME NAME         # PrimrecExpr
    ;

MAIN: 'main';
IMPORT: 'import';
EXTENDED: 'extended';
DEFINE: 'define';
PAIR: 'pair';
COMP: 'comp';
MU: 'mu';
COMPAIR: 'compair';
PRIMREC: 'primrec';

DOC: '[' ~']'* ']';
NAME: [a-zA-Z_][a-zA-Z_0-9]*;

COMMENT: '#' ~[\r\n]* -> skip;
WS: [ \t\r\n]+ -> skip;
