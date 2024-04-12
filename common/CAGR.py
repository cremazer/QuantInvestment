class CAGR:
    """Compound Annual Growth Rate (CAGR) is a business and investing specific term for the geometric progression ratio that provides a constant rate of return over the time period."""
    def __init__(self, start_value, end_value, periods):
        """Constructor for CAGR class"""
        self.start_value = start_value
        self.end_value = end_value
        self.periods = periods

    def calculate(self):
        """Calculates the CAGR"""
        return ((self.end_value / self.start_value) ** (1 / self.periods)) - 1
