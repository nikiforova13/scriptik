import pytest
from test_data import *
from parser import generate_filter

TEST_HOSTNAME = "FAKE32"
TEST_TAGS = ["OS:Linux"]


@pytest.mark.parametrize(
    "test_input,excepted_result",
    [
        (input_string_1, excepted_result_1),
        (input_string_2, excepted_result_2),
        (input_string_3, excepted_result_3),
        (input_string_4, excepted_result_4),
        (input_string_5, excepted_result_5),
        (input_string_6, excepted_result_6),
        (input_string_7, excepted_result_7),
        (input_string_8, excepted_result_8),
        (input_string_9, excepted_result_9),
        (input_string_10, excepted_result_10),
        (input_string_11, excepted_result_11),
        (input_string_12, excepted_result_12),
        (input_string_13, excepted_result_13),
        (input_string_14, excepted_result_14),
        (input_string_15, excepted_result_15),
    ],
)
def test_parser_string(test_input, excepted_result):
    assert (
        generate_filter(
            filter_string=test_input, hostname=TEST_HOSTNAME, tags=TEST_TAGS
        )
        == excepted_result
    )
