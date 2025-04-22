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
                value = [sort_blocks(item) for item in value]
                value = sorted(
                    value,
                    key=lambda x: x.get("value", "") if isinstance(x, dict) else str(x),
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


def build_nested_and_chain(conditions: list[dict]) -> dict:
    """
    Вкладывает цепочку условий с сохранением порядка:
    A AND B AND C AND D -> AND[A, AND[B, AND[C, D]]]
    """
    if len(conditions) == 1:
        return conditions[0]

    nested = conditions[-1]
    for condition in reversed(conditions[:-1]):
        nested = {"AND": [condition, nested]}
    return nested


def parse_filter_string(filter_string: str) -> dict:
    """
    Учитывает логическую приоритетность AND > OR
    и корректно формирует блоки вложенности OR/AND.
    """
    filter_string = filter_string.strip()

    or_parts = [p.strip() for p in re.split(r"\bOR\b", filter_string)]
    or_blocks = []

    for or_part in or_parts:
        and_parts = [p.strip() for p in re.split(r"\bAND\b", or_part)]
        parsed_and = [parse_expression(p) for p in and_parts]
        and_nested = build_nested_and_chain(parsed_and)
        or_blocks.append(and_nested)

    # Если только один OR-блок, то просто возвращаем его
    if len(or_blocks) == 1:
        return {"AND": [or_blocks[0]]}

    # Если несколько OR-блоков, то вложить их в OR
    return {"AND": [{"OR": or_blocks}]}


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


if __name__ == "__main__":
    input_string_11 = (
        "Теги = Application AND Источник != self-dev AND Ack = Commented AND Flp != No"
    )
    result = generate_filter(
        hostname="FAKE32",
        tags=["OS:Linux"],
        filter_string="Теги = Application AND Источник != self-dev AND Ack = Commented AND Flp != No",
    )
    # result = parse_filter_string_regex("Теги !== Application:Inventory OR Теги == Application:Disk sda")
    print(f"{result=}")
