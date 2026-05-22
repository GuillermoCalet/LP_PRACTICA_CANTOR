# Gramàtica ANTLR4 del llenguatge Cantor.
GRAMMAR := cantor.g4

# Jar local d'ANTLR. El projecte no depèn del wrapper antlr4 ni d'internet.
ANTLR_JAR := antlr-4.13.2-complete.jar
ANTLR_FLAGS := -Dlanguage=Python3 -no-listener -visitor

# Si existeix l'entorn virtual lp/, l'usem per defecte; si no, usem python3.
PYTHON ?= $(shell if [ -x lp/bin/python3 ]; then printf 'lp/bin/python3'; else printf 'python3'; fi)

# Fitxers generats per ANTLR. No s'editen a mà.
GENERATED := cantorLexer.py cantorParser.py cantorVisitor.py \
             cantor.interp cantor.tokens cantorLexer.interp cantorLexer.tokens

.PHONY: all antlr install test examples doctest run clean

all: antlr

antlr: $(GRAMMAR)
	@if [ -f "$(ANTLR_JAR)" ]; then \
		java -jar $(ANTLR_JAR) $(ANTLR_FLAGS) $(GRAMMAR); \
	elif command -v antlr4 >/dev/null 2>&1; then \
		antlr4 $(ANTLR_FLAGS) $(GRAMMAR); \
	else \
		echo "ANTLR not found. Place $(ANTLR_JAR) here or install antlr4."; \
		exit 1; \
	fi

install:
	$(PYTHON) -m pip install antlr4-python3-runtime==4.13.2

test: antlr examples doctest

examples:
	$(PYTHON) tests/run_tests.py

doctest:
	$(PYTHON) -m doctest -v test.txt

run: antlr
	echo "6 2 13" | $(PYTHON) cantor.py tests/add3.cantor

clean:
	rm -f $(GENERATED)
	rm -rf __pycache__ tests/__pycache__ .antlr
