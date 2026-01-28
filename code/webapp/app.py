from flask import Flask, render_template, request, flash
import sys
import os

# Добавляем путь к модулям translator
base_dir = os.path.dirname(os.path.abspath(__file__))
translator_dir = os.path.abspath(os.path.join(base_dir, '..', 'translator'))
sys.path.insert(0, translator_dir)

import codegen
import semanalyzer
import lexer
import syntaxer

# Указываем Flask, где искать шаблоны и статические файлы
template_dir = os.path.join(base_dir, 'templates')
static_dir = os.path.join(base_dir, 'static')
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.config['SECRET_KEY'] = 'smA8691BVVd2bq9iSzeAm2yW1GJJD0dE'

@app.route('/', methods=['GET'])
def index():
    input = request.args.get('input')
    output = ''
    textTree = ''
    tokens = ''

    if not input:
        return render_template('index.html', input='', output='', syntaxTree='', tokens='')

    try:        
        tokens = lexer.tokenize(input)
        analyzer = syntaxer.SyntaxAnalyzer(tokens)
        syntaxTree = analyzer.parse_program()
        textTree = analyzer.getTextTree(syntaxTree)
        semanalyzer.SemanticAnalyzer().check_program(syntaxTree)
        output = codegen.CodeGenerator().generate(syntaxTree)
    except Exception as err:
        flash(f'{type(err)}: {err}', category='error')

    return render_template('index.html', input=input, output=output, syntaxTree=textTree, tokens='\n'.join(map(str, tokens)))


if __name__ == '__main__':
    import socket
    
    # Функция для поиска свободного порта
    def find_free_port(start_port=5000, max_attempts=10):
        for port in range(start_port, start_port + max_attempts):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(('127.0.0.1', port))
                    return port
                except OSError:
                    continue
        return start_port  # Если не нашли, используем начальный порт
    
    port = find_free_port(5000)
    print(f"Запуск сервера на http://127.0.0.1:{port}")
    app.run(debug=True, host='127.0.0.1', port=port)
