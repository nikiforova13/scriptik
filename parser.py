import pprint
import re

FilterKey = {
    "Теги": "tags",
    "Источник": "source",
    "Важность": "severity",
    "CL": "critical_level",
    "Ack": "ack_status",
    "Flp": "flap",
    "КЕ": "sm",
    "Группы": "groups",
}


def _parse_expression(expression: str) -> dict | None:
    pattern = r"(\w+)\s*(==|!=|=|!==)\s*([\w:\.\- ]+)"
    match = re.match(pattern, expression.strip())
    if match:
        key, operator, value = match.groups()
        return {
            "key": FilterKey.get(key.strip()),
            "operator": operator.strip(),
            "value": value.strip(),
        }

    raise ValueError(f"Не удалось распарсить фильтр: {expression}")


def create_and_block(AND_PARTS, last_result: bool = True) -> dict:
    AND_PARTS.reverse()
    result = {"AND": []}
    current = result["AND"]
    i = 0

    while i < len(AND_PARTS):
        current_elem = AND_PARTS[i]
        if current_elem == "AND":
            # Проверка: есть ли элемент после AND и есть ли что-то после элемента него
            if (i + 2) < len(
                AND_PARTS
            ):  # ['Flp != No', 'AND', 'Ack = Commented', 'AND', 'Источник != self-dev', 'AND', 'Теги = Application']
                new_and = {
                    "AND": []
                }  # например проверяем есть ли элемент после 'Теги = Application' на этапе когда мы на элементе 'AND'
                current.append(new_and)
                current = new_and["AND"]
        else:
            current.append(_parse_expression(current_elem))
        i += 1
    return {"AND": [result]} if last_result else result


def get_first_operator(filter_string: str) -> str:
    # Находим первое вхождение AND или OR
    match = re.search(r"\b(AND|OR)\b", filter_string)
    return match.group(1) if match else None


def create_or_block(or_expressions: list[str], reverse: bool = True) -> dict:
    if reverse:
        or_expressions.reverse()

    simple_ors, and_blocks = [], []

    for expr in or_expressions:
        and_parts = [p.strip() for p in re.split(r"(\bAND\b)", expr)]
        if len(and_parts) > 1:
            and_blocks.append(create_and_block(and_parts, last_result=False))
        else:
            simple_ors.append(_parse_expression(expr.strip()))

    result = {"AND": []}

    # Если есть AND-блоки
    if and_blocks:
        or_block = {"OR": and_blocks}
        if simple_ors:
            # Построим вложенную OR-цепочку из простых выражений
            nested_or = build_nested_or(simple_ors)
            or_block["OR"].append(nested_or)
        result["AND"].append(or_block)
    elif simple_ors:
        # Только OR — строим вложенность
        result["AND"].append(build_nested_or(simple_ors))
    if not reverse:
        result['AND'][0]['OR'].reverse()
    return result


def build_nested_or(expressions: list[dict] | None = None) -> dict | dict:
    """
    Создаёт вложенные OR-выражения, например:
    [A, B, C] -> {"OR": [A, {"OR": [B, C]}]}
    """
    if not expressions:
        return {}
    if len(expressions) == 1:
        return expressions[0]

    nested = expressions[-1]
    for expr in reversed(expressions[:-1]):
        nested = {"OR": [expr, nested]}
    return nested


def parse_filter_string(filter_string: str) -> dict:
    filter_string = filter_string.strip()
    first_operator = get_first_operator(filter_string)

    or_expressions = [p.strip() for p in re.split(r"\bOR\b", filter_string)]

    # Нет вложенных OR вообще
    if len(or_expressions) == 1:
        and_expressions = [p.strip() for p in re.split(r"(\bAND\b)", filter_string)]
        # нет вложенных AND вообще
        if len(and_expressions) == 1:
            return {"AND": [_parse_expression(and_expressions[0])]}
        # Есть Вложенные AND
        return create_and_block(and_expressions)
    # Если есть OR, то начинаем обработку
    return create_or_block(or_expressions, first_operator == "OR")


def generate_filter(
    hostname: str,
    tags: list[str],
    filter_string: str | None = None,
) -> dict:
    extra_filter = parse_filter_string(filter_string) if filter_string else None
    filter = {
        "filter": {
            "AND": [
                {"OR": [{"key": "host", "operator": "==", "value": hostname}]},
                {
                    "OR": [
                        {"key": "tags", "operator": "==", "value": tag} for tag in tags
                    ]
                },
                extra_filter,
            ]
        }
    }
    return filter


TEST_HOSTNAME = "FAKE32"
TEST_TAGS = ["OS:Linux"]
# res = generate_filter(filter_string="Теги !== Application:Inventory OR Теги == Application:Disk sda",        hostname=TEST_HOSTNAME, tags=TEST_TAGS
# )
# res = generate_filter(filter_string="Теги != Application:Inventory AND Теги = 100",        hostname=TEST_HOSTNAME, tags=TEST_TAGS
# )
res = generate_filter(
    filter_string="Теги = Application AND Источник != self-dev AND Ack = Commented AND Flp != No",
    hostname=TEST_HOSTNAME,
    tags=TEST_TAGS,
)
# res = generate_filter(filter_string="Теги != ApplicationOR:Inventory",        hostname=TEST_HOSTNAME, tags=TEST_TAGS
# )
pprint.pprint(res)
parse_result_10 = {
    "filter": {
        "AND": [
            {"OR": [{"key": "host", "operator": "==", "value": "FAKE32"}]},
            {"OR": [{"key": "tags", "operator": "==", "value": "OS:Linux"}]},
            {
                "AND": [
                    {
                        "OR": [
                            {
                                "AND": [
                                    {
                                        "key": "tags",
                                        "operator": "==",
                                        "value": "Inventory",
                                    },
                                    {"key": "sm", "operator": "=", "value": "one"},
                                ]
                            },
                            {
                                "OR": [
                                    {
                                        "key": "severity",
                                        "operator": "!=",
                                        "value": "Average",
                                    },
                                    {
                                        "key": "tags",
                                        "operator": "=",
                                        "value": "Application",
                                    },
                                ]
                            },
                        ]
                    }
                ]
            },
        ]
    }
}
print()
# pprint.pprint(parse_result_10)
# pprint.pprint(res == parse_result_10)
