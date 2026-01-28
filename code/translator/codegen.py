from lexer import *
from nodes import *

toGo = {
    'writeln': 'fmt.Println',
    'integer': 'int',
    'string': 'string',
    'boolean': 'bool',
    'float': 'float64',
    'char': 'rune',
    'and': '&&',
    'or': '||',
    'xor': '!=',
    'not': '!',
    '=': '==',
    '<>': '!=',
    ':=': '=',
}

MARGIN = '\t'

class CodeGenerator:
    def __init__(self) -> None:
        self.output = ''
        self.needs_fmt_import = False
        self.current_function = None
        self.array_scopes = [{}]

    def push_scope(self):
        self.array_scopes.append({})

    def pop_scope(self):
        self.array_scopes.pop()

    def register_array(self, name: str, low: int):
        self.array_scopes[-1][name] = low

    def lookup_array_low(self, name: str):
        for scope in reversed(self.array_scopes):
            if name in scope:
                return scope[name]
        return None

    def format_type(self, type_) -> str:
        if isinstance(type_, dict) and type_.get('kind') == 'array':
            size = type_['high'] - type_['low'] + 1
            elem = self.format_type(type_['elem'])
            return f'[{size}]{elem}'
        return toGo.get(type_, type_)

    def genVarDeclaration(self, node) -> str:
        decls = []
        for name, type_ in node.declarations:
            if isinstance(type_, dict) and type_.get('kind') == 'array':
                self.register_array(name, type_['low'])
            decls.append(f'var {name} {self.format_type(type_)}')
        return '\n'.join(decls) + '\n'

    def genProcedureCall(self, node) -> str:
        args = ', '.join(self.genCode(arg) for arg in node.args)
        if node.name.lower() == 'writeln':
            self.needs_fmt_import = True
            return f'fmt.Println({args})'
        return f'{node.name}({args})'

    def genFunctionCall(self, node) -> str:
        args = ', '.join(self.genCode(arg) for arg in node.args)
        return f'{node.name}({args})'

    def genBinOperator(self, node) -> str:
        left = self.genCode(node.leftNode)
        right = self.genCode(node.rightNode)
        op_key = node.operator.value.lower()
        op = toGo.get(op_key, node.operator.value)
        if op_key == ':=' and self.current_function and left == self.current_function:
            return f'return {right}'
        return f'{left} {op} {right}'

    def genUnaryOperator(self, node) -> str:
        op_key = node.operator.value.lower()
        op = toGo.get(op_key, node.operator.value)
        operand = self.genCode(node.operand)
        return f'{op}{operand}'

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
        code = MARGIN * level + f'for {condition} {{\n'
        for stmt in node.body.body:
            code += self.genCode(stmt, level + 1) + '\n'
        return code + MARGIN * level + '}'
    
    def genDoWhileStatement(self, node, level) -> str:
        indent = MARGIN * level
        code = indent + 'for {\n'
        for stmt in node.body.body:
            code += self.genCode(stmt, level + 1) + '\n'
        condition = self.genCode(node.condition)
        code += indent + f'\tif !({condition}) {{ break }}\n'
        code += indent + '}'
        return code

    def genRepeatUntilStatement(self, node, level) -> str:
        indent = MARGIN * level
        code = indent + 'for {\n'
        for stmt in node.body.body:
            code += self.genCode(stmt, level + 1) + '\n'
        condition = self.genCode(node.condition)
        code += indent + f'\tif {condition} {{ break }}\n'
        code += indent + '}'
        return code

    def genCaseStatement(self, node, level) -> str:
        expr = self.genCode(node.expression)
        indent = MARGIN * level
        code = indent + f'switch {expr} {{\n'
        for labels, block in node.cases:
            labels_code = ', '.join(self.genCode(label) for label in labels)
            code += indent + f'case {labels_code}:\n'
            for stmt in block.body:
                code += self.genCode(stmt, level + 1) + '\n'
        if node.else_block:
            code += indent + 'default:\n'
            for stmt in node.else_block.body:
                code += self.genCode(stmt, level + 1) + '\n'
        code += indent + '}'
        return code
    
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

        elif isinstance(node, UnaryOperatorNode):
            return MARGIN * level + self.genUnaryOperator(node)

        elif isinstance(node, FunctionCallNode):
            return self.genFunctionCall(node)

        elif isinstance(node, ArrayAccessNode):
            return self.genArrayAccess(node)

        elif isinstance(node, IfStatementNode):
            return self.genIfStatement(node, level)

        elif isinstance(node, WhileStatementNode):
            return self.genWhileStatement(node, level)

        elif isinstance(node, ForStatementNode):
            return self.genForStatement(node, level)
        
        elif isinstance(node, DoWhileStatementNode):
            return self.genDoWhileStatement(node, level)
        
        elif isinstance(node, RepeatUntilStatementNode):
            return self.genRepeatUntilStatement(node, level)

        elif isinstance(node, CaseStatementNode):
            return self.genCaseStatement(node, level)

        else:
            return ''

    def generate(self, root) -> str:
        self.output = 'package main\n\n'
        import_line = ''

        if isinstance(root, ProgramNode):
            self.array_scopes = [{}]
            if root.declarations:
                for name, type_ in root.declarations:
                    if isinstance(type_, dict) and type_.get('kind') == 'array':
                        self.register_array(name, type_['low'])
                self.output += '\n'.join(
                    f'var {name} {self.format_type(type_)}' for name, type_ in root.declarations
                ) + '\n\n'

            for routine in root.routines:
                self.output += self.genRoutine(routine) + '\n\n'

            self.output += 'func main() {\n'
            self.push_scope()
            for stmt in root.main_block.body:
                self.output += self.genCode(stmt, 1) + '\n'
            self.pop_scope()
            self.output += '}'
        else:
            self.output += 'func main() {\n'
            for node in root.codeStrings:
                self.output += self.genCode(node, 1) + '\n'
            self.output += '}'

        if self.needs_fmt_import:
            import_line = 'import "fmt"\n\n'
        self.output = 'package main\n\n' + import_line + self.output.split('\n\n', 1)[1]
        return self.output

    def genRoutine(self, node) -> str:
        if isinstance(node, FunctionDeclNode):
            return self.genFunctionDecl(node)
        if isinstance(node, ProcedureDeclNode):
            return self.genProcedureDecl(node)
        return ''

    def genFunctionDecl(self, node) -> str:
        params = ', '.join(f'{name} {toGo.get(type_, type_)}' for name, type_ in node.params)
        ret_type = toGo.get(node.return_type, node.return_type)
        code = f'func {node.name}({params}) {ret_type} {{\n'
        if node.local_decls:
            self.push_scope()
            for name, type_ in node.local_decls:
                if isinstance(type_, dict) and type_.get('kind') == 'array':
                    self.register_array(name, type_['low'])
                code += MARGIN + f'var {name} {self.format_type(type_)}\n'
        else:
            self.push_scope()
        prev_function = self.current_function
        self.current_function = node.name
        for stmt in node.body.body:
            code += self.genCode(stmt, 1) + '\n'
        self.current_function = prev_function
        self.pop_scope()
        code += '}'
        return code

    def genProcedureDecl(self, node) -> str:
        params = ', '.join(f'{name} {toGo.get(type_, type_)}' for name, type_ in node.params)
        code = f'func {node.name}({params}) {{\n'
        self.push_scope()
        if node.local_decls:
            for name, type_ in node.local_decls:
                if isinstance(type_, dict) and type_.get('kind') == 'array':
                    self.register_array(name, type_['low'])
                code += MARGIN + f'var {name} {self.format_type(type_)}\n'
        prev_function = self.current_function
        self.current_function = None
        for stmt in node.body.body:
            code += self.genCode(stmt, 1) + '\n'
        self.current_function = prev_function
        self.pop_scope()
        code += '}'
        return code

    def genArrayAccess(self, node) -> str:
        index = self.genCode(node.index)
        low = self.lookup_array_low(node.name)
        if low is None or low == 0:
            return f'{node.name}[{index}]'
        return f'{node.name}[({index}) - {low}]'
