from pytest import raises

from colectica_api import ColecticaObject


def test_no_such_item_code():
    with raises(KeyError):
        ColecticaObject.item_code("ThereIsNoSuchKey")


def test_no_such_item_code_inv():
    with raises(KeyError):
        ColecticaObject.item_code_inv("ThereIsNoSuchKey")


def test_item_code():
    x = ColecticaObject.item_code("Question")
    assert x == "a1bb19bd-a24a-4443-8728-a6ad80eb42b8"
    y = ColecticaObject.item_code_inv(x)
    assert y == "Question"
