"""Test projector version and basic imports."""

import projector


def test_version():
    """Test that projector has a version."""
    assert hasattr(projector, '__version__')
    assert projector.__version__ == "0.1.0"


def test_import():
    """Test that projector module can be imported."""
    assert projector is not None
