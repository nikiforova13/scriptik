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

def sort_blocks(node):
    if isinstance(node, dict):
        sorted_node = {}
        for key, value in node.items():
            if key in ("AND", "OR") and isinstance(value, list):
                # Рекурсивно сортируем каждый элемент
                value = [sort_blocks(item) for item in value]

                # Сортируем, только если все элементы — обычные выражения, а не логические блоки
                if all(isinstance(item, dict) and "key" in item and "operator" in item for item in value):
                    value = sorted(
                        value,
                        key=lambda x: (x["key"], x["value"])
                    )

            else:
                value = sort_blocks(value)
            sorted_node[key] = value
        return sorted_node

    elif isinstance(node, list):
        return [sort_blocks(item) for item in node]

    return node





def parse_expression(cond: str) -> dict | None:
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



# Обновим build_nested_and_chain для корректной правой вложенности

def build_nested_and_chain(conditions: list[dict]) -> dict:
    """
    Создаёт вложенные AND в правильном порядке:
    [A, B, C, D] -> AND[A, AND[B, AND[C, D]]]
    """
    if len(conditions) == 1:
        return conditions[0]

    nested = conditions[-1]
    for condition in reversed(conditions[:-1]):
        nested = {"AND": [condition, nested]}
    return nested



def tokenize_preserve_logic(s: str) -> list:
    tokens = []
    current = []
    parts = s.strip().split()
    i = 0
    while i < len(parts):
        if parts[i] in ("AND", "OR"):
            if current:
                tokens.append(" ".join(current))
                current = []
            tokens.append(parts[i])
        else:
            current.append(parts[i])
        i += 1
    if current:
        tokens.append(" ".join(current))
    return tokens
def parse_expression_group_final(tokens: list[str]) -> dict:
    def split_by_operator(tokens, op):
        groups = []
        current = []
        for token in tokens:
            if token == op:
                if current:
                    groups.append(current)
                    current = []
            else:
                current.append(token)
        if current:
            groups.append(current)
        return groups

    def parse_atom(expr: str) -> dict:
        return parse_expression(expr)

    def parse_and_group(group: list[str]) -> dict:
        and_tokens = split_by_operator(group, "AND")
        expressions = [parse_atom(" ".join(part)) for part in and_tokens]
        return build_nested_and_chain(expressions)

    # Разделяем по OR
    or_groups = split_by_operator(tokens, "OR")
    parsed_groups = []

    for group in or_groups:
        if any("AND" in g for g in group if isinstance(g, str)):
            and_exprs = []
            sub_expr = []
            for item in group:
                if item == "AND":
                    if sub_expr:
                        and_exprs.append(" ".join(sub_expr))
                        sub_expr = []
                else:
                    sub_expr = item.split() if not sub_expr else sub_expr + item.split()
            if sub_expr:
                and_exprs.append(" ".join(sub_expr))
            and_nodes = [parse_expression(e) for e in and_exprs]
            parsed_groups.append(build_nested_and_chain(and_nodes))
        else:
            parsed_groups.append(parse_atom(" ".join(group)))

    # Специальное поведение: если более двух OR-блоков, последние два вложим в OR
    if len(parsed_groups) > 2:
        *initial, penultimate, ultimate = parsed_groups
        nested_or = {"OR": [penultimate, ultimate]}
        return {"OR": initial + [nested_or]}
    elif len(parsed_groups) == 2:
        return {"OR": parsed_groups}
    else:
        return parsed_groups[0]

def parse_filter_string(filter_string: str) -> dict:
    tokens = tokenize_preserve_logic(filter_string)
    ast = parse_expression_group_final(tokens)
    return {"AND": [ast]}



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
    return sort_blocks(filter)


tokens_fixed = tokenize_preserve_logic("Теги = Application OR Важность != Average OR КЕ = one AND Теги == Inventory")
ast_fixed = parse_expression_group_final(tokens_fixed)
# print(ast_fixed)

# print(parse_filter_string("Теги = Application OR Важность != Average OR КЕ = one AND Теги == Inventory"))

TEST_HOSTNAME = "FAKE32"
TEST_TAGS = ["OS:Linux"]
res = generate_filter(
    filter_string="Теги = Application OR Важность != Average OR КЕ = one AND Теги == Inventory",
    hostname=TEST_HOSTNAME,
    tags=TEST_TAGS
)
print(f"{res=}")