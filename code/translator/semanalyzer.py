from nodes import *

class SemanticAnalyzer:
    def __init__(self) -> None:
        self.variables = {}
        self.current_scope = "global"
        self.in_loop = False

    def check_program(self, root: StatementNode):
        for node in root.codeStrings:
            self.check_node(node)

    def check_node(self, node: ExpressionNode):
        if isinstance(node, VarDeclarationNode):
            for var_name, var_type in node.declarations:
                if var_name in self.variables:
                    raise NameError(f"Переменная {var_name} уже объявлена")
                self.variables[var_name] = var_type

        elif isinstance(node, BinOperatorNode):
            if node.operator.type == 'ASSIGN':
                var_name = node.leftNode.value.value
                if var_name not in self.variables:
                    raise NameError(f"Переменная {var_name} не объявлена")
                expr_type = self.infer_type(node.rightNode)
                if expr_type != self.variables[var_name]:
                    raise TypeError(f"Тип {expr_type} не соответствует {self.variables[var_name]}")

        elif isinstance(node, IfStatementNode):
            self.check_condition(node.condition)
            for stmt in node.then_block.body:
                self.check_node(stmt)
            if node.else_block:
                for stmt in node.else_block.body:
                    self.check_node(stmt)

        elif isinstance(node, WhileStatementNode):
            self.check_condition(node.condition)
            self.in_loop = True
            for stmt in node.body.body:
                self.check_node(stmt)
            self.in_loop = False

        elif isinstance(node, ForStatementNode):
            var_name = node.var_token.value

            if var_name not in self.variables:
                raise NameError(f"Переменная {var_name} не объявлена")
            if self.variables[var_name] != 'integer':
                raise TypeError(f"Переменная цикла {var_name} должна быть типа integer")

            start_type = self.infer_type(node.start_expr)
            end_type = self.infer_type(node.end_expr)

            if start_type != 'integer' or end_type != 'integer':
                raise TypeError(f"Границы цикла for должны быть integer, получено: {start_type} и {end_type}")

            self.in_loop = True
            for stmt in node.body.body:
                self.check_node(stmt)
            self.in_loop = False

        elif isinstance(node, ProcedureCallNode):
            for arg in node.args:
                self.check_expression(arg)

    def check_expression(self, node: ExpressionNode):
        if isinstance(node, BinOperatorNode):
            left_type = self.infer_type(node.leftNode)
            right_type = self.infer_type(node.rightNode)
            if node.operator.value in ['+', '-', '*', '/'] and (left_type != 'integer' or right_type != 'integer'):
                raise TypeError("Арифметические операции требуют integer")

    def infer_type(self, node: ExpressionNode) -> str:
        if isinstance(node, ValueNode):
            if node.value.type == 'NUMBER':
                return 'integer'
            elif node.value.type == 'STRING':
                return 'string'
            elif node.value.type == 'IDENTIFIER':
                return self.variables.get(node.value.value, 'unknown')
        
        elif isinstance(node, BinOperatorNode):
            left_type = self.infer_type(node.leftNode)
            right_type = self.infer_type(node.rightNode)

            # Логические операторы
            if node.operator.value in ['and', 'or']:
                if left_type != 'boolean' or right_type != 'boolean':
                    raise TypeError(f"Логические операторы требуют boolean, получено {left_type} и {right_type}")
                return 'boolean'
            
            # Операторы сравнения
            elif node.operator.value in ['==', '!=', '<', '>', '<=', '>=']:
                if left_type != right_type:
                    raise TypeError(f"Сравнение типов {left_type} и {right_type} невозможно")
                return 'boolean'
            
            # Арифметические операторы
            elif node.operator.value in ['+', '-', '*', '/']:
                if left_type != 'integer' or right_type != 'integer':
                    raise TypeError(f"Арифметические операции требуют integer, получено {left_type} и {right_type}")
                return 'integer'
        
        return 'unknown'
    def check_condition(self, condition: ExpressionNode):
        if self.infer_type(condition) != 'boolean':
            raise TypeError("Условие должно быть логическим")