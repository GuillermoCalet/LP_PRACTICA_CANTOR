"""Carrega, analitza i construeix programes Cantor."""

# dataclass evita escribir clases llenas de __init__ manuales.
from dataclasses import dataclass

# Path se usa para rutas de archivos de forma robusta.
from pathlib import Path

# Callable es el tipo de una funcion Python.
from typing import Callable

# Excepciones propias y listener que recoge errores de ANTLR.
from errors import (
    CantorLoadError,
    CantorSyntaxError,
    CantorValidationError,
    CollectingErrorListener,
)

# Funciones y constructores del runtime.
from runtime import (
    NaturalFunction,
    base_functions,
    extended_functions,
    make_comp,
    make_compair,
    make_mu,
    make_pair,
    make_primrec,
)

try:
    # cantorVisitor.py lo genera ANTLR cuando se ejecuta make.
    from cantorVisitor import cantorVisitor
except ModuleNotFoundError:
    # Si el usuario ejecuta cantor.py antes de make, no queremos que Python
    # rompa al importar loader.py. Dejamos una clase minima y luego damos un
    # error claro cuando realmente se intente cargar un programa.
    class cantorVisitor:
        """Substitut usat perquè cantor.py mostri un error clar abans de make."""

        pass


# Operadores que solo son legales si el programa esta en modo extended.
EXTENDED_OPERATORS = {"compair", "primrec"}


def _load_antlr_classes():
    # Importamos estas clases dentro de la funcion para poder capturar errores
    # con mensajes de usuario. Si se importaran arriba, Python podria mostrar
    # un traceback feo antes de que main pudiera capturarlo.
    try:
        from antlr4 import CommonTokenStream, FileStream
        from cantorLexer import cantorLexer
        from cantorParser import cantorParser
    except ModuleNotFoundError as exc:
        missing_name = getattr(exc, "name", "")

        # Caso 1: falta el runtime de ANTLR para Python.
        if missing_name == "antlr4":
            raise CantorLoadError(
                "ANTLR Python runtime is missing. Install "
                "antlr4-python3-runtime or activate the project environment."
            ) from exc

        # Caso 2: faltan los archivos generados por ANTLR.
        raise CantorLoadError(
            "ANTLR files are missing. Run 'make' before executing cantor.py."
        ) from exc

    return CommonTokenStream, FileStream, cantorLexer, cantorParser


@dataclass(frozen=True)
class Definition:
    """Representació intermèdia de la definició d'una funció Cantor."""

    # Nombre de la funcion definida con "define nombre".
    name: str

    # Operador usado: pair, comp, mu, compair o primrec.
    op: str

    # Nombres de las funciones argumento del operador.
    # Ejemplo: comp f g -> args == ("f", "g").
    args: tuple[str, ...]

    # Texto dentro de [ ... ]. No se ejecuta, solo se conserva.
    doc: str

    # Archivo de origen, util para errores claros.
    source: Path


@dataclass
class ParsedFile:
    """Informació extreta d'un fitxer .cantor."""

    # Ruta del archivo parseado.
    path: Path

    # Funcion main declarada en ese archivo, o None.
    main: str | None

    # Lista de imports escritos en el archivo.
    imports: list[str]

    # True si aparece la directiva extended.
    extended: bool

    # Definiciones encontradas en el archivo.
    definitions: list[Definition]


@dataclass
class LoadedProgram:
    """Programa executable construït a partir de les definicions analitzades."""

    # Nombre de la funcion principal.
    main_name: str

    # Funcion Python ya construida que se ejecutara.
    main_function: NaturalFunction

    # Todas las funciones disponibles, predefinidas e importadas.
    functions: dict[str, NaturalFunction]

    # Definiciones de usuario antes de construirlas como closures.
    definitions: dict[str, Definition]

    # Indica si se activo el modo extended.
    extended: bool


class ProgramVisitor(cantorVisitor):
    """Extreu les directives main/import/extended i les definicions de l'arbre."""

    def __init__(self, path: Path):
        # Guardamos la ruta para meterla en cada Definition.
        self.path = path

        # Campos que iremos rellenando al visitar el arbol.
        self.main = None
        self.imports = []
        self.extended = False
        self.definitions = []

    def visitProgram(self, ctx):
        # ctx.statement() contiene todas las sentencias del programa:
        # main, import, extended y define.
        for statement in ctx.statement():
            self.visit(statement)

        # Al terminar, devolvemos un resumen facil de usar por ProgramLoader.
        return ParsedFile(
            path=self.path,
            main=self.main,
            imports=self.imports,
            extended=self.extended,
            definitions=self.definitions,
        )

    def visitMainDecl(self, ctx):
        # main nombre -> guardamos "nombre".
        self.main = ctx.NAME().getText()

    def visitImportDecl(self, ctx):
        # import nombre -> guardamos "nombre"; loader anadira ".cantor".
        self.imports.append(ctx.NAME().getText())

    def visitExtendedDecl(self, ctx):
        # extended -> activa modo extendido para todo el programa cargado.
        self.extended = True

    def visitDefinition(self, ctx):
        # Primer NAME de una definicion es el nombre de la funcion.
        name = ctx.NAME().getText()

        # DOC incluye los corchetes. [texto] -> texto.
        doc = ctx.DOC().getText()[1:-1].strip()

        # Visitamos expression para obtener ("op", ("arg1", ...)).
        op, args = self.visit(ctx.expression())

        # Guardamos la definicion como datos; todavia no construimos la
        # funcion Python. Eso se hace despues para permitir referencias futuras.
        self.definitions.append(
            Definition(
                name=name,
                op=op,
                args=args,
                doc=doc,
                source=self.path,
            )
        )

    def visitPairExpr(self, ctx):
        # pair f g
        return "pair", (ctx.NAME(0).getText(), ctx.NAME(1).getText())

    def visitCompExpr(self, ctx):
        # comp f g
        return "comp", (ctx.NAME(0).getText(), ctx.NAME(1).getText())

    def visitMuExpr(self, ctx):
        # mu f
        return "mu", (ctx.NAME().getText(),)

    def visitCompairExpr(self, ctx):
        # compair f g h
        return (
            "compair",
            (
                ctx.NAME(0).getText(),
                ctx.NAME(1).getText(),
                ctx.NAME(2).getText(),
            ),
        )

    def visitPrimrecExpr(self, ctx):
        # primrec f g h
        return (
            "primrec",
            (
                ctx.NAME(0).getText(),
                ctx.NAME(1).getText(),
                ctx.NAME(2).getText(),
            ),
        )


class ProgramLoader:
    """Carrega el fitxer principal, els imports i les funcions executables."""

    def __init__(self):
        # Rutas ya cargadas. Evita cargar dos veces y evita bucles de imports.
        self.loaded_paths: set[Path] = set()

        # Tabla de definiciones de usuario por nombre.
        self.definitions: dict[str, Definition] = {}

        # El modo extended se activa si cualquier archivo cargado lo pide.
        self.extended = False

        # Solo se toma el main del archivo principal.
        self.main_name = None

    def load(self, path: Path) -> LoadedProgram:
        """Carrega un fitxer principal .cantor i retorna un programa executable."""

        # Normalizamos la ruta del archivo principal.
        main_path = self._normalize_path(path)

        # Fase 1: cargar y parsear archivo principal e imports.
        self._load_file(main_path, is_main=True)

        self._validate()

        # Fase 2: convertir definiciones en funciones Python ejecutables.
        return self._build_program()

    def _normalize_path(self, path: Path) -> Path:
        # Permite usar "programa" o "programa.cantor".
        if path.suffix != ".cantor":
            path = path.with_suffix(".cantor")

        # resolve convierte la ruta en absoluta y limpia componentes como ..
        return path.resolve()

    def _resolve_import(self, current_file: Path, import_name: str) -> Path:
        # Los imports son relativos al directorio del archivo que importa.
        return (current_file.parent / f"{import_name}.cantor").resolve()

    def _load_file(self, path: Path, is_main: bool) -> None:
        # Si ya lo hemos cargado, no hacemos nada.
        if path in self.loaded_paths:
            return

        if not path.exists():
            raise CantorLoadError(f"file not found: {path}")

        # Parseamos el archivo con ANTLR y visitor.
        parsed = self._parse_file(path)

        # Marcamos como cargado antes de procesar imports para cortar ciclos.
        self.loaded_paths.add(path)

        # Si cualquier archivo usa extended, todo el programa queda extended.
        self.extended = self.extended or parsed.extended

        # Solo el archivo principal decide la funcion main.
        if is_main:
            self.main_name = parsed.main

        # Cargamos imports antes de registrar definiciones del archivo actual.
        # Asi las librerias quedan disponibles para el archivo que importa.
        for import_name in parsed.imports:
            imported_path = self._resolve_import(path, import_name)
            self._load_file(imported_path, is_main=False)

        # Registramos definiciones y detectamos duplicados.
        for definition in parsed.definitions:
            self._register_definition(definition)

    def _parse_file(self, path: Path) -> ParsedFile:
        # Obtenemos las clases generadas por ANTLR.
        token_stream_class, file_stream_class, lexer_class, parser_class = (
            _load_antlr_classes()
        )

        # FileStream lee el archivo fuente.
        lexer = lexer_class(file_stream_class(str(path), encoding="utf-8"))

        # El lexer convierte texto en tokens; CommonTokenStream los almacena.
        token_stream = token_stream_class(lexer)

        # El parser convierte tokens en arbol sintactico.
        parser = parser_class(token_stream)

        # Listener propio para capturar errores de sintaxis.
        listener = CollectingErrorListener(path)

        # Quitamos listeners por defecto para que ANTLR no imprima directamente.
        lexer.removeErrorListeners()
        parser.removeErrorListeners()
        lexer.addErrorListener(listener)
        parser.addErrorListener(listener)

        # program es la regla inicial de la gramatica cantor.g4.
        tree = parser.program()

        if listener.errors:
            raise CantorSyntaxError("\n".join(listener.errors))

        # El visitor recorre el arbol y lo convierte en ParsedFile.
        return ProgramVisitor(path).visit(tree)

    def _register_definition(self, definition: Definition) -> None:
        # No dejamos redefinir funciones predefinidas como add, id o fst.
        predefined = set(base_functions()) | set(extended_functions())
        if definition.name in predefined:
            raise CantorValidationError(
                f"{definition.source}: function '{definition.name}' "
                "redefines a predefined function"
            )

        # Tampoco dejamos dos definiciones de usuario con el mismo nombre.
        if definition.name in self.definitions:
            first = self.definitions[definition.name].source
            raise CantorValidationError(
                f"{definition.source}: duplicate definition "
                f"'{definition.name}' already defined in {first}"
            )

        self.definitions[definition.name] = definition

    def _validate(self) -> None:
        # El archivo principal debe declarar main.
        if self.main_name is None:
            raise CantorValidationError("main file does not define 'main'")

        # Si no hay extended, compair y primrec no se pueden usar.
        if not self.extended:
            for definition in self.definitions.values():
                if definition.op in EXTENDED_OPERATORS:
                    raise CantorValidationError(
                        f"{definition.source}: '{definition.op}' requires "
                        "the 'extended' directive"
                    )

    def _build_program(self) -> LoadedProgram:
        # Empezamos con las funciones predefinidas basicas.
        functions = base_functions()

        # Si toca, anadimos fst y snd.
        if self.extended:
            functions.update(extended_functions())

        # Cada operador de la gramatica tiene una funcion constructora.
        builders = {
            "pair": self._build_pair,
            "comp": self._build_comp,
            "mu": self._build_mu,
            "compair": self._build_compair,
            "primrec": self._build_primrec,
        }

        # Pila de construccion para detectar ciclos:
        # f depende de g y g depende de f.
        building_stack = []

        def resolve(name: str) -> NaturalFunction:
            # Si ya existe en functions, puede ser predefinida o ya construida.
            if name in functions:
                return functions[name]

            if name not in self.definitions:
                raise CantorValidationError(f"unknown function '{name}'")

            if name in building_stack:
                cycle = " -> ".join(building_stack + [name])
                raise CantorValidationError(f"cyclic definition: {cycle}")

            # Construimos la funcion pidiendo antes sus dependencias.
            definition = self.definitions[name]
            building_stack.append(name)
            functions[name] = builders[definition.op](definition, resolve)
            building_stack.pop()
            return functions[name]

        # Forzamos que todas las definiciones se construyan y validen.
        for name in self.definitions:
            resolve(name)

        # Finalmente resolvemos la funcion main.
        main_function = resolve(self.main_name)

        return LoadedProgram(
            main_name=self.main_name,
            main_function=main_function,
            functions=functions,
            definitions=self.definitions,
            extended=self.extended,
        )

    def _build_pair(
        self,
        definition: Definition,
        resolve: Callable[[str], NaturalFunction],
    ) -> NaturalFunction:
        # pair f g necesita resolver f y g a funciones Python.
        f_name, g_name = definition.args
        return make_pair(resolve(f_name), resolve(g_name))

    def _build_comp(
        self,
        definition: Definition,
        resolve: Callable[[str], NaturalFunction],
    ) -> NaturalFunction:
        # comp f g necesita resolver f y g.
        f_name, g_name = definition.args
        return make_comp(resolve(f_name), resolve(g_name))

    def _build_mu(
        self,
        definition: Definition,
        resolve: Callable[[str], NaturalFunction],
    ) -> NaturalFunction:
        # mu f solo recibe un predicado.
        (predicate_name,) = definition.args
        return make_mu(resolve(predicate_name))

    def _build_compair(
        self,
        definition: Definition,
        resolve: Callable[[str], NaturalFunction],
    ) -> NaturalFunction:
        # compair f g h resuelve las tres funciones.
        f_name, g_name, h_name = definition.args
        return make_compair(resolve(f_name), resolve(g_name), resolve(h_name))

    def _build_primrec(
        self,
        definition: Definition,
        resolve: Callable[[str], NaturalFunction],
    ) -> NaturalFunction:
        # primrec f g h resuelve predicado, caso base y paso recursivo.
        f_name, g_name, h_name = definition.args
        return make_primrec(resolve(f_name), resolve(g_name), resolve(h_name))


def load_program(path: str | Path) -> LoadedProgram:
    """Funció auxiliar utilitzada per cantor.py."""

    # Funcion pequena para que cantor.py no tenga que crear ProgramLoader.
    return ProgramLoader().load(Path(path))
