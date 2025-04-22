# TODO 4 оператора: !=, !==, =, ==


input_string_1 = "Теги != Application:Inventory"
parse_result_1 = {
    "filter": {
        "AND": [
            {"OR": [{"key": "host", "operator": "==", "value": "FAKE32"}]},
            {"OR": [{"key": "tags", "operator": "==", "value": "OS:Linux"}]},
            {
                "AND": [
                    {"key": "tags", "operator": "!=", "value": "Application:Inventory"}
                ]
            },
        ]
    }
}
input_string_2 = "Теги == Application:Inventory"
parse_result_2 = {
    "filter": {
        "AND": [
            {"OR": [{"key": "host", "operator": "==", "value": "FAKE32"}]},
            {"OR": [{"key": "tags", "operator": "==", "value": "OS:Linux"}]},
            {
                "AND": [
                    {"key": "tags", "operator": "==", "value": "Application:Inventory"}
                ]
            },
        ]
    }
}
input_string_3 = "Теги = Application:Inventory"
parse_result_3 = {
    "filter": {
        "AND": [
            {"OR": [{"key": "host", "operator": "==", "value": "FAKE32"}]},
            {"OR": [{"key": "tags", "operator": "==", "value": "OS:Linux"}]},
            {
                "AND": [
                    {"key": "tags", "operator": "=", "value": "Application:Inventory"}
                ]
            },
        ]
    }
}
input_string_4 = "Теги !== Application:Inventory"
parse_result_4 = {
    "filter": {
        "AND": [
            {"OR": [{"key": "host", "operator": "==", "value": "FAKE32"}]},
            {"OR": [{"key": "tags", "operator": "==", "value": "OS:Linux"}]},
            {
                "AND": [
                    {"key": "tags", "operator": "!==", "value": "Application:Inventory"}
                ]
            },
        ]
    }
}

input_string_5 = "Теги !== Application:Inventory OR Теги == Application:Disk sda"
parse_result_5 = {
    "filter": {
        "AND": [
            {"OR": [{"key": "host", "operator": "==", "value": "FAKE32"}]},
            {"OR": [{"key": "tags", "operator": "==", "value": "OS:Linux"}]},
            {
                "AND": [
                    {
                        "OR": [
                            {
                                "key": "tags",
                                "operator": "==",
                                "value": "Application:Disk sda",
                            },
                            {
                                "key": "tags",
                                "operator": "!==",
                                "value": "Application:Inventory",
                            },
                        ]
                    }
                ]
            },
        ]
    }
}

input_string_6 = "Теги != Application:Inventory AND Теги = 100"
parse_result_6 = {
    "filter": {
        "AND": [
            {"OR": [{"key": "host", "operator": "==", "value": "FAKE32"}]},
            {"OR": [{"key": "tags", "operator": "==", "value": "OS:Linux"}]},
            {
                "AND": [
                    {
                        "AND": [
                            {"key": "tags", "operator": "=", "value": "100"},
                            {
                                "key": "tags",
                                "operator": "!=",
                                "value": "Application:Inventory",
                            },
                        ]
                    }
                ]
            },
        ]
    }
}
input_string_7 = (
    "Теги !== Application:Inventory OR Теги == Application:Disk sda AND Группы =12"
)
parse_result_7 = {
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
                                    {"key": "groups", "operator": "=", "value": "12"},
                                    {
                                        "key": "tags",
                                        "operator": "==",
                                        "value": "Application:Disk sda",
                                    },
                                ]
                            },
                            {
                                "key": "tags",
                                "operator": "!==",
                                "value": "Application:Inventory",
                            },
                        ]
                    }
                ]
            },
        ]
    }
}
input_string_8 = "CL = BC"
parse_result_8 = {
    "filter": {
        "AND": [
            {"OR": [{"key": "host", "operator": "==", "value": "FAKE32"}]},
            {"OR": [{"key": "tags", "operator": "==", "value": "OS:Linux"}]},
            {"AND": [{"key": "critical_level", "operator": "=", "value": "BC"}]},
        ]
    }
}
input_string_9 = "Теги = Application AND Важность != Average"
parse_result_9 = {
    "filter": {
        "AND": [
            {"OR": [{"key": "host", "operator": "==", "value": "FAKE32"}]},
            {"OR": [{"key": "tags", "operator": "==", "value": "OS:Linux"}]},
            {
                "AND": [
                    {
                        "AND": [
                            {"key": "severity", "operator": "!=", "value": "Average"},
                            {"key": "tags", "operator": "=", "value": "Application"},
                        ]
                    }
                ]
            },
        ]
    }
}
input_string_10 = (
    "Теги = Application OR Важность != Average OR КЕ = one AND Теги == Inventory"
)

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
input_string_11 = (
    "Теги = Application AND Источник != self-dev AND Ack = Commented AND Flp != No"
)
parse_result_11 = {
    "filter": {
        "AND": [
            {"OR": [{"key": "host", "operator": "==", "value": "FAKE32"}]},
            {"OR": [{"key": "tags", "operator": "==", "value": "OS:Linux"}]},
            {
                "AND": [
                    {
                        "AND": [
                            {"key": "flap", "operator": "!=", "value": "No"},
                            {
                                "AND": [
                                    {
                                        "key": "ack_status",
                                        "operator": "=",
                                        "value": "Commented",
                                    },
                                    {
                                        "AND": [
                                            {
                                                "key": "source",
                                                "operator": "!=",
                                                "value": "self-dev",
                                            },
                                            {
                                                "key": "tags",
                                                "operator": "=",
                                                "value": "Application",
                                            },
                                        ]
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
