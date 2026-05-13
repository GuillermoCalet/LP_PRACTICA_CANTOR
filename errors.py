"""Common exceptions and ANTLR error collection for the Cantor interpreter."""

try:
    # ErrorListener es la clase base de ANTLR para reaccionar a errores.
    from antlr4.error.ErrorListener import ErrorListener
except ModuleNotFoundError:
    # Si falta antlr4, dejamos una clase minima para que el import no explote.
    # loader.py mostrara luego un error claro explicando que falta ANTLR.
    class ErrorListener:
        """Fallback so missing ANTLR runtime becomes a clean load error later."""

        pass


class CantorError(Exception):
    """Base class for user-facing interpreter errors."""


# Cada excepcion representa un tipo de problema. Todas heredan de CantorError,
# asi cantor.py puede capturarlas juntas y escribir "Error: ...".
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

        # Archivo donde ocurrio el error.
        self.path = path

        # Lista de mensajes acumulados. Puede haber mas de un error sintactico.
        self.errors = []

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, exc):
        # ANTLR llama automaticamente a este metodo cuando encuentra un error.
        # Guardamos una ubicacion estilo archivo:linea:columna.
        location = f"{self.path}:{line}:{column}"
        self.errors.append(f"{location}: {msg}")
