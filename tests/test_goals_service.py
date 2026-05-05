from app.services.goals_service import _normalize_cargo


def test_closer_recognized():
    assert _normalize_cargo("Closer") == "Closer"


def test_vendedor_recognized_as_closer():
    assert _normalize_cargo("Vendedor") == "Closer"


def test_sdr_recognized():
    assert _normalize_cargo("SDR") == "SDR"


def test_pre_vendedor_recognized_as_sdr():
    """Bug fix: 'pré-vendedor' must be SDR, not Closer."""
    assert _normalize_cargo("pré-vendedor") == "SDR"
    assert _normalize_cargo("Pre-Vendedor") == "SDR"
    assert _normalize_cargo("Pré Vendedor") == "SDR"


def test_unknown_cargo_passthrough():
    assert _normalize_cargo("Gerente") == "Gerente"
