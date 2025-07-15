"""Tests for the actions module."""

import pytest

from src.ap.actions import Action, Add, AskUser, Divide, Done, Multiply, Subtract


class MockIO:
    """Mock IO for testing."""
    
    def __init__(self, responses=None):
        self.responses = responses or {}
        self.prompts = []
    
    def prompt(self, text):
        """Mock prompt method that returns predefined responses."""
        self.prompts.append(text)
        if text in self.responses:
            return self.responses[text]
        return f"Mock response for {text}"


class TestAction:
    """Tests for the Action base class and its subclasses."""
    
    def test_execute_caches_result(self):
        """Test that execute caches the result."""
        # Create a counter outside the model to track calls
        compute_calls = [0]
        
        # Create a test action that tracks calls to _compute_result using the external counter
        class TestAction(Action):
            def _compute_result(self, **kwargs):
                compute_calls[0] += 1
                return f"Result {compute_calls[0]}"
        
        # Create an instance and execute it multiple times
        action = TestAction()
        
        # First execution should compute the result
        result1 = action.execute()
        assert result1 == "Result 1"
        assert compute_calls[0] == 1
        
        # Second execution should return the cached result
        result2 = action.execute()
        assert result2 == "Result 1"  # Same result
        assert compute_calls[0] == 1  # No additional compute call
    
    def test_add_action(self):
        """Test the Add action."""
        add = Add(a=2, b=3)
        
        # Before execution
        assert add.result == "Not yet calculated"
        
        # After execution
        result = add.execute()
        assert result == 5
        assert add.result == 5
        assert str(add) == "Add(a=2.0, b=3.0), result=5.0"
    
    def test_subtract_action(self):
        """Test the Subtract action."""
        subtract = Subtract(a=5, b=3)
        
        # Before execution
        assert subtract.result == "Not yet calculated"
        
        # After execution
        result = subtract.execute()
        assert result == 2
        assert subtract.result == 2
        assert str(subtract) == "Subtract(a=5.0, b=3.0), result=2.0"
    
    def test_multiply_action(self):
        """Test the Multiply action."""
        multiply = Multiply(a=2, b=3)
        
        # Before execution
        assert multiply.result == "Not yet calculated"
        
        # After execution
        result = multiply.execute()
        assert result == 6
        assert multiply.result == 6
        assert str(multiply) == "Multiply(a=2.0, b=3.0), result=6.0"
    
    def test_divide_action(self):
        """Test the Divide action."""
        divide = Divide(a=6, b=2)
        
        # Before execution
        assert divide.result == "Not yet calculated"
        
        # After execution
        result = divide.execute()
        assert result == 3
        assert divide.result == 3
        assert str(divide) == "Divide(a=6.0, b=2.0), result=3.0"
    
    def test_divide_by_zero(self):
        """Test that dividing by zero raises an error."""
        divide = Divide(a=6, b=0)
        
        # Execution should raise an exception
        with pytest.raises(ValueError, match="Division by zero is not allowed"):
            divide.execute()
    
    def test_ask_user_action(self):
        """Test the AskUser action."""
        # Create a mock IO object
        mock_io = MockIO(responses={"What is your name?": "John"})
        
        # Create an AskUser action
        ask = AskUser(request="What is your name?")
        
        # Before execution
        assert ask.result == "Not yet calculated"
        
        # After execution
        result = ask.execute(io=mock_io)
        assert result == "John"
        assert ask.result == "John"
        assert mock_io.prompts == ["What is your name?"]
        assert str(ask) == "RequestUserInput(request=What is your name?), result=John"
    
    def test_done_action(self):
        """Test the Done action."""
        # Create a Done action with a result
        done = Done(output="Final result")
        
        # Before execution
        assert done.result == "Not yet calculated"
        
        # After execution
        result = done.execute()
        assert result == "Final result"
        assert done.result == "Final result"
        assert str(done) == "Done(output=Final result)"
