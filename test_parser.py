import pytest
from test_data import *

# from parser import generate_filter
from parser import generate_filter

TEST_HOSTNAME = "FAKE32"
TEST_TAGS = ["OS:Linux"]


@pytest.mark.parametrize(
    "test_input,excepted_result",
    [
        (input_string_1, parse_result_1),
        (input_string_2, parse_result_2),
        (input_string_3, parse_result_3),
        (input_string_4, parse_result_4),
        (input_string_5, parse_result_5),
        (input_string_6, parse_result_6),
        (input_string_7, parse_result_7),
        (input_string_8, parse_result_8),
        (input_string_9, parse_result_9),
        (input_string_10, parse_result_10),
        (input_string_11, parse_result_11),
    ],
)
def test_parser_string(test_input, excepted_result):
    # assert (
    #     generate_filter(TEST_HOSTNAME, TEST_TAGS, filter_string=test_input)
    #     == excepted_result
    # )
    res = generate_filter(
        filter_string=test_input,
        hostname=TEST_HOSTNAME,
        tags=TEST_TAGS
    )
    print(f"{res=}")
    print(f"{excepted_result=}")
    assert res == excepted_result
