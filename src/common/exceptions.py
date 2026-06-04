"""Custom exception hierarchy for AutoTest-Agent."""


class AutoTestError(Exception):
    """Base exception for all AutoTest-Agent errors."""

    def __init__(self, message: str, code: str = "AUTOTEST_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class NotFoundError(AutoTestError):
    """Resource not found."""

    def __init__(self, resource: str, identifier: str):
        super().__init__(
            message=f"{resource} with id '{identifier}' not found",
            code="NOT_FOUND",
        )
        self.resource = resource
        self.identifier = identifier


class ValidationError(AutoTestError):
    """Input validation error."""

    def __init__(self, message: str, field: str = None):
        super().__init__(message=message, code="VALIDATION_ERROR")
        self.field = field


class SandboxError(AutoTestError):
    """Sandbox execution error."""

    def __init__(self, message: str, sandbox_id: str = None):
        super().__init__(message=message, code="SANDBOX_ERROR")
        self.sandbox_id = sandbox_id


class LLMProviderError(AutoTestError):
    """LLM provider communication error."""

    def __init__(self, message: str, provider: str = None):
        super().__init__(message=message, code="LLM_ERROR")
        self.provider = provider


class TaskSchedulingError(AutoTestError):
    """Task scheduling / queue error."""

    def __init__(self, message: str):
        super().__init__(message=message, code="SCHEDULING_ERROR")