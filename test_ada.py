"""
test_ada.py

Richard E. Rawson
2019-07-31

Program Description:

"""

import pytest

# import ada


# def test_sub():
#     stack = [10, 5, 0, 0]
#     result = ada.sub(stack[0])
#     assert result == -5


def test_file1_method1():
    x = 5
    y = 6
    assert x + 1 == y, "test failed"
    # assert x == y, "test failed"


def test_file1_method2():
    x = 5
    y = 6
    assert x + 1 == y, "test failed"
