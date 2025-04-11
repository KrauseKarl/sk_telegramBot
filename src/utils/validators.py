from src.database import CustomError


async def target_price_validator(price: float) -> bool:
    if price < 1:
        raise CustomError("\nЦена должна быть положительной" "\n🔄 попробуйте еще раз")
    if 1000000 < price:
        raise CustomError(
            "\nЦена не должна быть больше 1000000" "\n🔄 попробуйте еще раз"
        )
    return True


async def min_price_validator(price: int) -> bool:
    if int(price) < 1:
        raise CustomError(
            "Минимальная цена не должна быть отрицательной\t" "🔄\tпопробуйте еще раз"
        )
    return True


async def max_price_validator(min_price: int, max_price: int) -> bool:
    if min_price > max_price:
        raise CustomError(
            "Максимальная цена должна быть больше минимальной\t"
            "🔄\tпопробуйте еще раз"
        )
    return True
