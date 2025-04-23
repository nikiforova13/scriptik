import re

# Маппинг текстовых ключей на нормализованные ключи фильтра
KEY_MAPPING = {
    "Теги": "tags",
    "Важность": "severity",
    "КЕ": "sm",
    "Источник": "source",
    "Ack": "ack_status",
    "Flp": "flap",
    "host": "host",
}

# Операторы
OPERATOR_MAPPING = {
    "==": "==",
    "!=": "!=",
    "=": "=",
    "!==": "!==",
}

# Регулярка для извлечения простых выражений
SIMPLE_EXPR_PATTERN = re.compile(r"([^=!\s]+)\s*(!=|==|=|!==)\s*([^\s]+)")


def parse_condition(expr: str):
    match = SIMPLE_EXPR_PATTERN.match(expr.strip())
    if not match:
        raise ValueError(f"Invalid expression: {expr}")
    key_raw, operator, value = match.groups()
    key = KEY_MAPPING.get(key_raw, key_raw)
    return {"key": key, "operator": operator, "value": value}


def split_by_operator(expression: str, operator: str):
    """Разделение строки по оператору, но без скобок — безопасно"""
    return [e.strip() for e in expression.split(f" {operator} ")]


def parse_filter_string(input_string: str) -> dict:
    # Добавим "заглушки" OR от FAKE32 и tags == OS:Linux
    base = {"OR": [{"key": "host", "operator": "==", "value": "FAKE32"}]}
    tags_linux = {"OR": [{"key": "tags", "operator": "==", "value": "OS:Linux"}]}

    def build_nested(items, op):
        """Рекурсивно вложенная структура по приоритету (обратный порядок)"""
        if len(items) == 1:
            return parse_condition(items[0])
        else:
            return {op: [build_nested(items[:-1], op), parse_condition(items[-1])]}

    # Разделение по AND, затем каждую часть по OR
    and_parts = split_by_operator(input_string, "AND")
    parsed_and_parts = []

    for part in and_parts:
        or_parts = split_by_operator(part, "OR")
        if len(or_parts) == 1:
            parsed_and_parts.append(build_nested(or_parts, "AND"))
        else:
            parsed_or = {"OR": [build_nested([sub], "AND") for sub in or_parts]}
            parsed_and_parts.append(parsed_or)

    # Максимально вложенный AND (в обратном порядке)
    nested_and = parsed_and_parts[-1]
    for part in reversed(parsed_and_parts[:-1]):
        nested_and = {"AND": [part, nested_and]}

    return {"filter": {"AND": [base, tags_linux, {"AND": [nested_and]}]}}


input_string_10 = (
    "Теги = Application OR Важность != Average OR КЕ = one AND Теги == Inventory"
)

input_string_11 = (
    "Теги = Application AND Источник != self-dev AND Ack = Commented AND Flp != No"
)

from pprint import pprint

pprint(parse_filter_string(input_string_10), width=140)
pprint(parse_filter_string(input_string_11), width=140)
