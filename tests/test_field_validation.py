from datetime import datetime, timedelta
from uuid import UUID, uuid4

import pytest

from stelar.client.proxy import *
from stelar.client.proxy.fieldvalidation import FieldValidator


def test_basic_checks():
    val = FieldValidator()
    assert val.validate(None) is None
    assert val.validate(2) == 2


def test_nullable():
    nv = AnyField(nullable=True)
    nnv = AnyField(nullable=False)

    assert nv.validate(None) is None
    with pytest.raises(ValueError):
        nnv.validate(None)


def test_minimum_value():
    v = AnyField(minimum_value=10)
    assert v.validate(None) is None
    assert v.validate(20) == 20
    assert v.validate(10) == 10
    with pytest.raises(ValueError):
        v.validate(9)
    with pytest.raises(ValueError):
        v.validate(0)


def test_maximum_value():
    v = AnyField(maximum_value=10)
    assert v.validate(None) is None
    assert v.validate(-20) == -20
    assert v.validate(10) == 10
    with pytest.raises(ValueError):
        v.validate(19)
    with pytest.raises(ValueError):
        v.validate(11)


def test_max_min_length():
    v = StrField(minimum_len=3, maximum_len=5)

    assert v.prioritized_checks == [
        (v.check_null, -1),
        (v.to_ftype, 5),
        (v.check_length, 20),
    ]

    assert v.validate("abc") == "abc"
    assert v.validate("abcde") == "abcde"

    for s in ["", "a", "sf", "123456", "adlasdjasdasdlas"]:
        with pytest.raises(ValueError):
            v.validate(s)


def test_str_field():
    v = StrField()
    assert v.validate(10) == "10"
    assert v.validate(True) == "True"
    assert v.validate("10 312") == "10 312"
    assert v.validate("") == ""


def test_int_field():
    v = IntField()

    assert v.validate(-1231) == -1231
    assert v.validate(1.4) == 1
    assert v.validate(False) == 0
    assert v.validate("14") == 14

    with pytest.raises(ValueError):
        v.validate("aaa")


def test_bool_field():
    v = BoolField()

    assert v.validate(True) is True
    assert v.validate(False) is False
    assert v.validate(-1231) is True
    assert v.validate(1.4) is True
    assert v.validate(0) is False
    assert v.validate(0.0) is False
    assert v.validate([]) is False
    assert v.validate("14") is True
    assert v.validate("") is False


def test_no_checks():
    v = FieldValidator(nullable=None)
    assert v.prioritized_checks == []
    assert v.checks == []


def test_strict():
    v = AnyField(nullable=None, strict=True)
    assert v.prioritized_checks == []
    assert v.checks == []

    for s in [None, 1, "aa", ...]:
        with pytest.raises(ValueError):
            v.validate(s)

    assert v.convert_to_entity(10) == 10
    assert v.convert_to_proxy(10) == 10


def test_date_field():
    v = DateField(nullable=False, minimum_value=datetime(2020, 1, 1))

    n = datetime.now()
    assert v.validate(n) == n
    tendays = timedelta(days=10)
    assert v.validate(n - tendays) == n - tendays

    with pytest.raises(ValueError):
        v.validate(datetime(2019, 12, 31, 23, 59))
    with pytest.raises(ValueError):
        v.validate(None)

    assert v.validate(n.isoformat()) == n
    assert v.validate("2022-11-11") == datetime.fromisoformat("2022-11-11")
    with pytest.raises(ValueError):
        v.validate("2022/11/11")
    with pytest.raises(ValueError):
        v.validate(12313)

    assert v.convert_to_entity(n) == n.isoformat()
    assert v.convert_to_proxy(n.isoformat()) == n


def test_uuid_field():
    v = UUIDField()

    u = uuid4()
    assert v.validate(str(u)) == u
    assert v.validate(u) == u
    with pytest.raises(ValueError):
        v.validate(1192929292)

    assert v.convert_to_entity(u) == str(u)
    assert v.convert_to_proxy(str(u)) == u


def test_state_field():
    v = StateField()

    assert v.validate("active")
    assert v.validate("deleted")

    for val in ("", "ACTIVE", 4, None):
        with pytest.raises(ValueError):
            assert v.validate(val)
