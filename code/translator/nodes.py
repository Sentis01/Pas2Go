from lexer import Token


class ExpressionNode:
    pass


class VarDeclarationNode(ExpressionNode):
    def __init__(self, declarations: list) -> None:
        self.declarations = declarations


class ProcedureCallNode(ExpressionNode):
    def __init__(self, name: str, args: list, token: Token = None) -> None:
        self.name = name
        self.args = args
        self.token = token


class ValueNode(ExpressionNode):
    def __init__(self, value: Token) -> None:
        self.value = value


class BinOperatorNode(ExpressionNode):
    def __init__(
        self,
        operator: Token,
        left_node: ExpressionNode,
        right_node: ExpressionNode,
    ) -> None:
        self.operator = operator
        self.leftNode = left_node
        self.rightNode = right_node


class UnaryOperatorNode(ExpressionNode):
    def __init__(self, operator: Token, operand: ExpressionNode) -> None:
        self.operator = operator
        self.operand = operand


class BlockNode(ExpressionNode):
    def __init__(self) -> None:
        self.body = []

    def addNode(self, node: ExpressionNode) -> None:
        self.body.append(node)


class IfStatementNode(ExpressionNode):
    def __init__(
        self,
        condition: ExpressionNode,
        then_block: BlockNode,
        else_block: BlockNode = None,
    ) -> None:
        self.condition = condition
        self.then_block = then_block
        self.else_block = else_block


class WhileStatementNode(ExpressionNode):
    def __init__(self, condition: ExpressionNode, body: BlockNode) -> None:
        self.condition = condition
        self.body = body


class StatementNode(ExpressionNode):
    def __init__(self) -> None:
        self.codeStrings = []

    def addNode(self, node: ExpressionNode) -> None:
        self.codeStrings.append(node)


class ProgramNode(ExpressionNode):
    def __init__(
        self,
        declarations: list,
        routines: list,
        main_block: BlockNode,
    ) -> None:
        self.declarations = declarations
        self.routines = routines
        self.main_block = main_block


class FunctionDeclNode(ExpressionNode):
    def __init__(
        self,
        name: str,
        params: list,
        return_type: str,
        local_decls: list,
        body: BlockNode,
    ) -> None:
        self.name = name
        self.params = params
        self.return_type = return_type
        self.local_decls = local_decls
        self.body = body


class ProcedureDeclNode(ExpressionNode):
    def __init__(
        self,
        name: str,
        params: list,
        local_decls: list,
        body: BlockNode,
    ) -> None:
        self.name = name
        self.params = params
        self.local_decls = local_decls
        self.body = body


class FunctionCallNode(ExpressionNode):
    def __init__(self, name: str, args: list, token: Token = None) -> None:
        self.name = name
        self.args = args
        self.token = token


class ArrayAccessNode(ExpressionNode):
    def __init__(
        self,
        name: str,
        index: ExpressionNode,
        token: Token = None,
    ) -> None:
        self.name = name
        self.index = index
        self.token = token


class ForStatementNode(ExpressionNode):
    def __init__(
        self,
        var_token: Token,
        start_expr: ExpressionNode,
        end_expr: ExpressionNode,
        direction: str,
        body: BlockNode,
    ) -> None:
        self.var_token = var_token
        self.start_expr = start_expr
        self.end_expr = end_expr
        self.direction = direction
        self.body = body


class DoWhileStatementNode(ExpressionNode):
    def __init__(self, body: BlockNode, condition: ExpressionNode) -> None:
        self.body = body
        self.condition = condition


class RepeatUntilStatementNode(ExpressionNode):
    def __init__(self, body: BlockNode, condition: ExpressionNode) -> None:
        self.body = body
        self.condition = condition


class CaseStatementNode(ExpressionNode):
    def __init__(
        self,
        expression: ExpressionNode,
        cases: list,
        else_block: BlockNode = None,
    ) -> None:
        self.expression = expression
        self.cases = cases
        self.else_block = else_block
