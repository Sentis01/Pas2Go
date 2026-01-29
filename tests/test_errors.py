import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TRANSLATOR_DIR = os.path.join(ROOT, "code", "translator")
sys.path.insert(0, TRANSLATOR_DIR)

import lexer
import syntaxer
import semanalyzer


def analyze_pascal(code: str):
    tokens = lexer.tokenize(code)
    analyzer = syntaxer.SyntaxAnalyzer(tokens)
    ast = analyzer.parse_program()
    semanalyzer.SemanticAnalyzer().check_program(ast)


class TranslatorErrorTests(unittest.TestCase):
    def test_undeclared_variable(self):
        src = """
program t;
begin
  x := 1;
end.
"""
        with self.assertRaises(NameError):
            analyze_pascal(src)

    def test_type_mismatch_assignment(self):
        src = """
program t;
var
  s: string;
begin
  s := 1;
end.
"""
        with self.assertRaises(TypeError):
            analyze_pascal(src)

    def test_wrong_arg_count(self):
        src = """
program t;
function add(a: integer; b: integer): integer;
begin
  add := a + b;
end;
begin
  add(1);
end.
"""
        with self.assertRaises(TypeError):
            analyze_pascal(src)

    def test_wrong_arg_type(self):
        src = """
program t;
function add(a: integer; b: integer): integer;
begin
  add := a + b;
end;
begin
  add(1, 'a');
end.
"""
        with self.assertRaises(TypeError):
            analyze_pascal(src)

    def test_procedure_used_as_function(self):
        src = """
program t;
var
  x: integer;
procedure p(a: integer);
begin
  writeln(a);
end;
begin
  x := p(1);
end.
"""
        with self.assertRaises(TypeError):
            analyze_pascal(src)

    def test_function_used_as_procedure(self):
        src = """
program t;
function f(): integer;
begin
  f := 1;
end;
begin
  f();
end.
"""
        with self.assertRaises(TypeError):
            analyze_pascal(src)

    def test_array_index_not_integer(self):
        src = """
program t;
var
  a: array[1..3] of integer;
  f: real;
begin
  f := 1.5;
  a[f] := 1;
end.
"""
        with self.assertRaises(TypeError):
            analyze_pascal(src)

    def test_array_element_type_mismatch(self):
        src = """
program t;
var
  a: array[1..3] of integer;
begin
  a[1] := 'a';
end.
"""
        with self.assertRaises(TypeError):
            analyze_pascal(src)

    def test_array_comparison_not_supported(self):
        src = """
program t;
var
  a: array[1..2] of integer;
  b: array[1..2] of integer;
begin
  if a = b then
    writeln(1);
end.
"""
        with self.assertRaises(TypeError):
            analyze_pascal(src)

    def test_mixed_numeric_types(self):
        src = """
program t;
var
  i: integer;
begin
  i := 1 + 1.0;
end.
"""
        with self.assertRaises(TypeError):
            analyze_pascal(src)

    def test_invalid_array_bounds_float(self):
        src = """
program t;
var
  a: array[1.5..3] of integer;
begin
  writeln(1);
end.
"""
        with self.assertRaises(SyntaxError):
            analyze_pascal(src)

    def test_invalid_array_bounds_order(self):
        src = """
program t;
var
  a: array[5..1] of integer;
begin
  writeln(1);
end.
"""
        with self.assertRaises(SyntaxError):
            analyze_pascal(src)

    def test_array_in_params_not_supported(self):
        src = """
program t;
function f(a: array[1..2] of integer): integer;
begin
  f := 1;
end;
begin
  f(1);
end.
"""
        with self.assertRaises(SyntaxError):
            analyze_pascal(src)

    def test_unknown_function(self):
        src = """
program t;
var
  x: integer;
begin
  x := foo(1);
end.
"""
        with self.assertRaises(NameError):
            analyze_pascal(src)


if __name__ == "__main__":
    unittest.main()
