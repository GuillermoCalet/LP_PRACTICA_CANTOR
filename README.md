# Intèrpret Cantor LP

Implementació en Python 3 d'un intèrpret per al llenguatge cantorià de la
pràctica de LP. El llenguatge treballa només amb nombres naturals i totes les
funcions tenen un únic paràmetre natural i retornen un natural.

Per representar parelles i llistes s'utilitza la funció d'aparellament de
Cantor:

```python
pi(x, y) = ((x + y) * (x + y + 1)) // 2 + y
```

Per exemple, l'entrada:

```text
1 3 2
```

es codifica com:

```text
pi(1, pi(3, 2)) = 188
```

## Requisits

- Python 3.10 o superior
- Java, per executar el jar local d'ANTLR
- GNU Make
- `antlr4-python3-runtime==4.13.2`

El projecte inclou `antlr-4.13.2-complete.jar`, de manera que `make` pot generar
el parser sense descarregar cap eina addicional.

## Instal·lació i execució

Instal·la el runtime de Python d'ANTLR en el mateix `python3` amb què
executaràs l'intèrpret:

```bash
python3 -m pip install antlr4-python3-runtime==4.13.2
```

També es pot fer dins d'un entorn virtual:

```bash
python3 -m venv lp
source lp/bin/activate
make install
```

Genera els fitxers d'ANTLR:

```bash
make
```

Executa un programa Cantor:

```bash
echo "6 2 13" | python3 cantor.py tests/add3.cantor
```

Sortida esperada:

```text
21
```

Si s'utilitza l'entorn virtual, primer cal activar-lo:

```bash
source lp/bin/activate
echo "6 2 13" | python3 cantor.py tests/add3.cantor
```

L'entrada i la sortida es fan per `stdin` i `stdout`, així que també es pot
executar amb redireccions:

```bash
python3 cantor.py tests/add3.cantor < tests/add3.inp > sortida.txt
```

## Llenguatge implementat

Un programa Cantor pot contenir directives i definicions:

```text
main nom_funcio
extended
import nom_sense_extensio

define nom_funcio
    [documentacio]
    expressio
```

Les funcions predefinides del mode bàsic són:

- `k_1`: funció constant 1.
- `id`: identitat.
- `add`: rep `<x.y>` i retorna `x + y`.
- `mul`: rep `<x.y>` i retorna `x * y`.
- `diff`: rep `<x.y>` i retorna `max(0, x - y)`.

Les expressions del mode bàsic són:

- `pair f g`: donada una entrada `x`, retorna `<f(x).g(x)>`.
- `comp f g`: donada una entrada `x`, retorna `f(g(x))`.
- `mu f`: cerca el primer `k >= 0` tal que `f(<x.k>) != 0`.

El mode estès s'activa amb la directiva `extended` i afegeix:

- `fst`: primera projecció d'una parella.
- `snd`: segona projecció d'una parella.
- `compair f g h`: abreviatura de `comp f (pair g h)`.
- `primrec f g h`: recursió primitiva simplificada.

En `primrec`, el runtime calcula els valors `s(0), ..., s(x)` en ordre. El pas
recursiu `h` rep `<i.historial>`, on `historial` és la llista codificada dels
resultats anteriors. El valor retornat per la funció és `s(x)`, tal com fan els
exemples de factorial i fibonacci.

## Tasques i exercicis inclosos

Els programes de prova dins de `tests/` cobreixen les tasques demanades:

- Nucli bàsic: `suma.cantor`, `anterior.cantor`, `core.cantor`.
- Importació: `signe.cantor` i els exercicis que reutilitzen funcions amb
  `import`.
- Booleans: `booleans.cantor`, amb `and`, `or` i `not`.
- Mode estès i `compair`: `add3.cantor`.
- Relacionals: `relationals.cantor`, amb `lt`, `gt`, `eq` i `neq`. També hi ha
  `relacionals.cantor` com a àlies per als exemples escrits en català.
- Minimització `mu`: `div.cantor` i `arithmetic.cantor`, amb `div`, `mod` i
  `even`.
- Recursió primitiva: `factorial.cantor` i `fibonacci.cantor`.
- Condicionals amb funcions: `max_min.cantor`, amb `max`, `min`, `cond` i
  `max2`.

## Estructura

```text
LP_PRACTICA_CANTOR/
├── README.md
├── Makefile
├── cantor.g4
├── cantor.py
├── loader.py
├── runtime.py
├── errors.py
├── test.txt
├── tests/
└── antlr-4.13.2-complete.jar
```

- `cantor.py`: punt d'entrada. Llegeix arguments, `stdin`, codifica l'entrada i
  imprimeix el resultat.
- `loader.py`: carrega fitxers `.cantor`, resol imports, visita l'arbre d'ANTLR,
  valida el programa i construeix les funcions executables.
- `runtime.py`: implementa `pi`, `unpi`, la codificació d'entrada, les funcions
  predefinides i els constructors `pair`, `comp`, `mu`, `compair` i `primrec`.
- `errors.py`: excepcions controlades i listener d'errors sintàctics d'ANTLR.
- `cantor.g4`: gramàtica del llenguatge.

Els fitxers generats per ANTLR (`cantorLexer.py`, `cantorParser.py`,
`cantorVisitor.py`, `*.tokens`, `*.interp`) no s'han d'editar ni incloure com a
codi font manual; es creen amb `make`.

## Decisions de disseny

La implementació separa l'entrada de terminal, la càrrega del programa i el
runtime matemàtic. Això manté petit el punt d'entrada i facilita provar les
peces importants per separat.

ANTLR s'utilitza només per a l'anàlisi lèxica i sintàctica. La gramàtica
`cantor.g4` defineix les directives (`main`, `import`, `extended`) i les
expressions del llenguatge (`pair`, `comp`, `mu`, `compair`, `primrec`). Després,
el visitor converteix l'arbre sintàctic en una representació intermèdia formada
per directives i definicions de funcions.

Les definicions de l'usuari es guarden primer com a dades i després es resolen
en una segona fase. Això permet referències cap endavant, detectar funcions
desconegudes, evitar redefinir primitives i informar de cicles entre
definicions.

Els imports es resolen de manera relativa al fitxer que fa l'`import`. El `main`
efectiu sempre és el del fitxer executat; els `main` dels fitxers importats no
substitueixen el principal.

El mode `extended` és global per a tots els fitxers carregats. Si algun fitxer
inclou la directiva, queden disponibles `fst`, `snd`, `compair` i `primrec` per
al programa carregat.

Les funcions Cantor es representen internament com a funcions de Python
`natural -> natural`. Els constructors `pair`, `comp`, `mu`, `compair` i
`primrec` creen noves funcions Python a partir de les funcions ja resoltes.
Això fa que l'avaluació del programa principal sigui simplement aplicar la
funció `main` al natural codificat de l'entrada.

No s'utilitzen llibreries externes a banda del runtime Python d'ANTLR. La resta
del codi fa servir només la llibreria estàndard de Python.

## Gestió d'errors

Els errors de sintaxi produïts per ANTLR es recullen amb un listener propi a
`errors.py`. Així s'evita que ANTLR imprimeixi missatges directament i es pot
mostrar un error amb el fitxer, la línia i la columna.

`cantor.py` captura totes les excepcions pròpies de l'intèrpret (`CantorError`)
i les mostra per `stderr` amb el prefix `Error:`. També captura qualsevol altra
excepció inesperada per evitar que el programa acabi amb un traceback sense
control. Quan hi ha error, el programa retorna codi de sortida `1`; quan
l'execució és correcta, imprimeix el resultat per `stdout` i retorna `0`.

Tot i que l'enunciat assumeix que no hi haurà errors semàntics, la
implementació també comprova alguns casos per donar missatges més clars:
fitxers inexistents, imports que no es poden carregar, funcions desconegudes,
definicions duplicades, ús de `compair` o `primrec` sense `extended`, cicles
entre definicions i entrades que no són nombres naturals.

## Tests

Executa tots els tests:

```bash
make test
```

El target executa:

- els programes `tests/*.cantor` amb les seves entrades `.inp` i sortides
  esperades `.out`;
- els doctests de `test.txt`, que comproven `pi`, `unpi`, la codificació
  d'entrada i alguns programes representatius.

També es poden executar per separat:

```bash
make examples
make doctest
```

