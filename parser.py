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


def get_first_operator(filter_string: str) -> str | None:
    match = re.search(r"\b(AND|OR)\b", filter_string)
    return match.group(1) if match else None


def split_string_into_expressions(s: str, pattern: str) -> list[str]:
    return [p.strip() for p in re.split(pattern, s)]


def _parse_expression(expression: str) -> dict | None:
    match = re.match(r"(\w+)\s*(==|!=|=|!==)\s*([\w:\.\- ]+)", expression.strip())
    if match:
        key, operator, value = match.groups()
        return {
            "key": FilterKey.get(key.strip()),
            "operator": operator.strip(),
            "value": value.strip(),
        }

    raise ValueError(f"Не удалось распарсить фильтр: {expression}")


def create_nested_and(expressions: list[str], last_result: bool = True) -> dict:
    """
    Создаёт вложенные AND-выражения из строки, разбитой по "AND".

    Пример:
    ["A", "AND", "B", "AND", "C"] →
    {"AND": [{"AND": ["С", {"AND": ["B", "А"]}]}]}

    :param expressions: Список выражений с "AND" разделителем
    :param last_result: Если True — оборачивает результат ещё одним "AND" уровнем
    :return: Словарь с вложенными AND-условиями
    """
    expressions.reverse()
    result = {"AND": []}
    current_result = result["AND"]
    i = 0
    while i < len(expressions):
        current_exp = expressions[i]
        if current_exp == "AND":
            if (i + 2) < len(expressions):
                new_nested_and = {"AND": []}
                current_result.append(new_nested_and)
                current_result = new_nested_and["AND"]
        else:
            current_result.append(_parse_expression(current_exp))
        i += 1
    return {"AND": [result]} if last_result else result


def create_nested_or(expressions: list[dict] | None = None) -> dict:
    """
    Создаёт вложенные OR-выражения, например:
    [A, B, C] -> {"OR": [С, {"OR": [B, A]}]}

    :param expressions: Список выражений, которые нужно вложить по OR
    :return: Словарь с вложенными OR-условиями
    """
    if not expressions:
        return {}
    if len(expressions) == 1:
        return expressions[0]

    nested = expressions[-1]
    for expr in reversed(expressions[:-1]):
        nested = {"OR": [expr, nested]}
    return nested


def create_blocks(or_expressions: list[str], reverse: bool = True) -> dict:
    """
    Собирает логическую структуру из выражений, содержащих OR и вложенные AND.
    """
    result = {"AND": []}

    if reverse:
        or_expressions = list(reversed(or_expressions))

    ordered_or_parts = []
    for or_expr in or_expressions:
        and_parts = split_string_into_expressions(or_expr, r"(\bAND\b)")
        if len(and_parts) > 1:
            ordered_or_parts.append(create_nested_and(and_parts, last_result=False))
        else:
            ordered_or_parts.append(_parse_expression(or_expr.strip()))

    contains_nested_and_expression = any(
        isinstance(part, dict) and "AND" in part for part in ordered_or_parts
    )
    contains_multiple_expressions = len(ordered_or_parts) > 1

    if contains_nested_and_expression and contains_multiple_expressions:
        nested_or = create_nested_or(ordered_or_parts)
        result["AND"].append(nested_or)
    else:
        simple_or_blocks, and_blocks = [], []

        for part in ordered_or_parts:
            if isinstance(part, dict) and "AND" in part:
                and_blocks.append(part)
            else:
                simple_or_blocks.append(part)

        if and_blocks:
            or_block = {"OR": and_blocks}
            if simple_or_blocks:
                or_block["OR"].append(create_nested_or(simple_or_blocks))
            result["AND"].append(or_block)
        elif simple_or_blocks:
            result["AND"].append(create_nested_or(simple_or_blocks))

    if (
        not reverse
        and result["AND"]
        and isinstance(result["AND"][0], dict)
        and "OR" in result["AND"][0]
    ):
        result["AND"][0]["OR"].reverse()

    return result


def create_filter_from_string(filter_string: str) -> dict:
    filter_string = filter_string.strip()
    first_operator = get_first_operator(filter_string)

    or_expressions = split_string_into_expressions(filter_string, r"\bOR\b")

    if len(or_expressions) == 1:
        and_expressions = split_string_into_expressions(filter_string, r"(\bAND\b)")
        if len(and_expressions) == 1:
            return {"AND": [_parse_expression(and_expressions[0])]}
        return create_nested_and(and_expressions)
    return create_blocks(or_expressions, first_operator == "OR")


def generate_filter(
    hostname: str,
    tags: list[str],
    filter_string: str | None = None,
) -> dict:
    extra_filter = create_filter_from_string(filter_string) if filter_string else None
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
    filter_string="Теги = Application AND Источник != self-dev__1 AND Ack = Commented AND Flp != No",
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
