import importlib
import os
import socket
import sys

from flask import Flask, flash, render_template, request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRANSLATOR_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "translator"))
sys.path.insert(0, TRANSLATOR_DIR)

codegen = importlib.import_module("codegen")
lexer = importlib.import_module("lexer")
semanalyzer = importlib.import_module("semanalyzer")
syntaxer = importlib.import_module("syntaxer")

TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = Flask(
    __name__,
    template_folder=TEMPLATE_DIR,
    static_folder=STATIC_DIR,
)
app.config["SECRET_KEY"] = "smA8691BVVd2bq9iSzeAm2yW1GJJD0dE"


@app.route("/", methods=["GET"])
def index():
    input_text = request.args.get("input")
    output = ""

    if not input_text:
        return render_template("index.html", input="", output="")

    try:
        tokens = lexer.tokenize(input_text)
        analyzer = syntaxer.SyntaxAnalyzer(tokens)
        syntax_tree = analyzer.parse_program()
        semanalyzer.SemanticAnalyzer().check_program(syntax_tree)
        output = codegen.CodeGenerator().generate(syntax_tree)
    except Exception as err:
        flash(f"{type(err)}: {err}", category="error")

    return render_template("index.html", input=input_text, output=output)


def find_free_port(start_port: int = 5000, max_attempts: int = 10) -> int:
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return start_port


if __name__ == "__main__":
    port = find_free_port(5000)
    print(f"Запуск сервера на http://127.0.0.1:{port}")
    app.run(debug=True, host="127.0.0.1", port=port)
