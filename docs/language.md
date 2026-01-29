# Поддержка языка (PascalABC subset)

## 1. Типы
Поддерживаются:
- `integer`
- `real`
- `string`
- `char`
- `boolean`

В Go:
- `integer` → `int`
- `real` → `float64`
- `string` → `string`
- `char` → `rune`
- `boolean` → `bool`

Ограничения:
- Смешанная арифметика `integer` + `real` запрещена (нужны одинаковые числовые типы).

## 2. Переменные
```
var
  x: integer;
  s: string;
```

## 3. Логические операторы
```
and, or, not, xor
```
В Go:
- `and` → `&&`
- `or` → `||`
- `not` → `!`
- `xor` → `!=` (логическое XOR на boolean)

## 4. Выражения и присваивания
```
x := 1 + 2;
```

## 5. Условные конструкции
```
if a > b then
  writeln(a)
else
  writeln(b);
```

## 6. Циклы
### while
```
while i < 10 do
  i := i + 1;
```

### for
```
for i := 1 to 10 do
  writeln(i);
```

### repeat ... until
```
repeat
  i := i + 1;
until i = 10;
```

## 7. case ... of
```
case x of
  1: writeln(1);
  2, 3: writeln(2);
else
  writeln(0);
end;
```

## 8. Функции и процедуры (MVP)
Поддерживаются:
- параметры по значению
- возврат через присваивание имени функции
- объявления до основного `begin`

Пример:
```
function add(a: integer; b: integer): integer;
begin
  add := a + b;
end;
```

Ограничения:
- нет `var`‑параметров
- нет перегрузок
- массивы в параметрах не поддерживаются

## 9. Массивы (1D, статические)
```
var
  a: array[1..3] of integer;
```

Индексация:
```
a[1] := 10;
writeln(a[i]);
```

Ограничения:
- только одномерные массивы
- только статические границы `low..high`
- индекс должен быть integer

## 10. Операторы сравнения
Поддерживаются:
```
=, <>, <, >, <=, >=
```

В Go:
- `=` → `==`
- `<>` → `!=`
