"""Common exceptions and ANTLR error collection for the Cantor interpreter."""

try:
    from antlr4.error.ErrorListener import ErrorListener
except ModuleNotFoundError:
    class ErrorListener:
        """Fallback so missing ANTLR runtime becomes a clean load error later."""

        pass


class CantorError(Exception):
    """Base class for user-facing interpreter errors."""


class CantorSyntaxError(CantorError):
    """Raised when ANTLR reports one or more syntax errors."""


class CantorLoadError(CantorError):
    """Raised when a program or one of its imports cannot be loaded."""


class CantorValidationError(CantorError):
    """Raised when the parsed program is syntactically valid but unusable."""


class CantorRuntimeError(CantorError):
    """Raised when evaluation cannot finish cleanly."""


class CantorInputError(CantorError):
    """Raised when stdin does not contain a list of natural numbers."""


class CollectingErrorListener(ErrorListener):
    """Collects ANTLR syntax errors instead of printing them directly."""

    def __init__(self, path):
        super().__init__()
        self.path = path
        self.errors = []

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, exc):
        location = f"{self.path}:{line}:{column}"
        self.errors.append(f"{location}: {msg}")
