"""Custom domain exceptions for pembayaran module (ADR 002)."""


class PaymentError(Exception):
    """Base exception for payment domain errors."""
    pass


class PaymentValidationError(PaymentError):
    """Raised when payment validation fails (e.g. invalid amount, duplicate payment)."""
    pass


class TagihanNotFoundError(PaymentError):
    """Raised when requested Tagihan does not exist."""
    pass


class PaymentAlreadySettledError(PaymentValidationError):
    """Raised when attempting to pay a tagihan that is already paid/settled."""
    pass


class CustomerNotFoundError(PaymentError):
    """Raised when requested customer/barcode is not found."""
    pass
