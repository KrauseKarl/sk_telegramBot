from src.database import exceptions


async def target_price_validator(price: str) -> bool:
    """Функция проверяет чтобы целевая цена > 0 и < 1 000 000."""
    try:
        price = float(price)
    except ValueError:
        raise exceptions.CustomError(
            message="\nЦена должна быть числом\n"
                    "🔄 попробуйте еще раз")
    if price < 1:
        raise exceptions.CustomError(
            message="\nЦена должна быть положительной\n"
                    "🔄 попробуйте еще раз"
        )
    if 1000000 < price:
        raise exceptions.CustomError(
            message="\nЦена не должна быть больше 1000000\n"
                    "🔄 попробуйте еще раз"
        )
    return True


async def min_price_validator(price: str) -> bool:
    """Функция проверяет чтобы минимальная цена > 0."""
    try:
        price = float(price)
    except ValueError:
        raise exceptions.CustomError(
            message="\nЦена должна быть числом\n"
                    "🔄 попробуйте еще раз")
    if int(price) < 1:
        raise exceptions.CustomError(
            message=f"Минимальная цена {price} должна быть больше 0\n"
                    f"🔄 попробуйте еще раз"
        )
    return True


async def max_price_validator(min_price: str, max_price: str) -> bool:
    """Функция проверяет чтобы максимальная цена > минимальной цены."""
    await min_price_validator(min_price)
    try:
        max_price = float(max_price)
    except ValueError:
        raise exceptions.CustomError(
            message="\nЦена должна быть числом\n"
                    "🔄 попробуйте еще раз")
    if float(min_price) > float(max_price):
        raise exceptions.CustomError(
            message="Максимальная цена должна быть больше минимальной\t"
                    "🔄\tпопробуйте еще раз"
        )
    return True
