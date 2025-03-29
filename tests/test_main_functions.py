# pylint: disable=missing-docstring

from src.main import cleanMatchingUsers, cleanMatchingGroups, healthz


def test_cleanMatchingUsers():
    assert cleanMatchingUsers("test") == "test"
    assert cleanMatchingUsers("TEST\n") == "test"
    assert cleanMatchingUsers("   test\n\n") == "test"
    assert cleanMatchingUsers("tEst\n\n\n") == "test"
    assert cleanMatchingUsers("  \n  teSt\n\n\n\n") == "test"


def test_cleanMatchingGroups():
    assert cleanMatchingGroups("test") == "test"
    assert cleanMatchingGroups("TEST\n") == "TEST"
    assert cleanMatchingGroups("   test\n\n") == "test"
    assert cleanMatchingGroups("tEst\n\n\n") == "tEst"
    assert cleanMatchingGroups("  \n  teSt\n\n\n\n") == "teSt"


def test_healthz():
    assert healthz("/healthz") == ("OK", 200)
