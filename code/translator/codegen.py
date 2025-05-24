from lexer import *
from nodes import *

toGo = {
    'writeln': 'fmt.Println',
    'integer': 'int',
    'string': 'string',
    'and': '&&',
    'or': '||',
    ':=': '=',
}

MARGIN = '\t'

class CodeGenerator:
    def __init__(self) -> None:
        self.output = ''
        self.needs_fmt_import = False

    def genVarDeclaration(self, node) -> str:
        decls = [f'var {name} {toGo.get(type_, type_)}' for name, type_ in node.declarations]
        return '\n'.join(decls) + '\n'

    def genProcedureCall(self, node) -> str:
        self.needs_fmt_import = True
        args = ', '.join(self.genCode(arg) for arg in node.args)
        return f'fmt.Println({args})'

    def genBinOperator(self, node) -> str:
        left = self.genCode(node.leftNode)
        right = self.genCode(node.rightNode)
        op = toGo.get(node.operator.value, node.operator.value)
        return f'{left} {op} {right}'

    def genBlock(self, node, level) -> str:
        code = '{\n'
        for stmt in node.body:
            code += self.genCode(stmt, level + 1) + '\n'
        return code + MARGIN * level + '}'

    def genIfStatement(self, node, level) -> str:
        condition = self.genCode(node.condition, level)
        code = MARGIN * level + f'if {condition} {{\n'
        for stmt in node.then_block.body:
            code += self.genCode(stmt, level + 1) + '\n'
        code += MARGIN * level + '}'
        
        if node.else_block:
            code += ' else {\n'
            for stmt in node.else_block.body:
                code += self.genCode(stmt, level + 1) + '\n'
            code += MARGIN * level + '}'
        return code

    def genWhileStatement(self, node, level) -> str:
        condition = self.genCode(node.condition, level)
        code = MARGIN * level + f'for {condition} \n'
        for stmt in node.body.body:
            code += self.genCode(stmt, level + 1) + '\n'
        return code + MARGIN * level + '}'
    
    def genForStatement(self, node, level) -> str:
        var = node.var_token.value
        start = self.genCode(node.start_expr)
        end = self.genCode(node.end_expr)
        indent = MARGIN * level

        loop = ''
        if node.direction == 'TO':
            loop = f'for {var} := {start}; {var} <= {end}; {var}++ {{\n'
        else:  # DOWNTO
            loop = f'for {var} := {start}; {var} >= {end}; {var}-- {{\n'

        code = indent + loop
        for stmt in node.body.body:
            code += self.genCode(stmt, level + 1) + '\n'
        code += indent + '}'
        return code

    def genCode(self, node, level=0) -> str:
        if isinstance(node, VarDeclarationNode):
            return MARGIN * level + self.genVarDeclaration(node).strip()

        elif isinstance(node, BinOperatorNode):
            # Убираем точку с запятой для выражений внутри вызовов функций
            return MARGIN * level + self.genBinOperator(node)  # <-- удалено ';'

        elif isinstance(node, ProcedureCallNode):
            return MARGIN * level + self.genProcedureCall(node) + ';'  # <-- добавляем ';' здесь

        elif isinstance(node, ValueNode):
            return node.value.value

        elif isinstance(node, IfStatementNode):
            return self.genIfStatement(node, level)

        elif isinstance(node, WhileStatementNode):
            return self.genWhileStatement(node, level)

        elif isinstance(node, ForStatementNode):
            return self.genForStatement(node, level)

        else:
            return ''

    def generate(self, root) -> str:
        self.output = 'package main\n\n'
        self.output += 'import "fmt"\n\n'

        self.output += 'func main() {\n'
        for node in root.codeStrings:
            self.output += self.genCode(node, 1) + '\n'
        self.output += '}'
        return self.output