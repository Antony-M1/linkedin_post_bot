class ErrorNotDeltaGenerator(Exception):
    """
        Its not a delta generator
    """
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
