from src.database import CustomError


async def target_price_validator(price: float) -> bool:
    if price < 1:
        raise CustomError(
            message="\nЦена должна быть положительной\n🔄 попробуйте еще раз"
        )
    if 1000000 < price:
        raise CustomError(
            message="\nЦена не должна быть больше 1000000\n🔄 попробуйте еще раз"
        )
    return True


async def min_price_validator(price: int) -> bool:
    if int(price) < 1:
        raise CustomError(
            message="Минимальная цена должна быть больше 0\n🔄 попробуйте еще раз"
        )
    return True


async def max_price_validator(min_price: int, max_price: int) -> bool:
    if min_price > max_price:
        raise CustomError(
            message="Максимальная цена должна быть больше минимальной\t"
            "🔄\tпопробуйте еще раз"
        )
    return True
