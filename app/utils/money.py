from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


def rupees_to_paise(amount):
    """Convert a positive rupee amount to integer paise without float drift."""
    if isinstance(amount, bool) or amount is None:
        raise ValueError("Amount must be a valid positive number.")
    try:
        value = Decimal(str(amount).strip())
        if not value.is_finite() or value <= 0:
            raise ValueError("Amount must be a finite number greater than zero.")
        rounded = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError, AttributeError):
        raise ValueError("Amount must be a valid positive number.")
    return int(rounded * 100)


def paise_to_rupees(amount_paise):
    return Decimal(int(amount_paise)) / Decimal("100")
