# tests/test_sys_utils.py

import pytest
from collections import namedtuple, OrderedDict

# Import the functions to test
from kiauh.utils.sys_utils import namedtuple_to_dict, compare_dict


# Sample namedtuples for testing
Point = namedtuple("Point", "x y")
Person = namedtuple("Person", "name age address")
Address = namedtuple("Address", "street city")


@pytest.fixture
def sample_data():
    """Provide reusable sample data including nested structures."""
    addr = Address(street="123 Main St", city="Springfield")
    person = Person(name="Alice", age=30, address=addr)
    point = Point(x=10, y=20)

    return {
        "person": person,
        "point": point,
        "addr": addr,
    }


def test_namedtuple_to_dict_basic(sample_data):
    point = sample_data["point"]
    result = namedtuple_to_dict(point)
    expected = {"x": 10, "y": 20}
    assert result == expected
    assert isinstance(result, dict)


def test_namedtuple_to_dict_nested(sample_data):
    person = sample_data["person"]
    result = namedtuple_to_dict(person)
    expected = {
        "name": "Alice",
        "age": 30,
        "address": sample_data["addr"],  # still a namedtuple at this level
    }
    assert result == expected
    # Note: nested namedtuple is not recursively converted
    #   (only is during compare_dict).
    assert isinstance(result["address"], Address)


def test_compare_dict_identical_dicts():
    d1 = {"a": 1, "b": {"c": 2, "d": 3}}
    d2 = {"a": 1, "b": {"c": 2, "d": 3}}
    assert compare_dict(d1, d2) is True
    assert compare_dict(d2, d1) is True


def test_compare_dict_different_order_same_content():
    d1 = {"a": 1, "b": 2}
    d2 = {"b": 2, "a": 1}
    assert compare_dict(d1, d2) is True


def test_compare_dict_missing_key():
    d1 = {"a": 1, "b": 2}
    d2 = {"a": 1}
    assert compare_dict(d1, d2) is False
    assert compare_dict(d2, d1) is False


def test_compare_dict_different_values():
    d1 = {"a": 1}
    d2 = {"a": 2}
    assert compare_dict(d1, d2) is False


def test_compare_dict_with_None():
    assert compare_dict(
        {'a': None, 'b': 2},
        {'a': None, 'b': 2}
    )
    assert compare_dict(
        {'a': {'c': 3}, 'b': None},
        {'a': {'c': 3}, 'b': None}
    )
    assert not compare_dict(
        {'a': None, 'b': 2},
        {'a': None, 'b': 2, 'c': 3}
    )
    assert not compare_dict(
        {'a': None, 'b': 2, 'c': 3},
        {'a': None, 'b': 2}
    )
    assert not compare_dict(
        {'a': None, 'b': 2},
        {'a': {'c': 3}, 'b': 2}
    )
    assert not compare_dict(
        {'a': {'c': 3}, 'b': 2},
        {'a': None, 'b': 2}
    )


def test_compare_dict_with_namedtuple(sample_data):
    person = sample_data["person"]
    person_dict = {"name": "Alice", "age": 30, "address": sample_data["addr"]}

    # Try manual conversion first to eliminate issues in deeper calls:
    person_d = namedtuple_to_dict(person)
    person_d['address'] = namedtuple_to_dict(person_d['address'])
    person_dict_d = dict(person_dict)  # shallow copy
    person_dict_d['address'] = namedtuple_to_dict(person_dict_d['address'])
    assert person_d == person_dict_d
    assert compare_dict(person_d, person_dict_d) is True

    # Try automatic conversion:
    # namedtuple vs dict with same structure
    assert compare_dict(person, person_dict, verbose=True) is True
    assert compare_dict(person_dict, person, verbose=True) is True

    # Convert namedtuple to dict and compare
    person_as_dict = namedtuple_to_dict(person)
    person_as_dict["address"] = namedtuple_to_dict(person_as_dict["address"])
    full_dict = {"name": "Alice", "age": 30, "address": {"street": "123 Main St", "city": "Springfield"}}

    assert compare_dict(person, full_dict) is True
    # ^ namedtuple is converted to dict


def test_compare_dict_nested_namedtuple_deep_conversion(sample_data):
    addr = sample_data["addr"]
    person = sample_data["person"]

    # Deep dict version
    expected = {
        "name": "Alice",
        "age": 30,
        "address": {"street": "123 Main St", "city": "Springfield"}
    }

    assert compare_dict(person, expected) is True


def test_compare_dict_ordereddict():
    od1 = OrderedDict([("z", 3), ("a", 1), ("b", 2)])
    od2 = OrderedDict([("a", 1), ("b", 2), ("z", 3)])
    d = {"a": 1, "b": 2, "z": 3}

    assert compare_dict(od1, od2) is True
    assert compare_dict(od1, d) is True
    assert compare_dict(d, od2) is True


def test_compare_dict_different_types_but_same_content(sample_data):
    point = sample_data["point"]
    point_dict = {"x": 10, "y": 20}
    point_tuple_as_dict = namedtuple_to_dict(point)

    assert compare_dict(point, point_dict) is True
    assert compare_dict(point, point_tuple_as_dict) is True
    assert compare_dict(point_dict, point) is True


def test_compare_dict_extra_key_in_second():
    d1 = {"a": 1}
    d2 = {"a": 1, "b": 2}
    assert compare_dict(d1, d2) is False
    assert compare_dict(d2, d1) is False


def test_compare_dict_none_inputs():
    with pytest.raises(AssertionError):
        compare_dict(None, {"a": 1})
    with pytest.raises(AssertionError):
        compare_dict({"a": 1}, None)
    with pytest.raises(AssertionError):
        compare_dict(None, None)


def test_compare_dict_empty_structures():
    assert compare_dict({}, {}) is True
    Empty = namedtuple("Empty", [])
    e1 = Empty()
    e2 = Empty()
    assert compare_dict(e1, {}) is True
    assert compare_dict({}, e2) is True
    assert compare_dict(e1, e2) is True


def test_compare_dict_different_nesting():
    d1 = {"a": {"b": 1}}
    d2 = {"a": {"b": 1, "c": 2}}
    assert compare_dict(d1, d2) is False

    d3 = {"a": 1}
    d4 = {"a": {"b": 1}}
    assert compare_dict(d3, d4) is False


def test_compare_dict_with_lists_fails_gracefully():
    # Since compare_dict only handles mapping-like objects, lists should fail comparison properly
    d1 = {"items": [1, 2, 3]}
    d2 = {"items": [1, 2, 3]}
    assert compare_dict(d1, d2) is True  # lists are compared directly if no .items()


def test_compare_dict_different_list_content():
    d1 = {"items": [1, 2]}
    d2 = {"items": [1, 2, 3]}
    assert compare_dict(d1, d2) is False

    d3 = {"items": [1, 2]}
    d4 = {"items": [2, 1]}
    assert compare_dict(d3, d4) is False  # order matters in lists!


def test_compare_dict_namedtuple_with_extra_field():
    ExtendedPerson = namedtuple("ExtendedPerson", "name age address email")
    p1 = Person(name="Bob", age=35, address=Address("456 Elm", "Shelbyville"))
    p2 = ExtendedPerson(name="Bob", age=35, address=Address("456 Elm", "Shelbyville"), email="bob@example.com")

    assert compare_dict(p1, p2) is False  # p2 has extra field
    assert compare_dict(p2, p1) is False


if __name__ == "__main__":
    pytest.main(["-v", __file__])