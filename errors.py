
try:
    # ErrorListener es la clase base de ANTLR para reaccionar a errores.
    from antlr4.error.ErrorListener import ErrorListener
except ModuleNotFoundError:
    # Si falta antlr4, dejamos una clase minima para que el import no explote.
    # loader.py mostrara luego un error claro explicando que falta ANTLR.
    class ErrorListener:
        """Substitut perquè la falta del runtime ANTLR generi un error clar."""

        pass


class CantorError(Exception):
    """Classe base dels errors de l'intèrpret mostrats a l'usuari."""


# Cada excepcion representa un tipo de problema. Todas heredan de CantorError,
# asi cantor.py puede capturarlas juntas y escribir "Error: ...".
class CantorSyntaxError(CantorError):
    """Es produeix quan ANTLR informa d'un o més errors de sintaxi."""


class CantorLoadError(CantorError):
    """Es produeix quan no es pot carregar un programa o algun import."""


class CantorValidationError(CantorError):
    """Es produeix quan el programa és sintàcticament vàlid però inutilitzable."""


class CantorRuntimeError(CantorError):
    """Es produeix quan l'avaluació no pot acabar correctament."""


class CantorInputError(CantorError):
    """Es produeix quan stdin no conté una llista de nombres naturals."""


class CollectingErrorListener(ErrorListener):
    """Recull els errors de sintaxi d'ANTLR en lloc de mostrar-los directament."""

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
