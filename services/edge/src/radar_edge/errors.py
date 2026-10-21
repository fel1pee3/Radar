"""Controlled errors: library exceptions and private paths never become CLI output."""


class EdgeError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message
