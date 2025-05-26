import pytest
from tracking.steps.step_counter import StepCounter

def test_initial_total_zero():
    sc = StepCounter()
    assert sc.total_steps() == 0


def test_add_steps_increases_count():
    sc = StepCounter()
    sc.add_steps(5)
    sc.add_steps(3)
    assert sc.total_steps() == 8


def test_reset_sets_to_zero():
    sc = StepCounter()
    sc.add_steps(10)
    sc.reset()
    assert sc.total_steps() == 0


def test_add_negative_steps_raises():
    sc = StepCounter()
    with pytest.raises(ValueError):
        sc.add_steps(-1)
