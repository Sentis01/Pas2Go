from lexer import *

class ExpressionNode:
    pass

class VarDeclarationNode(ExpressionNode):
    def __init__(self, declarations: list) -> None:
        self.declarations = declarations

class ProcedureCallNode(ExpressionNode):
    def __init__(self, name: str, args: list):
        self.name = name
        self.args = args

class ValueNode(ExpressionNode):
    def __init__(self, value: Token) -> None:
        self.value = value

class BinOperatorNode(ExpressionNode):
    def __init__(self, operator: Token, leftNode: ExpressionNode, rightNode: ExpressionNode) -> None:
        self.operator = operator
        self.leftNode = leftNode
        self.rightNode = rightNode

class BlockNode(ExpressionNode):
    def __init__(self):
        self.body = []

    def addNode(self, node: ExpressionNode):
        self.body.append(node)

class IfStatementNode(ExpressionNode):
    def __init__(self, condition: ExpressionNode, then_block: BlockNode, else_block: BlockNode = None):
        self.condition = condition
        self.then_block = then_block
        self.else_block = else_block

class WhileStatementNode(ExpressionNode):
    def __init__(self, condition: ExpressionNode, body: BlockNode):
        self.condition = condition
        self.body = body

class StatementNode(ExpressionNode):
    def __init__(self) -> None:
        self.codeStrings = []

    def addNode(self, node: ExpressionNode):
        self.codeStrings.append(node)

class ForStatementNode(ExpressionNode):
    def __init__(self, var_token: Token, start_expr: ExpressionNode, end_expr: ExpressionNode, direction: str, body: BlockNode):
        self.var_token = var_token
        self.start_expr = start_expr
        self.end_expr = end_expr
        self.direction = direction
        self.body = body