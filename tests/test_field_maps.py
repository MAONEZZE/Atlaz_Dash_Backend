import pytest
from app.core.field_maps import resolve_field, resolve_name


@pytest.mark.parametrize("label,expected", [
    ("nome", "nome"),
    ("NOME", "nome"),
    ("Responsável", "nome"),
    ("responsavel", "nome"),
    ("Cargo", "cargo"),
    ("canal", "canal"),
    ("Origem", "canal"),
    ("bruto", "bruto"),
    ("Receita Bruta", "bruto"),
    ("completely_unknown_xyz", None),
])
def test_resolve_field(label, expected):
    assert resolve_field(label) == expected


@pytest.mark.parametrize("name,expected", [
    ("jonny", "Jonathan"),
    ("JONNY", "Jonathan"),
    ("Jônny", "Jonathan"),   # accent variant
    ("Jonathan", "Jonathan"),
    ("jacob", "Jacob"),
    ("jennifer", "Jennifer"),
    ("jenny", "Jennifer"),
    ("alex", "Alex"),
    ("alexandre", "Alex"),
    ("UnknownPerson", "Unknownperson"),  # title-cased passthrough
])
def test_resolve_name(name, expected):
    assert resolve_name(name) == expected
