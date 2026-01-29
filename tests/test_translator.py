import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TRANSLATOR_DIR = os.path.join(ROOT, "code", "translator")
sys.path.insert(0, TRANSLATOR_DIR)

import lexer
import syntaxer
import semanalyzer
import codegen


def compile_pascal(code: str) -> str:
    tokens = lexer.tokenize(code)
    analyzer = syntaxer.SyntaxAnalyzer(tokens)
    ast = analyzer.parse_program()
    semanalyzer.SemanticAnalyzer().check_program(ast)
    return codegen.CodeGenerator().generate(ast)


class TranslatorTests(unittest.TestCase):
    def test_logic_operators(self):
        src = """
program t;
var
  a: boolean;
begin
  a := not (true xor false) and true or false;
end.
"""
        out = compile_pascal(src)
        self.assertIn("&&", out)
        self.assertIn("||", out)
        self.assertIn("!", out)

    def test_unary_minus(self):
        src = """
program t;
var
  x: integer;
begin
  x := -1;
  x := -(1 + 2);
end.
"""
        out = compile_pascal(src)
        self.assertIn("x = -1", out)
        self.assertIn("x = -(1 + 2)", out)

    def test_parentheses_precedence(self):
        src = """
program t;
var
  x: integer;
begin
  x := (1 + 2) * 3;
  x := 1 + 2 * 3;
  x := (1 + 2) * (3 + 4);
  x := 10 - (3 - 1);
  x := 10 / (2 / 5);
end.
"""
        out = compile_pascal(src)
        self.assertIn("x = (1 + 2) * 3", out)
        self.assertIn("x = 1 + 2 * 3", out)
        self.assertIn("x = (1 + 2) * (3 + 4)", out)
        self.assertIn("x = 10 - (3 - 1)", out)
        self.assertIn("x = 10 / (2 / 5)", out)

    def test_functions_and_procedures(self):
        src = """
program t;
var
  x: integer;
function add(a: integer; b: integer): integer;
begin
  add := a + b;
end;
procedure hello(a: integer);
begin
  writeln(a);
end;
begin
  x := add(2, 3);
  hello(x);
end.
"""
        out = compile_pascal(src)
        self.assertIn("func add(a int, b int) int", out)
        self.assertIn("return a + b", out)
        self.assertIn("func hello(a int)", out)
        self.assertIn("hello(x)", out)

    def test_control_flow(self):
        src = """
program t;
var
  i: integer;
begin
  i := 0;
  while i < 3 do
    i := i + 1;
  for i := 1 to 3 do
    writeln(i);
  repeat
    i := i + 1;
  until i = 5;
  case i of
    1: writeln(1);
    2, 3: writeln(2);
  else
    writeln(0);
  end;
end.
"""
        out = compile_pascal(src)
        self.assertIn("for i := 1; i <= 3; i++", out)
        self.assertIn("switch i", out)
        self.assertIn("case 2, 3:", out)
        self.assertIn("default:", out)

    def test_types_float_char(self):
        src = """
program t;
var
  f: real;
  c: char;
begin
  f := 1.5;
  c := 'a';
end.
"""
        out = compile_pascal(src)
        self.assertIn("var f float64", out)
        self.assertIn("var c rune", out)

    def test_arrays(self):
        src = """
program t;
var
  a: array[1..3] of integer;
  i: integer;
begin
  i := 1;
  a[i] := 10;
  writeln(a[1]);
end.
"""
        out = compile_pascal(src)
        self.assertIn("var a [3]int", out)
        self.assertIn("a[(i) - 1] = 10", out)
        self.assertIn("fmt.Println(a[(1) - 1])", out)


if __name__ == "__main__":
    unittest.main()
