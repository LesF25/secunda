from enum import StrEnum, auto


class PaymentStatus(StrEnum):
    PENDING = auto()
    SUCCEEDED = auto()
    FAILED = auto()

    @property
    def is_terminal(self) -> bool:
        return self in TERMINAL_STATUS

TERMINAL_STATUS = {
    PaymentStatus.SUCCEEDED,
    PaymentStatus.FAILED,
}
