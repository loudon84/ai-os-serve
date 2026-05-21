from __future__ import annotations


class CopilotError(Exception):
    def __init__(self, message: str, *, code: str = "copilot_error") -> None:
        self.message = message
        self.code = code
        super().__init__(message)


class NotFoundError(CopilotError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="not_found")


class ConflictError(CopilotError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="conflict")


class GatewayError(CopilotError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="gateway_error")


class HermesClientError(CopilotError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="hermes_client_error")


class TeamHubError(CopilotError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="team_hub_error")


class PolicyError(CopilotError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="policy_denied")


class StateMachineError(CopilotError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="invalid_state_transition")
