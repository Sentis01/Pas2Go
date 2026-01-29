from typing import NamedTuple
import re

class Token(NamedTuple):
    type: str
    value: str
    line: int
    column: int

TOKEN_SPECIFICATION = [
    ('PROGRAM',      r'program\b'),
    ('VAR',          r'var\b'),
    ('FUNCTION',     r'function\b'),
    ('PROCEDURE',    r'procedure\b'),
    ('INTEGER',      r'integer\b'),
    ('REAL',         r'real\b'),
    ('BOOLEAN',      r'boolean\b'),
    ('CHAR',         r'char\b'),
    ('STRING',       r'string\b'),
    ('BEGIN',        r'begin\b'),
    ('END',          r'end\b'),
    ('IF',           r'if\b'),
    ('THEN',         r'then\b'),
    ('ELSE',         r'else\b'),
    ('WHILE',        r'while\b'),
    ('DO',           r'do\b'),
    ('REPEAT',       r'repeat\b'),
    ('UNTIL',        r'until\b'),
    ('FOR',          r'for\b'),
    ('TO',           r'to\b'),
    ('DOWNTO',       r'downto\b'),
    ('SWITCH',       r'switch\b'),
    ('CASE',         r'case\b'),
    ('DEFAULT',      r'default\b'),
    ('WRITELN',      r'writeln\b'),
    ('NOT',          r'not\b'),
    ('ARRAY',        r'array\b'),
    ('OF',           r'of\b'),
    ('ASSIGN',       r':='),
    ('COLON',        r':'),
    ('SEMICOLON',    r';'),
    ('COMMA',        r','),
    ('LPAR',         r'\('),
    ('RPAR',         r'\)'),
    ('LBRACKET',     r'\['),
    ('RBRACKET',     r'\]'),
    ('OPERATOR',     r'(\+|\-|\*|/|==|!=|<=|>=|<>|<|>|=|\band\b|\bor\b|\bxor\b|\bdiv\b|\bmod\b)'),
    ('RANGE',        r'\.\.'),
    ('NUMBER',       r'-?\d+(\.\d+)?'),
    ('BOOL_LIT',     r'\btrue\b|\bfalse\b'),
    ('CHAR_LIT',     r"'(.)'"),
    ('STRING_LIT',   r"'[^']*'"),
    ('COMMENT1',     r'//.*'),
    ('COMMENT2',     r'\{[^}]*\}'),
    ('IDENTIFIER',   r'[a-zA-Z_][a-zA-Z0-9_]*'),
    ('SKIP',         r'[\s\t\n\r]+'),
    ('DOT',          r'\.'),
    ('MISMATCH',     r'.'),
]

def tokenize(code: str) -> list[Token]:
    tokens = []
    tok_regex = '|'.join(f'(?P<{pair[0]}>{pair[1]})' for pair in TOKEN_SPECIFICATION)
    line_num = 1
    line_start = 0

    for mo in re.finditer(tok_regex, code, re.IGNORECASE):
        kind = mo.lastgroup
        value = mo.group()
        column = mo.start() - line_start

        if kind in ['SKIP', 'COMMENT1', 'COMMENT2']:
            if '\n' in value:
                line_num += value.count('\n')
                line_start = mo.end() - (len(value) - value.rfind('\n') - 1)
            continue
        elif kind == 'MISMATCH':
            raise SyntaxError(f"Недопустимый символ '{value}' на строке {line_num}, колонка {column}")
        elif kind == 'STRING_LIT':
            tokens.append(Token('STRING', value, line_num, column))
        elif kind == 'IDENTIFIER' and value.lower() in {'package', 'import', 'func'}:
            raise NameError(f"Использование зарезервированного слова Go: '{value}' (строка {line_num}, колонка {column})")
        else:
            tokens.append(Token(kind, value, line_num, column))

        if '\n' in value:
            line_num += value.count('\n')
            line_start = mo.end() - (len(value) - value.rfind('\n') - 1)

    return tokens
