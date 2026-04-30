# Pràctica LP: funcions de Cantor

Aquesta pàgina descriu la pràctica de GEI-LP (edició 2025-2026 Q2). En aquesta pràctica has d'escriure un intèrpret d'un llenguatge de programació minimalista que té com a base funcions simples d'un únic paràmetre i les [funcions d'aparellament de Cantor](https://en.wikipedia.org/wiki/Pairing_function) utilitzant Python i Antlr. 

```
# això és un comentari
main signe  # funció main

define aparella_1
    [Aparella l'entrada x amb 1: <x.1> ]
    pair id k_1

define anterior
    [Anterior amb limit 0]
    comp diff aparella_1

define aparella_ant
    [Aparella x amb el seu predecessor]
    pair id ant

define signe
    [Signe: 0 -> 0, resta -> 1]
    comp diff aparella_ant
```

En aquesta pràctica haureu d'implementar aquest llenguatge cantorià minimalista i programar alguns scripts bàsics en el llenguatge.

## Tasca 1: nucli bàsic

L'objectiu d'aquesta tasca és tenir el nucli bàsic en funcionament.

### Codificació de l'entrada

En el nostre llenguatge cantorià només treballarem amb nombres naturals. Necessitarem dues funcions prèvies `pi` (aparellament) i `unpi` (inversa). Mireu [Pairing function](https://en.wikipedia.org/wiki/Pairing_function) per trobar la definició i exemples del funcionament d'aquestes funcions.

Els aparellaments els codificarem com `<x.y>` en tot el document.

Exemples de funcionament:

```python3
>>> pi(47, 32)
3192
>>> unpi(3192)
(47, 32)
```

L'entrada dels nostres scripts vindrà donada per una llista de naturals donada per l'entrada estàndard en una única línia separada per espais. Codificarem la llista aparellant de dreta a esquerra amb la funció de projecció `pi`. En cas de tenir una llista buida la codificarem com a zero.

**Exemple**:

L'entrada "1 3 2" correspon a la llista python `[1, 3, 2]` que haurà de ser codificada com a 188.

```python3
>>> pi(3, 2)
17
>>> pi(1, 17)
188
```

Aquest nombre serà el valor d'entrada de la funció que correspongui. 

### Funcions disponibles bàsiques

El llenguatge haurà de disposar d'algunes funcions predefinides:

- `k_1`: la funció constant 1

- `id`: la funció identitat

- `add`: donada una parella codificada `<x.y>`, retorna `x+y`

- `mul`: donada una parella codificada `<x.y>`, retorna `x*y`

- `diff`: donada una parella codificada `<x.y>`, retorna `max(0, x-y)`

### Sintaxi bàsica

Un script estarà format per una directiva per definir la funció principal i per la definició de diverses funcions (o no).
L'exemple següent crida a la funció suma sense declarar cap funció:

```
# suma.cantor
main add  # directiva per declarar quina és la funció principal
```

Execució:

```
$ echo "3 2" | python3 cantor.py suma.cantor
5 
```

La definició de funcions es farà amb la sintaxi:

```
define nom_funció
    [documentació de la funció en llenguatge natural]
    pair_o_comp funció_1 funció_2
```

On el codi de la funció només pot ser la crida a una de les funcions següents:

- `pair f g`: donada l'entrada `x`, retorna `<f(x).g(x)>`

- `comp f g`: donada l'entrada `x`, retorna `f(g(x))`

**Exemple**

```
# anterior.cantor
main anterior

define aparella_amb_1
    [Aparella l'entrada x amb 1: <x.1> ]
    pair id k_1

define anterior
    [Anterior amb limit 0]
    comp diff aparella_amb_1
```

Execució:

```
$ echo "3" | python3 cantor.py anterior.cantor
2
```

## Tasca 2: importació

L'objectiu d'aquesta segona tasca serà la d'afegir la funcionalitat d'importació de nous scripts. Afegirem la comanda d'importació entre les directives i la definició de funcions amb la sintaxi:

```
import nom_sense_extensió
```

La vostra pràctica haurà d'importar l'arxiu sense processar les directives de l'script importat, però si les importacions.

**Exemple**:

```
# signe.cantor
main signe

import anterior

define aparella_amb_anterior
    [Aparella x amb el seu predecessor]
    pair id anterior

define signe
    [Signe: 0 per 0, 1 per la resta]
    comp diff aparella_amb_anterior
```

Execució:

```
$ echo "6" | python3 cantor.py signe.cantor
1
```

### Exercici: booleans

Tenint en compte que codifiquem el fals i cert com a 0 i 1 respectivament, doneu un script cantorià amb la implementació de les funcions booleanes: `and`, `or` i `not`.

## Tasca 3: funció compair i mode extended

L'objectiu d'aquesta tasca és afegir dues funcions bàsiques (`fst`i `snd`) i activar un mode "extès" que admeti una funció nova `compair`, composició de `comp` i `pair`.

Afegir la possibilitat d'utilitzar les funcions bàsiques:

- `fst`: donada una parella codificada `<x.y>`, retorna el primer element `x`

- `snd`: donada una parella codificada `<x.y>`, retorna el primer element `y`

Afegiu una directiva `extended` a la gramàtica i la pràctica en general que permeti (o no) l'ús de la funció `compair` i afegiu aquesta funció a la pràctica:

- `compair f g h = comp f (pair g h)`

**Exemple**:

```
# add3.cantor
main add3
extended

define third
    [3er element d'una seqüència de 3 elements]
    comp snd snd

define second
    [2on element d'una seqüència de 3 elements]
    comp fst snd

define add23
    [2on + 3er]
    compair add second third

define add3
    [Suma de seqüència de tres elements]
    compair add fst add23
```

Execució:

```
$ echo "6 2 13" | python3 cantor.py add3.cantor
21
```

### Exercici: relacionals

Doneu un script cantorià amb la implementació de les funcions relacionals: `lt`, `gt`, `eq` i `neq`.

## Tasca 4: recursivitat en mode bàsic

La recursivitat bàsica la tractarem amb la minimització μ. 

L'operador de minimització rep un predicat com a paràmetre i crea una funció `h = mu f` que implementa una cerca lineal sobre f. Concretament, `h(x)` va calculant iterativament la seqüència `f(<x.0>)`, `f(<x.1>)`, `f(<x.2>)` fins trobar un valor `k` que satisfà `f(<x.k>)`: aleshores `h(x)=k`.

**Exemple**: podem utilitzar la minimització μ per definir la divisió entera. Per fer-ho, formalitzarem la divisió com buscar la mínima `q` que satisfà `y*(q+1) > x`.  L'entrada de la funció `h` serà la parella `<x.y>` i la funció de test treballarà amb `<<x.y>.q>`.

```
# div.cantor
main div
extended
import relacionals

define vx
    [x a <<x.y>.q>]
    comp fst fst

define vy
    [y a <<x.y.q>]
    comp snd fst

define q1
    [q+1 a <<x.y>.q>]
    compair add snd k_1

define yq1
    [y*(q+1) a <<x.y>.q>]
    compair mul vy q1

define test_quocient
    [Test_Quocient per mu(q)-division, y*(q+1) > x a <<x.y>.q>]
    compair gt yq1 vx

define div
    [Quocient de la divisió per cerca lineal]
    mu test_quotient
```

Execució:

```
$ echo "7 2" | python3 cantor.py div.cantor
3
```

### Exercici: mod i even

Doneu un script cantorià amb la implementació de les funcions: `mod` i `even`. 

## Tasca 5: recursivitat en mode extended

L'objectiu d'aquesta tasca és afegir una funció per tractar la recursivitat, més senzilla de formalitzar, per problemes en els que sabem el nombre de passos per resoldre el problema i estàn fortament associats a la sèrie `0, 1, 2,...,x`.

- `primrec f g h`: retorna una funció `s` on `f` és un predicat que ens diu si estem davant del cas base *es_cas_base?*, `g`representa la funció *cas_base* i `h` el pas del *cas_recursiu*. La funció `s` retorna una tupla que conté els valors `s(x), s(x-1), s(x-2), ..., s(1), s(0)` on s'ha aplicat les funcions`g` o `h` a cada valor en funció de si és un cas base o no (si satisfà el predicat `f`). 

**Exemple**: per calcular el factorial, la funció `f` correspon a una que miri si som davant un 0 o no, la funció g és `k_1`(cas base) i la recursiva `h` correspon a multiplicar el resultat anterior `s(i-1)` per l'actual `i`, on `i` és el valor que portem de 0  a `x`.

```
# factorial.cantor

main factorial
extended
import relacionals

define k_0
    [0]
    compair diff k_1 k_1

define segon
    [2on]
    comp fst snd

define is_base
    [zero?]
    compair eq id k_0

define step
    [recursiu fact]
    compair mul fst segon

define factorial
    [x!]
    primrec is_base k_1 step
```

### Exercici: fibonacci

Doneu un script cantorià amb la implementació de la funció de `fibonacci`.

## Tasca 5: condicionals

En tot el documents no hem parlat dels condicionals, però amb el que tenim ja es poden aplicar; no necessitem afegir res al llenguatge. Quan hem d'aplicar temes relacionats amb condicions, apliquem la funció `diff`, com en el cas de la funció `signe`.

### Exercici: max i min

Doneu un script cantorià amb la implementació de la funcions: `max` i `min`. Noteu que es  pot resoldre combinant `add` i `diff`.

### Exercici: condicional tipus if

Doneu un script cantorià amb la implementació de la funcions:

- `cond p a b`: que funcioni tipus `if p then a else b`. En aquest cas us pot anar bé la funció `signe`i us podeu inspirar en la seva implementació.

- `max2`: doneu una implementació del màxim utilitzant la funció `cond`.

## La vostra feina

Heu d'escriure un intèrpret del llenguatge cantorià descrit utilitzant ANTLR i Python. Aquest intèrpret ha de ser capaç de llegir i avaluar les expressions descrites, així com definir i cridar funcions. Heu d'utilitzar ANTLR per escriure la gramàtica i els visitadors necessaris. 

El vostre programa s'ha de preparar amb un cop de `make`. Llavors, el vostre intèrpret s'ha d'invocar amb la comanda `python3 cantor.py` tot passant-li com a paràmetre el nom del fitxer que conté el codi font (l'extensió dels fitxers per programes cantorians és `.cantor`). Per exemple:

```bash
make
echo "1 2 3" | python3 cantor.py script.cantor
```

L'entrada-sortida ha de ser via stdin/stdout. Així es podran utilitzar operadors de redirecció i *pipes*:

```bash
python3 cantor.py exemple.cantor < entrada.txt > sortida.txt
```

### Jocs de proves

El vostre projecte ha d'incloure jocs de proves amb els exercicis proposats. Aquests jocs de proves han de ser fitxers amb extensió `.cantor` que continguin programes en la sintaxi descrita. 

### Llibreries

Utilitzeu `ANTLR` per escriure la gramàtica i l'intèrpret. Podeu utilitzar lliurament qualsevol llibreria **estàndard** de Python. No podeu usar cap altra llibreria no estàndard.

### Errors

Si el programa en Cantor conté errors sintàctics, cal reportar-ho.

En canvi, en aquesta pràctica, suposarem que no es donen mai errors semàntics, de tipus o d'execució. En cas de donar-se, l'efecte del programa és indefinit.

Però la vostra pràctica no ha de petar en cap cas, totes les excepcions que es puguin produir han de ser capturades.

## Lliurament

Heu de lliurar la vostra pràctica al Racó. Només heu de lliurar un fitxer ZIP que, al descomprimir-se generi:

- Un fitxer `README.md` que documenti el vostre projecte.
  
  - vegeu, per exemple, https://www.makeareadme.com/.

- Un fitxer `Makefile` tal que, quan s'executi `make`, es creïn els fitxers necessaris per executar el vostre projecte.

- Un fitxer `cantor.g4` amb la gramàtica del LP.

- Un fitxer `cantor.py` amb el programa principal de l'intèrpret.

- Més fitxers `.py` amb les classes, visitadors i funcions auxiliars.

- Jocs de proves en fitxers `.cantor` amb entrades en fitxers `.inp` i sortides en fitxers `.out`.

- Res més. 

Observacions:

- Els vostres fitxers de codi en Python han de seguir les regles d'estı́l PEP8, tot i que podeu oblidar les restriccions sobre la llargada màxima de les lı́nies. L'ús de tabuladors en el codi queda prohibit (zero directe).

- El termini de lliurament és el **dilluns 1 de juny a les 08:00**.

- Per evitar problemes de còpies, no pengeu el vostre projecte en repositoris públics.

- El vostre lliurament no ha d'incloure els fitxers que genera ANTLR, aquests s'han de crear via `make`.

- Si no heu realitzat alguna part de la pràctica, o sabeu que aquest té algun error en alguna part, deixeu-ho escrit al `README.md`.

## Avaluació

L'avaluació de la vostra pràctica tindrà en compte diversos aspectes clau, entre els quals es destaquen els següents:

1. **Qualitat de la gramàtica**: Es valorarà la qualitat de la gramàtica ANTLR, incloent la seva _completitud_, _precisió_, _concisió_ i _robustesa_. La gramàtica ha de ser capaç de reconèixer correctament els programes i les expressions del llenguate descrit, així com de manegar les diferents funcions que es poden realitzar en aquest llenguatge. 

2. **Qualitat del codi**: S'examinarà el codi font tenint en compte diversos factors, com ara la _correctesa_, la _completitud_, la _llegibilitat_, l'_eficiència_, el _bon ús dels identificadors_, ètc. També es tindrà en compte la _bona estructuració_ del codi, és a dir, l'ús adequat de funcions, classes, mòduls i altres elements que afavoreixin la redacció, la comprensió i el manteniment del codi a llarg termini. Es valorarà negativament l'ús de funcions llargues o poc clares, funcions incomprensibles sense especificació, la presència de codi duplicat o innecessari, acoblament fort, variables globals o atributs de classe erronis, comentaris excessius, i altres pràctiques nocives. Per aquesta pràctica, l'eficiència és secundària, però no s'admetran disbarats.

3. **Qualitat de la documentació**: S'analitzarà la documentació del projecte, amb especial atenció a la seva _claredat_, _precisió_ i _completesa_, alhora que la seva _concisió_. La documentació hauria de descriure adequadament el funcionament del codi, les seves funcions i característiques principals, així com qualsevol altre aspecte rellevant que faciliti la comprensió i l'ús del projecte. La documentació també ha de deixar clares les decisions de disseny preses.

En definitiva, és important recordar que es tracta d'un projecte de programació i, per tant, s'espera que el codi segueixi _bones pràctiques de programació_. 
