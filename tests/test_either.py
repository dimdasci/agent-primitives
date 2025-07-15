"""Tests for the Either monad implementation."""

from src.ap.either import Either, Left, Right


def test_right_value():
    """Test that Right.value contains the value."""
    r = Right(42)
    assert r.value == 42
    assert r.is_right() is True
    assert r.is_left() is False
    assert str(r) == "Right(42)"


def test_left_error():
    """Test that Left.error contains the error."""
    l = Left("error")
    assert l.error == "error"
    assert l.is_right() is False
    assert l.is_left() is True
    assert str(l) == "Left(error)"


def test_right_map():
    """Test that Right.map applies the function to the value."""
    r = Right(42)
    r2 = r.map(lambda x: x * 2)
    assert isinstance(r2, Right)
    assert r2.value == 84


def test_left_map():
    """Test that Left.map does not apply the function."""
    l = Left("error")
    l2 = l.map(lambda x: x * 2)
    assert isinstance(l2, Left)
    assert l2.error == "error"


def test_right_flat_map():
    """Test that Right.flat_map applies the function to the value."""
    r = Right(42)
    r2 = r.flat_map(lambda x: Right(x * 2))
    assert isinstance(r2, Right)
    assert r2.value == 84
    
    # Test flat_map that returns Left
    r3 = r.flat_map(lambda x: Left("converted to error"))
    assert isinstance(r3, Left)
    assert r3.error == "converted to error"


def test_left_flat_map():
    """Test that Left.flat_map does not apply the function."""
    l = Left("error")
    l2 = l.flat_map(lambda x: Right(x * 2))
    assert isinstance(l2, Left)
    assert l2.error == "error"


def test_right_fold():
    """Test that Right.fold applies the right function."""
    r = Right(42)
    result = r.fold(
        on_left=lambda e: f"Error: {e}",
        on_right=lambda v: f"Value: {v}"
    )
    assert result == "Value: 42"


def test_left_fold():
    """Test that Left.fold applies the left function."""
    l = Left("error")
    result = l.fold(
        on_left=lambda e: f"Error: {e}",
        on_right=lambda v: f"Value: {v}"
    )
    assert result == "Error: error"


def test_pattern_matching():
    """Test pattern matching on Either objects."""
    
    def handle(e: Either):
        match e:
            case Right(value):
                return f"Success: {value}"
            case Left(error):
                return f"Failed: {error}"
            case _:
                return "Unknown"
    
    assert handle(Right(42)) == "Success: 42"
    assert handle(Left("error")) == "Failed: error"
