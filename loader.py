"""Loading, parsing and building Cantor programs."""

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from errors import (
    CantorLoadError,
    CantorSyntaxError,
    CantorValidationError,
    CollectingErrorListener,
)
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
    from cantorVisitor import cantorVisitor
except ModuleNotFoundError:
    class cantorVisitor:
        """Fallback used only to let cantor.py print a clean error pre-make."""

        pass


EXTENDED_OPERATORS = {"compair", "primrec"}


def _load_antlr_classes():
    try:
        from antlr4 import CommonTokenStream, FileStream
        from cantorLexer import cantorLexer
        from cantorParser import cantorParser
    except ModuleNotFoundError as exc:
        missing_name = getattr(exc, "name", "")
        if missing_name == "antlr4":
            raise CantorLoadError(
                "ANTLR Python runtime is missing. Install "
                "antlr4-python3-runtime or activate the project environment."
            ) from exc
        raise CantorLoadError(
            "ANTLR files are missing. Run 'make' before executing cantor.py."
        ) from exc
    return CommonTokenStream, FileStream, cantorLexer, cantorParser


@dataclass(frozen=True)
class Definition:
    """Intermediate representation of a Cantor function definition."""

    name: str
    op: str
    args: tuple[str, ...]
    doc: str
    source: Path


@dataclass
class ParsedFile:
    """Information extracted from one .cantor file."""

    path: Path
    main: str | None
    imports: list[str]
    extended: bool
    definitions: list[Definition]


@dataclass
class LoadedProgram:
    """Executable program built from parsed definitions."""

    main_name: str
    main_function: NaturalFunction
    functions: dict[str, NaturalFunction]
    definitions: dict[str, Definition]
    extended: bool


class ProgramVisitor(cantorVisitor):
    """Extract main/import/extended directives and definitions from the tree."""

    def __init__(self, path: Path):
        self.path = path
        self.main = None
        self.imports = []
        self.extended = False
        self.definitions = []

    def visitProgram(self, ctx):
        for statement in ctx.statement():
            self.visit(statement)
        return ParsedFile(
            path=self.path,
            main=self.main,
            imports=self.imports,
            extended=self.extended,
            definitions=self.definitions,
        )

    def visitMainDecl(self, ctx):
        self.main = ctx.NAME().getText()

    def visitImportDecl(self, ctx):
        self.imports.append(ctx.NAME().getText())

    def visitExtendedDecl(self, ctx):
        self.extended = True

    def visitDefinition(self, ctx):
        name = ctx.NAME().getText()
        doc = ctx.DOC().getText()[1:-1].strip()
        op, args = self.visit(ctx.expression())
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
        return "pair", (ctx.NAME(0).getText(), ctx.NAME(1).getText())

    def visitCompExpr(self, ctx):
        return "comp", (ctx.NAME(0).getText(), ctx.NAME(1).getText())

    def visitMuExpr(self, ctx):
        return "mu", (ctx.NAME().getText(),)

    def visitCompairExpr(self, ctx):
        return (
            "compair",
            (
                ctx.NAME(0).getText(),
                ctx.NAME(1).getText(),
                ctx.NAME(2).getText(),
            ),
        )

    def visitPrimrecExpr(self, ctx):
        return (
            "primrec",
            (
                ctx.NAME(0).getText(),
                ctx.NAME(1).getText(),
                ctx.NAME(2).getText(),
            ),
        )


class ProgramLoader:
    """Load a main file plus imports, then build executable closures."""

    def __init__(self):
        self.loaded_paths: set[Path] = set()
        self.definitions: dict[str, Definition] = {}
        self.extended = False
        self.main_name = None

    def load(self, path: Path) -> LoadedProgram:
        """Load a main .cantor file and return an executable program."""

        main_path = self._normalize_path(path)
        self._load_file(main_path, is_main=True)
        self._validate()
        return self._build_program()

    def _normalize_path(self, path: Path) -> Path:
        if path.suffix != ".cantor":
            path = path.with_suffix(".cantor")
        return path.resolve()

    def _resolve_import(self, current_file: Path, import_name: str) -> Path:
        return (current_file.parent / f"{import_name}.cantor").resolve()

    def _load_file(self, path: Path, is_main: bool) -> None:
        if path in self.loaded_paths:
            return
        if not path.exists():
            raise CantorLoadError(f"file not found: {path}")

        parsed = self._parse_file(path)
        self.loaded_paths.add(path)
        self.extended = self.extended or parsed.extended

        if is_main:
            self.main_name = parsed.main

        for import_name in parsed.imports:
            imported_path = self._resolve_import(path, import_name)
            self._load_file(imported_path, is_main=False)

        for definition in parsed.definitions:
            self._register_definition(definition)

    def _parse_file(self, path: Path) -> ParsedFile:
        token_stream_class, file_stream_class, lexer_class, parser_class = (
            _load_antlr_classes()
        )
        lexer = lexer_class(file_stream_class(str(path), encoding="utf-8"))
        token_stream = token_stream_class(lexer)
        parser = parser_class(token_stream)
        listener = CollectingErrorListener(path)

        lexer.removeErrorListeners()
        parser.removeErrorListeners()
        lexer.addErrorListener(listener)
        parser.addErrorListener(listener)

        tree = parser.program()
        if listener.errors:
            raise CantorSyntaxError("\n".join(listener.errors))

        return ProgramVisitor(path).visit(tree)

    def _register_definition(self, definition: Definition) -> None:
        predefined = set(base_functions()) | set(extended_functions())
        if definition.name in predefined:
            raise CantorValidationError(
                f"{definition.source}: function '{definition.name}' "
                "redefines a predefined function"
            )
        if definition.name in self.definitions:
            first = self.definitions[definition.name].source
            raise CantorValidationError(
                f"{definition.source}: duplicate definition "
                f"'{definition.name}' already defined in {first}"
            )
        self.definitions[definition.name] = definition

    def _validate(self) -> None:
        if self.main_name is None:
            raise CantorValidationError("main file does not define 'main'")
        if not self.extended:
            for definition in self.definitions.values():
                if definition.op in EXTENDED_OPERATORS:
                    raise CantorValidationError(
                        f"{definition.source}: '{definition.op}' requires "
                        "the 'extended' directive"
                    )

    def _build_program(self) -> LoadedProgram:
        functions = base_functions()
        if self.extended:
            functions.update(extended_functions())

        builders = {
            "pair": self._build_pair,
            "comp": self._build_comp,
            "mu": self._build_mu,
            "compair": self._build_compair,
            "primrec": self._build_primrec,
        }
        building_stack = []

        def resolve(name: str) -> NaturalFunction:
            if name in functions:
                return functions[name]
            if name not in self.definitions:
                raise CantorValidationError(f"unknown function '{name}'")
            if name in building_stack:
                cycle = " -> ".join(building_stack + [name])
                raise CantorValidationError(f"cyclic definition: {cycle}")

            definition = self.definitions[name]
            building_stack.append(name)
            functions[name] = builders[definition.op](definition, resolve)
            building_stack.pop()
            return functions[name]

        for name in self.definitions:
            resolve(name)

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
        f_name, g_name = definition.args
        return make_pair(resolve(f_name), resolve(g_name))

    def _build_comp(
        self,
        definition: Definition,
        resolve: Callable[[str], NaturalFunction],
    ) -> NaturalFunction:
        f_name, g_name = definition.args
        return make_comp(resolve(f_name), resolve(g_name))

    def _build_mu(
        self,
        definition: Definition,
        resolve: Callable[[str], NaturalFunction],
    ) -> NaturalFunction:
        (predicate_name,) = definition.args
        return make_mu(resolve(predicate_name))

    def _build_compair(
        self,
        definition: Definition,
        resolve: Callable[[str], NaturalFunction],
    ) -> NaturalFunction:
        f_name, g_name, h_name = definition.args
        return make_compair(resolve(f_name), resolve(g_name), resolve(h_name))

    def _build_primrec(
        self,
        definition: Definition,
        resolve: Callable[[str], NaturalFunction],
    ) -> NaturalFunction:
        f_name, g_name, h_name = definition.args
        return make_primrec(resolve(f_name), resolve(g_name), resolve(h_name))


def load_program(path: str | Path) -> LoadedProgram:
    """Convenience function used by cantor.py."""

    return ProgramLoader().load(Path(path))
