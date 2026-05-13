# Intèrpret Cantor LP

## Què és?

Aquest projecte és un intèrpret en Python 3 per a un llenguatge minimalista
basat en les funcions d'aparellament de Cantor.

El llenguatge treballa amb nombres naturals. Cada funció rep exactament un
nombre natural i retorna exactament un nombre natural. Les llistes i les
parelles es codifiquen amb la funció d'aparellament de Cantor, de manera que un
programa pot rebre diversos valors d'entrada a través de `stdin`.

L'intèrpret utilitza ANTLR per generar el lexer, el parser i el visitor a partir
de `cantor.g4`.

Exemple:

```bash
make
echo "6 2 13" | python3 cantor.py tests/add3.cantor
```

Sortida esperada:

```text
21
```

## Per què l'he de fer?

Aquest projecte correspon a una pràctica universitària de Llenguatges de
Programació. L'objectiu és mostrar com es pot definir un llenguatge petit amb
una gramàtica, analitzar-lo amb ANTLR i avaluar-lo amb un runtime clar.

La pràctica treballa idees importants com:

- disseny de sintaxi amb ANTLR;
- interpretació d'un llenguatge funcional petit;
- codificació de parelles amb Cantor;
- imports entre fitxers font;
- funcions predefinides;
- minimització amb `mu`;
- recursivitat primitiva simplificada amb `primrec`;
- gestió clara d'errors.

## Qui l'hauria d'utilitzar?

Aquest repositori està pensat per a:

- estudiants que han d'executar i entendre la pràctica del llenguatge Cantor;
- professors o avaluadors que volen revisar la implementació;
- qualsevol persona que vulgui veure un exemple petit d'intèrpret fet amb
  Python i ANTLR.

El codi està escrit perquè sigui llegible i defensable en un examen oral. Les
funcions principals del runtime tenen docstrings explicatius, i aquest README
documenta les decisions de disseny més importants.

## Quan l'hauria d'utilitzar?

S'ha d'utilitzar després de generar el parser d'ANTLR amb:

```bash
make
```

Després es pot executar qualsevol programa `.cantor` amb:

```bash
echo "1 2 3" | python3 cantor.py program.cantor
```

Utilitza `make test` quan vulguis comprovar que l'intèrpret i els programes
d'exemple continuen funcionant correctament.

Utilitza `make clean` abans de preparar el ZIP final, perquè els fitxers
generats per ANTLR no s'han d'entregar.

## On l'he de posar?

Tots els fitxers del projecte han d'estar al directori arrel del repositori.

Fitxers importants:

- `README.md`: documentació del projecte.
- `Makefile`: generació del parser, neteja i tests.
- `cantor.g4`: gramàtica ANTLR.
- `cantor.py`: punt d'entrada per línia de comandes.
- `runtime.py`: aparellament de Cantor, codificació de l'entrada, funcions
  predefinides i constructors de funcions.
- `loader.py`: càrrega de fitxers, imports, parsing, validació i construcció de
  la taula de funcions.
- `errors.py`: excepcions orientades a l'usuari i recollida d'errors sintàctics
  d'ANTLR.
- `tests/`: programes Cantor i exemples d'entrada/sortida.

Els fitxers generats com `cantorLexer.py`, `cantorParser.py`,
`cantorVisitor.py`, `.tokens` i `.interp` es creen amb `make` i no s'han
d'incloure al ZIP final.

## Quins requisits necessita?

Cal tenir Python 3, Java i el runtime de ANTLR per a Python.

El projecte inclou `antlr-4.13.2-complete.jar`. El `Makefile` utilitza primer
aquest `.jar` local per generar el parser, així no depèn d'internet ni del
wrapper `antlr4` instal·lat amb `pip`.

Opcio recomanada amb entorn virtual:

```bash
python3 -m venv lp
source lp/bin/activate
python3 -m pip install antlr4-python3-runtime==4.13.2
```

Opcio amb instal·lacio d'usuari:

```bash
python3 -m pip install --user antlr4-python3-runtime==4.13.2
```

El codi no modifica `sys.path` per buscar entorns locals. Per tant,
`python3 cantor.py ...` s'ha d'executar amb un Python que ja pugui importar
`antlr4`.

## Com l'he d'executar?

Primer genera el parser:

```bash
make
```

Executa un script:

```bash
echo "3 2" | python3 cantor.py tests/anterior.cantor
```

Executa tots els tests:

```bash
make test
```

Si vols usar un Python concret, per exemple el de l'entorn local `lp/`:

```bash
make test PYTHON=lp/bin/python3
```

Neteja els fitxers generats:

```bash
make clean
```

L'intèrpret llegeix l'entrada per `stdin` i escriu el resultat per `stdout`.
Els errors s'escriuen per `stderr` i retornen un codi de sortida diferent de
zero.

## Com es codifica l'entrada?

L'entrada externa és una llista de nombres naturals separats per espais.
L'intèrpret codifica aquesta llista de dreta a esquerra amb la funció
d'aparellament de Cantor.

Funció d'aparellament de Cantor:

```python
pi(x, y) = ((x + y) * (x + y + 1)) // 2 + y
```

Exemples:

```python
pi(47, 32) == 3192
unpi(3192) == (47, 32)
```

Exemple d'entrada:

```text
1 3 2
```

Codificació interna:

```text
pi(3, 2) = 17
pi(1, 17) = 188
```

L'entrada buida es codifica com `0`.

## Com és el llenguatge Cantor?

Un programa pot contenir:

```text
main nom_funcio
extended
import nom_llibreria

define nom_funcio
    [documentacio lliure]
    expressio
```

Expressions bàsiques:

- `pair f g`: retorna `pi(f(x), g(x))`.
- `comp f g`: retorna `f(g(x))`.
- `mu f`: retorna el primer `k >= 0` tal que `f(pi(x, k)) != 0`.

Expressions del mode estès:

- `compair f g h`: equivalent a `comp f (pair g h)`.
- `primrec f g h`: recursivitat primitiva simplificada.

Els comentaris comencen amb `#` i continuen fins al final de línia.

Els blocs de documentació entre `[` i `]` es reconeixen com un únic token
`DOC`. Es guarden en la representació intermèdia, però no afecten l'execució.

## Com es representen internament les funcions?

El carregador treballa en dues fases.

Primer analitza tots els fitxers i guarda cada definició de l'usuari com a
dada:

```python
Definition(name, op, args, doc, source)
```

Després construeix funcions Python executables resolent noms en un diccionari:

```python
functions: dict[str, Callable[[int], int]]
definitions: dict[str, Definition]
```

Aquest disseny en dues fases permet referències cap endavant. Una funció pot
utilitzar una altra funció que apareix més avall en el mateix fitxer `.cantor`.

## Com funcionen les funcions predefinides?

El mode bàsic proporciona:

- `k_1(x) = 1`
- `id(x) = x`
- `add(<x.y>) = x + y`
- `mul(<x.y>) = x * y`
- `diff(<x.y>) = max(0, x - y)`

El mode estès també proporciona:

- `fst(<x.y>) = x`
- `snd(<x.y>) = y`

## Com funcionen els imports?

`import name` carrega `name.cantor` de manera relativa al fitxer que conté
l'import.

Regles:

- el fitxer principal utilitza el seu propi `main`;
- els fitxers importats ignoren el seu `main`;
- els fitxers importats sí que processen els seus propis imports;
- els fitxers ja carregats se salten per evitar bucles d'importació;
- les funcions importades queden disponibles per al fitxer que importa;
- les definicions duplicades es reporten com a errors de validació clars.

La política de redefinició escollida és estricta: redefinir una funció és un
error. És una decisió simple, predictible i evita ambigüitats durant
l'avaluació.

## Com funciona el mode estès?

Si qualsevol fitxer carregat conté:

```text
extended
```

tot el programa carregat s'executa en mode estès.

El mode estès activa:

- `fst`
- `snd`
- `compair`
- `primrec`

Si apareix `compair` o `primrec` sense mode estès, l'intèrpret informa d'un
error de validació en lloc de trencar-se.

## Com funciona `mu`?

`mu f` crea una nova funció `h`.

Per a una entrada `x`, `h(x)` busca linealment:

```text
k = 0, 1, 2, ...
```

fins que troba el primer valor on:

```text
f(pi(x, k)) != 0
```

Llavors retorna aquest `k`.

Hi ha un límit configurable per evitar bucles infinits accidentals:

```bash
CANTOR_MU_LIMIT=200000 echo "17 5" | python3 cantor.py tests/mod.cantor
```

Per defecte el límit és `100000`.

## Com funciona `primrec`?

`primrec f g h` crea una funció que calcula una seqüència de `0` fins a `x`.

Per a cada índex `i`:

- si `f(i) != 0`, el valor és `g(i)`;
- si no, el valor és `h(pi(i, previous_results))`.

El resultat final és la seqüència codificada:

```text
<s(x).<s(x-1)....<s(0).0>>>
```

La representació interna utilitza `0` com a cua buida. Cada nou resultat
s'afegeix al principi:

```text
previous_results = pi(current_value, previous_results)
```

Això és útil perquè:

- `fst(previous_results)` dona `s(i-1)`;
- `fst(snd(previous_results))` dona `s(i-2)`.

Aquesta representació fa que factorial i Fibonacci siguin fàcils d'expressar.

## Com es gestionen els errors?

L'intèrpret captura i informa de:

- errors sintàctics d'ANTLR;
- fitxers inexistents;
- imports inexistents;
- absència de `main`;
- funcions desconegudes;
- definicions duplicades;
- ús d'operadors estesos sense `extended`;
- valors d'entrada invàlids;
- errors d'execució controlats.

El programa no hauria de mostrar tracebacks llargs de Python per a errors
normals d'usuari.

## Com puc provar el projecte?

Executa:

```bash
make test
```

El runner de tests executa cada fitxer `.inp` de `tests/`, busca el programa
`.cantor` amb el mateix nom base i compara el resultat amb el fitxer `.out`
corresponent.

Exemples inclosos:

- `tests/anterior.cantor`
- `tests/add3.cantor`
- `tests/and.cantor`, `tests/or.cantor`, `tests/not.cantor`
- `tests/lt.cantor`, `tests/gt.cantor`, `tests/eq.cantor`,
  `tests/neq.cantor`
- `tests/mod.cantor`, `tests/even.cantor`
- `tests/fibonacci.cantor`
- `tests/factorial.cantor`
- `tests/max.cantor`, `tests/min.cantor`, `tests/cond.cantor`,
  `tests/max2.cantor`

## Com he de preparar el ZIP final?

Abans de crear el ZIP, executa:

```bash
make clean
```

Inclou els fitxers font, la gramàtica, els tests, el README i el Makefile.

No incloguis els fitxers generats per ANTLR:

- `cantorLexer.py`
- `cantorParser.py`
- `cantorVisitor.py`
- `*.tokens`
- `*.interp`

## Limitacions conegudes

- `mu` utilitza un límit de cerca per evitar execucions infinites.
- Els blocs de documentació no poden contenir `]`.
- Els exemples de divisió i mòdul assumeixen que el divisor és positiu.
