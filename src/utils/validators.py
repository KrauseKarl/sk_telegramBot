from src.database import exceptions


async def target_price_validator(price: float) -> bool:
    """Функция проверяет чтобы целевая цена > 0 и < 1 000 000."""
    if price < 1:
        raise exceptions.CustomError(
            message="\nЦена должна быть положительной\n🔄 попробуйте еще раз"
        )
    if 1000000 < price:
        raise exceptions.CustomError(
            message="\nЦена не должна быть больше 1000000\n🔄 попробуйте еще раз"
        )
    return True


async def min_price_validator(price: int) -> bool:
    """Функция проверяет чтобы минимальная цена > 0."""
    if int(price) < 1:
        raise exceptions.CustomError(
            message="Минимальная цена должна быть больше 0\n🔄 попробуйте еще раз"
        )
    return True


async def max_price_validator(min_price: int, max_price: int) -> bool:
    """Функция проверяет чтобы максимальная цена > минимальной цены."""
    if min_price > max_price:
        raise exceptions.CustomError(
            message="Максимальная цена должна быть больше минимальной\t"
            "🔄\tпопробуйте еще раз"
        )
    return True
