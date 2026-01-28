from nodes import *
from lexer import *

class SyntaxAnalyzer:
    def __init__(self, tokens: list) -> None:
        self.tokens = tokens
        self.pos = 0
        self.current_token: Token = None
        self.advance()

    def peek(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def advance(self) -> None:
        if self.pos < len(self.tokens):
            self.current_token = self.tokens[self.pos]
            self.pos += 1
        else:
            self.current_token = None

    def match(self, token_type: str) -> bool:
        if self.current_token and self.current_token.type == token_type:
            self.advance()
            return True
        return False

    def require(self, token_type: str) -> Token:
        if self.current_token and self.current_token.type == token_type:
            token = self.current_token
            self.advance()
            return token
        raise SyntaxError(self.format_error(
            f"Ожидается {token_type}, но получен {self.current_token.type if self.current_token else 'EOF'}",
            self.current_token
        ))

    def format_error(self, message: str, token: Token = None) -> str:
        if token:
            return f"{message} (строка {token.line}, колонка {token.column})"
        return f"{message} (строка ?, колонка ?)"

    def parse_program(self) -> ProgramNode:
        self.require('PROGRAM')
        program_name = self.require('IDENTIFIER').value
        self.require('SEMICOLON')

        global_decls = []
        routines = []

        if self.current_token and self.current_token.type == 'VAR':
            global_decls = self.parse_var_declaration()

        while self.current_token and self.current_token.type in ['FUNCTION', 'PROCEDURE']:
            routines.append(self.parse_routine_declaration())

        main_block = self.parse_block()
        self.require('DOT')
        return ProgramNode(global_decls, routines, main_block)

    def parse_routine_declaration(self) -> ExpressionNode:
        if self.current_token.type == 'FUNCTION':
            self.advance()
            name = self.require('IDENTIFIER').value
            params = self.parse_params()
            self.require('COLON')
            if self.current_token.type not in ['INTEGER', 'STRING', 'BOOL']:
                raise SyntaxError(self.format_error(
                    f"Неверный тип возвращаемого значения: {self.current_token.value}",
                    self.current_token
                ))
            return_type = self.current_token.value.lower()
            if self.current_token.type == 'BOOL':
                return_type = 'boolean'
            self.advance()
            self.require('SEMICOLON')

            local_decls = []
            if self.current_token and self.current_token.type == 'VAR':
                local_decls = self.parse_var_declaration()

            body = self.parse_block()
            self.require('SEMICOLON')
            return FunctionDeclNode(name, params, return_type, local_decls, body)

        elif self.current_token.type == 'PROCEDURE':
            self.advance()
            name = self.require('IDENTIFIER').value
            params = self.parse_params()
            self.require('SEMICOLON')

            local_decls = []
            if self.current_token and self.current_token.type == 'VAR':
                local_decls = self.parse_var_declaration()

            body = self.parse_block()
            self.require('SEMICOLON')
            return ProcedureDeclNode(name, params, local_decls, body)

        else:
            raise SyntaxError(self.format_error(
                f"Ожидается FUNCTION или PROCEDURE, получено {self.current_token.type}",
                self.current_token
            ))

    def parse_var_declaration(self) -> list:
        self.require('VAR')
        declarations = []
        while self.current_token.type == 'IDENTIFIER':
            names = [self.current_token.value]
            self.advance()
            while self.match('COMMA'):
                names.append(self.require('IDENTIFIER').value)
            self.require('COLON')
            # Исправлено: проверка типа
            var_type = self.parse_type(allow_array=True)
            for var_name in names:
                declarations.append((var_name, var_type))
            self.require('SEMICOLON')
        return declarations

    def parse_params(self) -> list:
        params = []
        if not self.match('LPAR'):
            return params

        if self.current_token.type == 'RPAR':
            self.advance()
            return params

        while True:
            names = [self.require('IDENTIFIER').value]
            while self.match('COMMA'):
                names.append(self.require('IDENTIFIER').value)
            self.require('COLON')
            param_type = self.parse_type(allow_array=False)
            for name in names:
                params.append((name, param_type))
            if self.match('SEMICOLON'):
                continue
            break

        self.require('RPAR')
        return params

    def parse_statement(self) -> ExpressionNode:
        if self.current_token.type == 'IDENTIFIER':
            if self.peek() and self.peek().type == 'LPAR':
                return self.parse_procedure_call()
            var_node = self.parse_lvalue()
            self.require('ASSIGN')
            expr_node = self.parse_expression()
            return BinOperatorNode(Token('ASSIGN', ':=', 0, 0), var_node, expr_node)

        elif self.current_token.type == 'WRITELN':
            self.advance()
            self.require('LPAR')
            args = []
            while not self.match('RPAR'):
                args.append(self.parse_expression())
                if self.match('COMMA'):
                    continue
            return ProcedureCallNode('writeln', args)

        elif self.current_token.type == 'IF':
            self.advance()
            condition = self.parse_expression()
            self.require('THEN')
            then_block = BlockNode()
            if self.match('BEGIN'):
                while not self.match('END'):
                    then_block.addNode(self.parse_statement())
                    self.require('SEMICOLON')
            else:
                then_block.addNode(self.parse_statement())

            else_block = None
            if self.match('ELSE'):
                else_block = BlockNode()
                if self.match('BEGIN'):
                    while not self.match('END'):
                        else_block.addNode(self.parse_statement())
                        self.require('SEMICOLON')
                else:
                    else_block.addNode(self.parse_statement())

            return IfStatementNode(condition, then_block, else_block)

        elif self.current_token.type == 'WHILE':
            self.advance()
            condition = self.parse_expression()
            self.require('DO')
            body = BlockNode()
            if self.match('BEGIN'):
                while not self.match('END'):
                    body.addNode(self.parse_statement())
                    self.require('SEMICOLON')
            else:
                body.addNode(self.parse_statement())
            return WhileStatementNode(condition, body)
        
        elif self.current_token.type == 'FOR':
            return self.parse_for_statement()
        
        elif self.current_token.type == 'REPEAT':
            return self.parse_repeat_until_statement()
        
        elif self.current_token.type == 'CASE':
            return self.parse_case_statement()

        else:
            raise SyntaxError(self.format_error(
                f"Неизвестный оператор: {self.current_token.type}",
                self.current_token
            ))
        
    def parse_term(self) -> ExpressionNode:
        if self.current_token.type in ['NUMBER', 'STRING', 'BOOL_LIT', 'CHAR_LIT']:
            node = ValueNode(self.current_token)
            self.advance()
            return node
        if self.current_token.type == 'IDENTIFIER':
            if self.peek() and self.peek().type == 'LPAR':
                return self.parse_function_call()
            if self.peek() and self.peek().type == 'LBRACKET':
                return self.parse_array_access()
            node = ValueNode(self.current_token)
            self.advance()
            return node
        elif self.match('LPAR'):
            node = self.parse_expression()
            self.require('RPAR')
            return node
        else:
            raise SyntaxError(self.format_error(
                f"Недопустимый терм: {self.current_token.type}",
                self.current_token
            ))

    def parse_expression(self) -> ExpressionNode:
        return self.parse_or()

    def parse_or(self) -> ExpressionNode:
        node = self.parse_and()
        while self.current_token and self.current_token.type == 'OPERATOR' and self.current_token.value.lower() in ['or', 'xor']:
            op_token = self.current_token
            self.advance()
            node = BinOperatorNode(op_token, node, self.parse_and())
        return node

    def parse_and(self) -> ExpressionNode:
        node = self.parse_compare()
        while self.current_token and self.current_token.type == 'OPERATOR' and self.current_token.value.lower() == 'and':
            op_token = self.current_token
            self.advance()
            node = BinOperatorNode(op_token, node, self.parse_compare())
        return node

    def parse_compare(self) -> ExpressionNode:
        node = self.parse_add()
        while self.current_token and self.current_token.type == 'OPERATOR' and self.current_token.value in ['==', '!=', '<', '>', '<=', '>=', '=', '<>']:
            op_token = self.current_token
            self.advance()
            node = BinOperatorNode(op_token, node, self.parse_add())
        return node

    def parse_add(self) -> ExpressionNode:
        node = self.parse_mul()
        while self.current_token and self.current_token.type == 'OPERATOR' and self.current_token.value in ['+', '-']:
            op_token = self.current_token
            self.advance()
            node = BinOperatorNode(op_token, node, self.parse_mul())
        return node

    def parse_mul(self) -> ExpressionNode:
        node = self.parse_unary()
        while self.current_token and self.current_token.type == 'OPERATOR' and self.current_token.value in ['*', '/', 'div', 'mod']:
            op_token = self.current_token
            self.advance()
            node = BinOperatorNode(op_token, node, self.parse_unary())
        return node

    def parse_unary(self) -> ExpressionNode:
        if self.current_token and self.current_token.type == 'NOT':
            op_token = self.current_token
            self.advance()
            return UnaryOperatorNode(op_token, self.parse_unary())
        return self.parse_term()
    
    def getTextTree(self, root: StatementNode) -> str:
        textTree = ""
        if isinstance(root, ProgramNode):
            if root.declarations:
                textTree += "VarDeclaration:\n"
                for name, type_ in root.declarations:
                    textTree += f"  {name} : {self.format_type(type_)}\n"
            for routine in root.routines:
                textTree += self.getTextNode(routine)
            textTree += "MainBlock:\n"
            for stmt in root.main_block.body:
                textTree += self.getTextNode(stmt, 1)
        else:
            for node in root.codeStrings:
                textTree += self.getTextNode(node)
        return textTree

    def getTextNode(self, node: ExpressionNode, level: int = 0) -> str:
        indent = '  ' * level
        result = ""

        if isinstance(node, VarDeclarationNode):
            result += f"{indent}VarDeclaration:\n"
            for name, type_ in node.declarations:
                result += f"{indent}  {name} : {self.format_type(type_)}\n"

        elif isinstance(node, BinOperatorNode):
            result += f"{indent}BinOp: {node.operator.value}\n"
            result += self.getTextNode(node.leftNode, level + 1)
            result += self.getTextNode(node.rightNode, level + 1)

        elif isinstance(node, UnaryOperatorNode):
            result += f"{indent}UnaryOp: {node.operator.value}\n"
            result += self.getTextNode(node.operand, level + 1)

        elif isinstance(node, ProcedureCallNode):
            result += f"{indent}ProcedureCall: {node.name}\n"
            for arg in node.args:
                result += self.getTextNode(arg, level + 1)

        elif isinstance(node, FunctionCallNode):
            result += f"{indent}FunctionCall: {node.name}\n"
            for arg in node.args:
                result += self.getTextNode(arg, level + 1)

        elif isinstance(node, ArrayAccessNode):
            result += f"{indent}ArrayAccess: {node.name}\n"
            result += self.getTextNode(node.index, level + 1)

        elif isinstance(node, ValueNode):
            result += f"{indent}Value: {node.value.value}\n"

        elif isinstance(node, IfStatementNode):
            result += f"{indent}If:\n"
            result += self.getTextNode(node.condition, level + 1)
            result += f"{indent}Then:\n"
            for stmt in node.then_block.body:
                result += self.getTextNode(stmt, level + 2)
            if node.else_block:
                result += f"{indent}Else:\n"
                for stmt in node.else_block.body:
                    result += self.getTextNode(stmt, level + 2)

        elif isinstance(node, WhileStatementNode):
            result += f"{indent}While:\n"
            result += self.getTextNode(node.condition, level + 1)
            result += f"{indent}Body:\n"
            for stmt in node.body.body:
                result += self.getTextNode(stmt, level + 2)

        elif isinstance(node, RepeatUntilStatementNode):
            result += f"{indent}RepeatUntil:\n"
            result += f"{indent}  Body:\n"
            for stmt in node.body.body:
                result += self.getTextNode(stmt, level + 2)
            result += f"{indent}  Until:\n"
            result += self.getTextNode(node.condition, level + 2)

        elif isinstance(node, CaseStatementNode):
            result += f"{indent}Case:\n"
            result += self.getTextNode(node.expression, level + 1)
            for labels, block in node.cases:
                result += f"{indent}  When:\n"
                for label in labels:
                    result += self.getTextNode(label, level + 2)
                result += f"{indent}  Do:\n"
                for stmt in block.body:
                    result += self.getTextNode(stmt, level + 2)
            if node.else_block:
                result += f"{indent}  Else:\n"
                for stmt in node.else_block.body:
                    result += self.getTextNode(stmt, level + 2)

        elif isinstance(node, FunctionDeclNode):
            result += f"{indent}Function: {node.name}\n"
            if node.params:
                result += f"{indent}  Params:\n"
                for name, type_ in node.params:
                    result += f"{indent}    {name} : {self.format_type(type_)}\n"
            result += f"{indent}  Return: {node.return_type}\n"
            if node.local_decls:
                result += f"{indent}  Locals:\n"
                for name, type_ in node.local_decls:
                    result += f"{indent}    {name} : {self.format_type(type_)}\n"
            result += f"{indent}  Body:\n"
            for stmt in node.body.body:
                result += self.getTextNode(stmt, level + 2)

        elif isinstance(node, ProcedureDeclNode):
            result += f"{indent}Procedure: {node.name}\n"
            if node.params:
                result += f"{indent}  Params:\n"
                for name, type_ in node.params:
                    result += f"{indent}    {name} : {self.format_type(type_)}\n"
            if node.local_decls:
                result += f"{indent}  Locals:\n"
                for name, type_ in node.local_decls:
                    result += f"{indent}    {name} : {self.format_type(type_)}\n"
            result += f"{indent}  Body:\n"
            for stmt in node.body.body:
                result += self.getTextNode(stmt, level + 2)

        return result
    
    def parse_for_statement(self) -> ExpressionNode:
        self.require('FOR')
        var_token = self.require('IDENTIFIER')
        self.require('ASSIGN')
        start_expr = self.parse_expression()

        direction = self.current_token.type
        if direction not in ['TO', 'DOWNTO']:
            raise SyntaxError(self.format_error(
                f"Ожидается TO или DOWNTO, получено {self.current_token.type}",
                self.current_token
            ))
        self.advance()

        end_expr = self.parse_expression()
        self.require('DO')
        if self.current_token.type == 'BEGIN':
            body = self.parse_block()
        else:
            body = BlockNode()
            body.addNode(self.parse_statement())
        return ForStatementNode(var_token, start_expr, end_expr, direction, body)

    def parse_repeat_until_statement(self) -> ExpressionNode:
        self.require('REPEAT')
        body = BlockNode()
        while not self.match('UNTIL'):
            body.addNode(self.parse_statement())
            self.require('SEMICOLON')
        condition = self.parse_expression()
        return RepeatUntilStatementNode(body, condition)
    
    def parse_block(self) -> BlockNode:
        """Парсит  begin … end  с опциональными ; перед END."""
        body = BlockNode()
        self.require('BEGIN')

        while True:
            # Если сразу END — пустой блок
            if self.current_token.type == 'END':
                self.advance()          # съесть END
                break

            # читаем очередной оператор
            body.addNode(self.parse_statement())

            # если дальше END — ; не требуется
            if self.current_token.type == 'END':
                self.advance()          # съесть END
                break

            # иначе должен быть ;
            self.require('SEMICOLON')

        return body

    def parse_case_statement(self) -> CaseStatementNode:
        self.require('CASE')
        expression = self.parse_expression()
        self.require('OF')
        cases = []

        while self.current_token and self.current_token.type not in ['ELSE', 'END']:
            labels = [self.parse_case_label()]
            while self.match('COMMA'):
                labels.append(self.parse_case_label())
            self.require('COLON')

            if self.current_token.type == 'BEGIN':
                block = self.parse_block()
            else:
                block = BlockNode()
                block.addNode(self.parse_statement())

            self.require('SEMICOLON')
            cases.append((labels, block))

        else_block = None
        if self.match('ELSE'):
            if self.current_token.type == 'BEGIN':
                else_block = self.parse_block()
            else:
                else_block = BlockNode()
                else_block.addNode(self.parse_statement())
            if self.current_token and self.current_token.type == 'SEMICOLON':
                self.advance()

        self.require('END')
        return CaseStatementNode(expression, cases, else_block)

    def parse_case_label(self) -> ExpressionNode:
        if self.current_token.type in ['NUMBER', 'STRING', 'BOOL_LIT', 'CHAR_LIT', 'IDENTIFIER']:
            node = ValueNode(self.current_token)
            self.advance()
            return node
        raise SyntaxError(self.format_error(
            f"Неверная метка CASE: {self.current_token.type}",
            self.current_token
        ))

    def parse_lvalue(self) -> ExpressionNode:
        if self.current_token.type != 'IDENTIFIER':
            raise SyntaxError(self.format_error(
                f"Ожидается идентификатор, получено {self.current_token.type}",
                self.current_token
            ))
        if self.peek() and self.peek().type == 'LBRACKET':
            return self.parse_array_access()
        node = ValueNode(self.current_token)
        self.advance()
        return node

    def parse_array_access(self) -> ArrayAccessNode:
        name_token = self.require('IDENTIFIER')
        name = name_token.value
        self.require('LBRACKET')
        index = self.parse_expression()
        self.require('RBRACKET')
        return ArrayAccessNode(name, index, name_token)

    def parse_type(self, allow_array: bool) -> any:
        if self.current_token.type == 'ARRAY':
            if not allow_array:
                raise SyntaxError(self.format_error("Массивы не поддерживаются в параметрах", self.current_token))
            self.advance()
            self.require('LBRACKET')
            low_tok = self.require('NUMBER')
            if '.' in low_tok.value:
                raise SyntaxError(self.format_error("Нижняя граница массива должна быть integer", low_tok))
            self.require('RANGE')
            high_tok = self.require('NUMBER')
            if '.' in high_tok.value:
                raise SyntaxError(self.format_error("Верхняя граница массива должна быть integer", high_tok))
            self.require('RBRACKET')
            self.require('OF')
            elem_type = self.parse_type(allow_array=False)
            low = int(low_tok.value)
            high = int(high_tok.value)
            if low > high:
                raise SyntaxError(self.format_error("Нижняя граница массива больше верхней", low_tok))
            return {'kind': 'array', 'low': low, 'high': high, 'elem': elem_type}

        if self.current_token.type in ['INTEGER', 'STRING', 'BOOL', 'FLOAT', 'CHAR']:
            var_type = self.current_token.value.lower()
            if self.current_token.type == 'BOOL':
                var_type = 'boolean'
            self.advance()
            return var_type

        raise SyntaxError(self.format_error(
            f"Неверный тип: {self.current_token.value}",
            self.current_token
        ))

    def format_type(self, type_) -> str:
        if isinstance(type_, dict) and type_.get('kind') == 'array':
            return f"array[{type_['low']}..{type_['high']}] of {self.format_type(type_['elem'])}"
        return str(type_)

    def parse_procedure_call(self) -> ProcedureCallNode:
        name_token = self.require('IDENTIFIER')
        name = name_token.value
        self.require('LPAR')
        args = []
        while not self.match('RPAR'):
            args.append(self.parse_expression())
            if self.match('COMMA'):
                continue
        return ProcedureCallNode(name, args, name_token)

    def parse_function_call(self) -> FunctionCallNode:
        name_token = self.require('IDENTIFIER')
        name = name_token.value
        self.require('LPAR')
        args = []
        while not self.match('RPAR'):
            args.append(self.parse_expression())
            if self.match('COMMA'):
                continue
        return FunctionCallNode(name, args, name_token)
