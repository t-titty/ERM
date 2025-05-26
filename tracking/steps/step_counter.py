class StepCounter:
    """A simple class to keep track of step counts."""

    def __init__(self):
        """Initialize the internal step count to zero."""
        self._count = 0

    def add_steps(self, n: int):
        """Increase the step count by ``n``.

        Parameters
        ----------
        n : int
            Number of steps to add. Must be non-negative.
        """
        if n < 0:
            raise ValueError("steps must be non-negative")
        self._count += n

    def total_steps(self) -> int:
        """Return the total number of steps recorded."""
        return self._count

    def reset(self):
        """Reset the internal step count back to zero."""
        self._count = 0
