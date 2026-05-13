.RECIPEPREFIX := >

ANTLR_JAR := antlr-4.13.2-complete.jar
GRAMMAR := cantor.g4
GENERATED := cantorLexer.py cantorParser.py cantorVisitor.py \
             cantor.interp cantor.tokens cantorLexer.interp cantorLexer.tokens

.PHONY: all antlr clean test

all: antlr
> @echo "ANTLR parser ready."

antlr: $(GENERATED)

$(GENERATED): $(GRAMMAR)
> @if command -v antlr4 >/dev/null 2>&1; then \
>     antlr4 -Dlanguage=Python3 -no-listener -visitor $(GRAMMAR); \
> elif [ -f "$(ANTLR_JAR)" ]; then \
>     java -jar $(ANTLR_JAR) -Dlanguage=Python3 -no-listener -visitor $(GRAMMAR); \
> else \
>     echo "ANTLR not found. Install antlr4 or place $(ANTLR_JAR) here."; \
>     exit 1; \
> fi

test: antlr
> python3 tests/run_tests.py

clean:
> rm -f $(GENERATED)
> rm -rf __pycache__ tests/__pycache__
