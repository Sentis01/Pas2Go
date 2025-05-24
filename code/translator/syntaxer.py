from nodes import *
from lexer import *

class SyntaxAnalyzer:
    def __init__(self, tokens: list) -> None:
        self.tokens = tokens
        self.pos = 0
        self.current_token: Token = None
        self.advance()

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
        raise SyntaxError(f"Ожидается {token_type}, но получен {self.current_token.type if self.current_token else 'EOF'}")

    def parse_program(self) -> StatementNode:
        root = StatementNode()
        self.require('PROGRAM')
        program_name = self.require('IDENTIFIER').value
        self.require('SEMICOLON')

        if self.current_token.type == 'VAR':
            var_decls = self.parse_var_declaration()
            root.addNode(VarDeclarationNode(var_decls))

        self.require('BEGIN')
        while not self.match('END'):
            stmt = self.parse_statement()
            root.addNode(stmt)
            self.require('SEMICOLON')
        self.require('DOT')
        return root

    def parse_var_declaration(self) -> list:
        self.require('VAR')
        declarations = []
        while self.current_token.type == 'IDENTIFIER':
            var_name = self.current_token.value
            self.advance()
            self.require('COLON')
            # Исправлено: проверка типа
            if self.current_token.type not in ['INTEGER', 'STRING']:
                raise SyntaxError(f"Неверный тип переменной: {self.current_token.value}")
            var_type = self.current_token.value
            self.advance()
            declarations.append((var_name, var_type))
            self.require('SEMICOLON')
        return declarations

    def parse_statement(self) -> ExpressionNode:
        if self.current_token.type == 'IDENTIFIER':
            var_node = ValueNode(self.current_token)
            self.advance()
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

        else:
            raise SyntaxError(f"Неизвестный оператор: {self.current_token.type}")
        
    def parse_term(self) -> ExpressionNode:
        if self.current_token.type in ['NUMBER', 'IDENTIFIER', 'STRING']:
            node = ValueNode(self.current_token)
            self.advance()
            return node
        elif self.match('LPAR'):
            node = self.parse_expression()
            self.require('RPAR')
            return node
        else:
            raise SyntaxError(f"Недопустимый терм: {self.current_token.type}")

    def parse_expression(self) -> ExpressionNode:
        node = self.parse_term()
        while self.current_token and self.current_token.type == 'OPERATOR':
            op_token = self.current_token
            self.advance()
            node = BinOperatorNode(op_token, node, self.parse_term())
        return node
    
    def getTextTree(self, root: StatementNode) -> str:
        textTree = ""
        for node in root.codeStrings:
            textTree += self.getTextNode(node)
        return textTree

    def getTextNode(self, node: ExpressionNode, level: int = 0) -> str:
        indent = '  ' * level
        result = ""

        if isinstance(node, VarDeclarationNode):
            result += f"{indent}VarDeclaration:\n"
            for name, type_ in node.declarations:
                result += f"{indent}  {name} : {type_}\n"

        elif isinstance(node, BinOperatorNode):
            result += f"{indent}BinOp: {node.operator.value}\n"
            result += self.getTextNode(node.leftNode, level + 1)
            result += self.getTextNode(node.rightNode, level + 1)

        elif isinstance(node, ProcedureCallNode):
            result += f"{indent}ProcedureCall: {node.name}\n"
            for arg in node.args:
                result += self.getTextNode(arg, level + 1)

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

        return result
    
    def parse_for_statement(self) -> ExpressionNode:
        self.require('FOR')
        var_token = self.require('IDENTIFIER')
        self.require('ASSIGN')
        start_expr = self.parse_expression()

        direction = self.current_token.type
        if direction not in ['TO', 'DOWNTO']:
            raise SyntaxError(f"Ожидается TO или DOWNTO, получено {self.current_token.type}")
        self.advance()

        end_expr = self.parse_expression()
        self.require('DO')

        body = BlockNode()
        if self.match('BEGIN'):
            while not self.match('END'):
                body.addNode(self.parse_statement())
                self.require('SEMICOLON')
        else:
            body.addNode(self.parse_statement())

        return ForStatementNode(var_token, start_expr, end_expr, direction, body)
