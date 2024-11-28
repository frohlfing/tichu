class ImmutableError(Exception):
    # Ausnahme für unveränderliche Objekte.

    def __init__(self, message="This object is immutable"):
        self.message = message
        super().__init__(self.message)
