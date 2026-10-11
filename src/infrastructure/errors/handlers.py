from typing import Never

from fastapi import HTTPException, status


def handle_tariff_not_found() -> Never:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Tariff not found",
    )


def handle_payment_not_found() -> Never:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Payment not found",
    )


def handle_invalid_promo_code() -> Never:
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail="Invalid promo code",
    )


def handle_validation_error(error_msg: str) -> Never:
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail=error_msg,
    )


def handle_internal_error(error: Exception) -> Never:
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Internal server error: {error!s}",
    )
