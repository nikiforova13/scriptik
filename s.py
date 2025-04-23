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

# def sort_blocks(node):
#     if isinstance(node, dict):
#         sorted_node = {}
#         for key, value in node.items():
#             if key in ("AND", "OR") and isinstance(value, list):
#                 value = [sort_blocks(item) for item in value]
#                 # Сортировка по key, затем по value
#                 value = sorted(
#                     value,
#                     key=lambda x: (
#                         x.get("key", "") if isinstance(x, dict) else "",
#                         x.get("value", "") if isinstance(x, dict) else str(x),
#                     ),
#                 )
#             else:
#                 value = sort_blocks(value)
#             sorted_node[key] = value
#         return sorted_node
#     elif isinstance(node, list):
#         return [sort_blocks(item) for item in node]
#     return node


def _parse_expression(cond: str) -> dict | None:
    pattern = r"(\w+)\s*(==|!=|=|!==)\s*([\w:\.\- ]+)"
    match = re.match(pattern, cond.strip())
    if match:
        key, operator, value = match.groups()
        return {
            "key": FilterKey.get(key.strip()),
            "operator": operator.strip(),
            "value": value.strip(),
        }

    raise ValueError(f"Не удалось распарсить фильтр: {cond}")


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


def reverse_logic_order(obj):
    if isinstance(obj, dict):
        new_obj = {}
        for key, value in obj.items():
            if key in ("AND", "OR") and isinstance(value, list):
                # Реверсим список и рекурсивно обрабатываем элементы
                new_obj[key] = [reverse_logic_order(v) for v in reversed(value)]
            else:
                new_obj[key] = reverse_logic_order(value)
        return new_obj
    elif isinstance(obj, list):
        return [reverse_logic_order(i) for i in obj]
    else:
        return obj  # строка или число — не меняем

def get_first_operator(filter_string: str) -> str:
    # Находим первое вхождение AND или OR
    match = re.search(r'\b(AND|OR)\b', filter_string)
    return match.group(1) if match else None
def reverse_logical_lists(obj):
    if isinstance(obj, dict):
        new_obj = {}
        for key, value in obj.items():
            print(f"{key}{value}")
            # Если ключ — "AND" или "OR", и значение — список
            if key in ("AND", "OR") and isinstance(value, list):
                # Реверс списка + рекурсивно на каждом элементе
                new_obj[key] = [reverse_logical_lists(v) for v in reversed(value)]
            else:
                new_obj[key] = reverse_logical_lists(value)
        return new_obj
    elif isinstance(obj, list):
        return [reverse_logical_lists(item) for item in obj]
    else:
        return obj  # примитив (строка, число, dict-поле)



def create_or_block(OR_PARTS: list[str], reverse: bool) -> dict:
    OR_BLOCKS_RESULT = {"AND": []}
    OR_BLOCK_AND_OR_IN_OR = {"OR": []}
    OR_TOGETHER = {"OR": []}
    if reverse:
        OR_PARTS.reverse()
    has_and_parts = False
    i = 0
    print(f"{OR_PARTS=}")
    filtered_parts = [part for part in OR_PARTS if "AND" not in part]
    print('dddddddd',filtered_parts)

    for or_part in OR_PARTS:
        AND_PARTS = [p.strip() for p in re.split(r"(\bAND\b)", or_part)]
        print(f"OR_PART = {or_part}")
        parsed = None
        if len(AND_PARTS) > 1:  # если есть AND внутри OR, создаем вложенность из AND-ов
            print(f"{AND_PARTS=}")
            parsed = create_nested_and(AND_PARTS, last_result=False)
            print("sfddsffd", parsed)
            has_and_parts = True  # Ставим, что and у нас выражения есть
        else:
            # Если AND отсутствует, значит у нас есть только OR. Если у нас несколько выражений OR то объединяем их в 1 блок OR - OR_TOGETHER
            # Если у нас 1 выражение OR, то просто добавляем в OR_TOGETHER
            if len(filtered_parts) > 1 :
                print("JDJDJDJDJDJJDJ")
                OR_TOGETHER["OR"].append(
                    _parse_expression(or_part)
                )  # все OR выражения добавляем в единый OR
            #
            else:
                parsed = _parse_expression(or_part)
        i += 1
        # Проверяем, что у нас были AND выражения и есть результат, добавляем в OR блок где будут и AND выражения и другие выражения
        if has_and_parts and parsed:
            print("YEEEESSS")
            OR_BLOCK_AND_OR_IN_OR["OR"].append(parsed)  # добавляем в один блок OR - and
    # Если были and то к ним добавляем получившееся OR
    if has_and_parts and OR_TOGETHER["OR"] != []:
        OR_BLOCK_AND_OR_IN_OR["OR"].append(
            OR_TOGETHER
        )  # В этот же блок добавляем несколько OR . Это для соединения OR/AND вместе

    # print(f'{OR_BLOCK_AND_OR_IN_OR["OR"]=}')


    # Если у нас есть и OR и AND выражения, которые объединены в блоке OR, то добавляем в блок AND это все
    if OR_BLOCK_AND_OR_IN_OR["OR"] != []:
        OR_BLOCKS_RESULT["AND"].append(
            OR_BLOCK_AND_OR_IN_OR
        )  # а это просто всегда обязательно
    else:  # Если были только OR блоки, то добавляем в AND
        OR_BLOCKS_RESULT["AND"].append(OR_TOGETHER)

    pprint.pprint(f"{OR_BLOCKS_RESULT=}")
    print()
    if not reverse:
        OR_BLOCKS_RESULT["AND"][0]["OR"].reverse()
    return OR_BLOCKS_RESULT


def parse_filter_string(filter_string: str) -> dict:
    filter_string = filter_string.strip()
    print(f"{filter_string=}")
    first_op = get_first_operator(filter_string)

    # Разбиваем по OR, OR могут быть либо их не будет вообще. Если нет, то строка остается такой какая была
    OR_PARTS = [p.strip() for p in re.split(r"\bOR\b", filter_string)]

    # Нет вложенных OR вообще
    if len(OR_PARTS) == 1:
        AND_PARTS = [p.strip() for p in re.split(r"(\bAND\b)", filter_string)]
        # нет вложенных AND вообще
        if len(AND_PARTS) == 1:
            return {"AND": [_parse_expression(AND_PARTS[0])]}
        # Есть Вложенные AND
        else:
            return create_nested_and(AND_PARTS)
    # Если есть OR, то начинаем обработку
    else:
        reverse = True
        if first_op == "AND":
            reverse = False
        return create_or_block(OR_PARTS, reverse)


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
