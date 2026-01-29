from nodes import *

class SemanticAnalyzer:
    def __init__(self) -> None:
        self.scopes = [{}]
        self.functions = {}
        self.procedures = {}
        self.in_loop = False

    def push_scope(self):
        self.scopes.append({})

    def pop_scope(self):
        self.scopes.pop()

    def declare(self, name: str, var_type: str):
        if name in self.scopes[-1]:
            raise NameError(f"Переменная {name} уже объявлена")
        self.scopes[-1][name] = var_type

    def lookup(self, name: str):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    def format_error(self, message: str, node: ExpressionNode = None) -> str:
        token = self.get_token(node)
        if token:
            return f"{message} (строка {token.line}, колонка {token.column})"
        return f"{message} (строка ?, колонка ?)"

    def get_token(self, node: ExpressionNode):
        if node is None:
            return None
        if hasattr(node, 'value') and isinstance(node.value, Token):
            return node.value
        if hasattr(node, 'token'):
            return node.token
        if hasattr(node, 'operator'):
            return node.operator
        return None

    def check_program(self, root: ExpressionNode):
        if isinstance(root, ProgramNode):
            for var_name, var_type in root.declarations:
                self.declare(var_name, var_type)

            for routine in root.routines:
                if isinstance(routine, FunctionDeclNode):
                    if routine.name in self.functions or routine.name in self.procedures:
                        raise NameError(f"Функция/процедура {routine.name} уже объявлена")
                    self.functions[routine.name] = {
                        'params': routine.params,
                        'return_type': routine.return_type
                    }
                elif isinstance(routine, ProcedureDeclNode):
                    if routine.name in self.functions or routine.name in self.procedures:
                        raise NameError(f"Функция/процедура {routine.name} уже объявлена")
                    self.procedures[routine.name] = {
                        'params': routine.params
                    }

            for routine in root.routines:
                self.check_node(routine)

            for stmt in root.main_block.body:
                self.check_node(stmt)
            return

        for node in root.codeStrings:
            self.check_node(node)

    def check_node(self, node: ExpressionNode):
        if isinstance(node, VarDeclarationNode):
            for var_name, var_type in node.declarations:
                self.declare(var_name, var_type)

        elif isinstance(node, BinOperatorNode):
            if node.operator.type == 'ASSIGN':
                if isinstance(node.leftNode, ArrayAccessNode):
                    arr_name = node.leftNode.name
                    arr_type = self.lookup(arr_name)
                    if arr_type is None or not self.is_array_type(arr_type):
                        raise NameError(self.format_error(
                            f"Переменная {arr_name} не объявлена как массив",
                            node.leftNode
                        ))
                    index_type = self.infer_type(node.leftNode.index)
                    if index_type != 'integer':
                        raise TypeError(self.format_error(
                            "Индекс массива должен быть integer",
                            node.leftNode.index
                        ))
                    expr_type = self.infer_type(node.rightNode)
                    elem_type = arr_type['elem']
                    if expr_type != elem_type:
                        raise TypeError(self.format_error(
                            f"Тип {expr_type} не соответствует {elem_type}",
                            node.rightNode
                        ))
                else:
                    var_name = node.leftNode.value.value
                    if self.lookup(var_name) is None:
                        raise NameError(self.format_error(
                            f"Переменная {var_name} не объявлена",
                            node.leftNode
                        ))
                    expr_type = self.infer_type(node.rightNode)
                    var_type = self.lookup(var_name)
                    if expr_type != var_type:
                        raise TypeError(self.format_error(
                            f"Тип {expr_type} не соответствует {var_type}",
                            node.rightNode
                        ))

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

        elif isinstance(node, RepeatUntilStatementNode):
            self.in_loop = True
            for stmt in node.body.body:
                self.check_node(stmt)
            self.in_loop = False
            self.check_condition(node.condition)

        elif isinstance(node, ForStatementNode):
            var_name = node.var_token.value

            if self.lookup(var_name) is None:
                raise NameError(self.format_error(
                    f"Переменная {var_name} не объявлена",
                    ValueNode(node.var_token)
                ))
            if self.lookup(var_name) != 'integer':
                raise TypeError(self.format_error(
                    f"Переменная цикла {var_name} должна быть типа integer",
                    ValueNode(node.var_token)
                ))

            start_type = self.infer_type(node.start_expr)
            end_type = self.infer_type(node.end_expr)

            if start_type != 'integer' or end_type != 'integer':
                raise TypeError(self.format_error(
                    f"Границы цикла for должны быть integer, получено: {start_type} и {end_type}",
                    node
                ))

            self.in_loop = True
            for stmt in node.body.body:
                self.check_node(stmt)
            self.in_loop = False

        elif isinstance(node, ProcedureCallNode):
            if node.name.lower() == 'writeln':
                for arg in node.args:
                    self.check_expression(arg)
                return
            self.check_call(node.name, node.args, allow_procedure=True, allow_function=False, node=node)

        elif isinstance(node, FunctionCallNode):
            self.check_call(node.name, node.args, allow_procedure=False, allow_function=True, node=node)

        elif isinstance(node, FunctionDeclNode):
            self.push_scope()
            for param_name, param_type in node.params:
                self.declare(param_name, param_type)
            self.declare(node.name, node.return_type)
            for var_name, var_type in node.local_decls:
                self.declare(var_name, var_type)
            for stmt in node.body.body:
                self.check_node(stmt)
            self.pop_scope()

        elif isinstance(node, ProcedureDeclNode):
            self.push_scope()
            for param_name, param_type in node.params:
                self.declare(param_name, param_type)
            for var_name, var_type in node.local_decls:
                self.declare(var_name, var_type)
            for stmt in node.body.body:
                self.check_node(stmt)
            self.pop_scope()

        elif isinstance(node, CaseStatementNode):
            expr_type = self.infer_type(node.expression)
            for labels, block in node.cases:
                for label in labels:
                    label_type = self.infer_type(label)
                    if label_type != expr_type:
                        raise TypeError(self.format_error(
                            f"Тип метки {label_type} не соответствует {expr_type}",
                            label
                        ))
                for stmt in block.body:
                    self.check_node(stmt)
            if node.else_block:
                for stmt in node.else_block.body:
                    self.check_node(stmt)

    def check_expression(self, node: ExpressionNode):
        if isinstance(node, BinOperatorNode):
            left_type = self.infer_type(node.leftNode)
            right_type = self.infer_type(node.rightNode)
            if node.operator.value in ['+', '-', '*', '/', 'div', 'mod']:
                if left_type not in ['integer', 'real'] or right_type not in ['integer', 'real']:
                    raise TypeError(self.format_error(
                        "Арифметические операции требуют числовые типы",
                        node
                    ))
                if left_type != right_type:
                    raise TypeError(self.format_error(
                        "Арифметические операции требуют одинаковые числовые типы",
                        node
                    ))
                if node.operator.value in ['div', 'mod'] and left_type != 'integer':
                    raise TypeError(self.format_error(
                        "Операции div/mod требуют integer",
                        node
                    ))
        elif isinstance(node, UnaryOperatorNode):
            if node.operator.value.lower() == 'not' and self.infer_type(node.operand) != 'boolean':
                raise TypeError(self.format_error(
                    "Оператор not требует boolean",
                    node
                ))

    def infer_type(self, node: ExpressionNode) -> str:
        if isinstance(node, ValueNode):
            if node.value.type == 'NUMBER':
                return 'real' if '.' in node.value.value else 'integer'
            elif node.value.type == 'STRING':
                return 'string'
            elif node.value.type == 'BOOL_LIT':
                return 'boolean'
            elif node.value.type == 'CHAR_LIT':
                return 'char'
            elif node.value.type == 'IDENTIFIER':
                return self.lookup(node.value.value) or 'unknown'
        
        elif isinstance(node, ArrayAccessNode):
            arr_type = self.lookup(node.name)
            if arr_type is None or not self.is_array_type(arr_type):
                raise NameError(self.format_error(
                    f"Массив {node.name} не объявлен",
                    node
                ))
            index_type = self.infer_type(node.index)
            if index_type != 'integer':
                raise TypeError(self.format_error(
                    "Индекс массива должен быть integer",
                    node.index
                ))
            return arr_type['elem']

        elif isinstance(node, UnaryOperatorNode):
            if node.operator.value.lower() == 'not':
                if self.infer_type(node.operand) != 'boolean':
                    raise TypeError(self.format_error(
                        "Оператор not требует boolean",
                        node
                    ))
                return 'boolean'
            if node.operator.value == '-':
                op_type = self.infer_type(node.operand)
                if op_type not in ['integer', 'real']:
                    raise TypeError(self.format_error(
                        "Унарный минус требует числовой тип",
                        node
                    ))
                return op_type
            return 'unknown'

        elif isinstance(node, FunctionCallNode):
            if node.name not in self.functions:
                if node.name in self.procedures:
                    raise TypeError(self.format_error(
                        f"{node.name} является процедурой и не может использоваться как функция",
                        node
                    ))
                raise NameError(self.format_error(
                    f"Функция {node.name} не объявлена",
                    node
                ))
            self.check_call(node.name, node.args, allow_procedure=False, allow_function=True, node=node)
            return self.functions[node.name]['return_type']

        elif isinstance(node, BinOperatorNode):
            left_type = self.infer_type(node.leftNode)
            right_type = self.infer_type(node.rightNode)

            # Логические операторы
            op_value = node.operator.value.lower()
            if op_value in ['and', 'or', 'xor']:
                if left_type != 'boolean' or right_type != 'boolean':
                    raise TypeError(self.format_error(
                        f"Логические операторы требуют boolean, получено {left_type} и {right_type}",
                        node
                    ))
                return 'boolean'
            
            # Операторы сравнения
            elif node.operator.value in ['==', '!=', '<', '>', '<=', '>=', '=', '<>']:
                if self.is_array_type(left_type) or self.is_array_type(right_type):
                    raise TypeError(self.format_error(
                        "Сравнение массивов не поддерживается",
                        node
                    ))
                if left_type != right_type:
                    raise TypeError(self.format_error(
                        f"Сравнение типов {left_type} и {right_type} невозможно",
                        node
                    ))
                return 'boolean'
            
            # Арифметические операторы
            elif node.operator.value in ['+', '-', '*', '/', 'div', 'mod']:
                if self.is_array_type(left_type) or self.is_array_type(right_type):
                    raise TypeError(self.format_error(
                        "Арифметика с массивами не поддерживается",
                        node
                    ))
                if left_type not in ['integer', 'real'] or right_type not in ['integer', 'real']:
                    raise TypeError(self.format_error(
                        f"Арифметические операции требуют числовые типы, получено {left_type} и {right_type}",
                        node
                    ))
                if left_type != right_type:
                    raise TypeError(self.format_error(
                        f"Арифметические операции требуют одинаковые типы, получено {left_type} и {right_type}",
                        node
                    ))
                if node.operator.value in ['div', 'mod'] and left_type != 'integer':
                    raise TypeError(self.format_error(
                        "Операции div/mod требуют integer",
                        node
                    ))
                return left_type
        
        return 'unknown'

    def check_call(self, name: str, args: list, allow_procedure: bool, allow_function: bool, node: ExpressionNode = None):
        if name in self.procedures:
            if not allow_procedure:
                raise TypeError(self.format_error(
                    f"{name} является процедурой и не может использоваться как функция",
                    node
                ))
            signature = self.procedures[name]
        elif name in self.functions:
            if not allow_function:
                raise TypeError(self.format_error(
                    f"{name} является функцией и не может использоваться как процедура",
                    node
                ))
            signature = self.functions[name]
        else:
            raise NameError(self.format_error(f"Процедура/функция {name} не объявлена", node))

        params = signature['params']
        if len(args) != len(params):
            raise TypeError(self.format_error(f"Неверное количество аргументов при вызове {name}", node))
        for arg, (_, param_type) in zip(args, params):
            arg_type = self.infer_type(arg)
            if arg_type != param_type:
                raise TypeError(self.format_error(
                    f"Тип аргумента {arg_type} не соответствует {param_type}",
                    arg
                ))

    def is_array_type(self, type_) -> bool:
        return isinstance(type_, dict) and type_.get('kind') == 'array'
    def check_condition(self, condition: ExpressionNode):
        if self.infer_type(condition) != 'boolean':
            raise TypeError(self.format_error("Условие должно быть логическим", condition))
