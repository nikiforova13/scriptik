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


def create_nested_and(AND_PARTS, last_result: bool = True) -> dict:
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
    result = {"AND": []}
    top_or_block = {"OR": []}
    simple_ors = []
    and_blocks = []

    if reverse:
        or_expressions = list(reversed(or_expressions))

    for or_expression in or_expressions:
        and_expressions = [p.strip() for p in re.split(r"(\bAND\b)", or_expression)]
        if len(and_expressions) > 1:
            parsed_and = create_nested_and(and_expressions, last_result=False)
            and_blocks.append(parsed_and)
        else:
            parsed_simple = _parse_expression(or_expression)
            simple_ors.append(parsed_simple)

    # 🔁 Объединяем простые OR в один OR-блок, если их несколько
    if len(simple_ors) == 1:
        simple_or_expr = simple_ors[0]
    elif simple_ors:
        nested = simple_ors[-1]
        for part in reversed(simple_ors[:-1]):
            nested = {"OR": [part, nested]}
        simple_or_expr = nested
    else:
        simple_or_expr = None

    # 🔁 Объединяем AND и OR в один OR-блок
    if and_blocks:
        top_or_block["OR"].extend(and_blocks)
        if simple_or_expr:
            top_or_block["OR"].append(simple_or_expr)
        result["AND"].append(top_or_block)
    elif simple_or_expr:
        result["AND"].append(simple_or_expr)
    if not reverse:
        result["AND"][0]["OR"].reverse()
    return result


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
        else:
            return create_nested_and(and_expressions)
    # Если есть OR, то начинаем обработку
    else:
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
