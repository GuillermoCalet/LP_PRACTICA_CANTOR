.RECIPEPREFIX := >

# Usamos primero el jar local para no depender de internet.
# Algunos comandos antlr4 instalados con pip intentan descargar cosas.
ANTLR_JAR := antlr-4.13.2-complete.jar

# Archivo fuente de la gramatica.
GRAMMAR := cantor.g4

# Python que se usara para los tests. Por defecto usa python3 del sistema.
# Si quieres usar un entorno virtual:
#   make test PYTHON=lp/bin/python3
PYTHON ?= python3

# Archivos que genera ANTLR. No se editan a mano ni se entregan en el ZIP.
GENERATED := cantorLexer.py cantorParser.py cantorVisitor.py \
             cantor.interp cantor.tokens cantorLexer.interp cantorLexer.tokens

# Declaramos objetivos que no son archivos reales.
.PHONY: all antlr clean test

# Objetivo por defecto: preparar el parser.
all: antlr
> @echo "ANTLR parser ready."

# antlr depende de los archivos generados.
antlr: $(GENERATED)

# Si falta algun generado, o cantor.g4 es mas nuevo, se ejecuta esta regla.
$(GENERATED): $(GRAMMAR)
> @if [ -f "$(ANTLR_JAR)" ]; then \
>     java -jar $(ANTLR_JAR) -Dlanguage=Python3 -no-listener -visitor $(GRAMMAR); \
> elif command -v antlr4 >/dev/null 2>&1; then \
>     antlr4 -Dlanguage=Python3 -no-listener -visitor $(GRAMMAR); \
> else \
>     echo "ANTLR not found. Install antlr4 or place $(ANTLR_JAR) here."; \
>     exit 1; \
> fi

# Ejecuta la bateria de pruebas.
test: antlr
> $(PYTHON) tests/run_tests.py

# Borra archivos generados y caches.
clean:
> rm -f $(GENERATED)
> rm -rf __pycache__ tests/__pycache__
