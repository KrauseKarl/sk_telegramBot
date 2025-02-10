from database.models import History, User, Favorite


async def orm_make_record_request(data: dict) -> None:
    History().create(**data).save()


async def orm_make_record_user(user_id: int) -> None:
    History.create(user=user_id, command='start').save()


async def orm_get_or_create_user(user) -> str:
    user, created = User.get_or_create(
        user_id=user.id,
        user_name=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    if created:
        return "🟨 🤚 Добро пожаловать"
    return "🤝 Рады снова видеть вас"


async def orm_get_history_list(user_id: int):
    return History.select().where(History.user == user_id).order_by(History.date)


async def orm_get_or_create_favorite(data):
    favorite, created = Favorite.get_or_create(
        product_id=data.get("product_id"),
        title=data.get("title"),
        price=data.get("price"),
        reviews=data.get("reviews"),
        stars=data.get("stars"),
        url=data.get("url"),
        image=data.get("image"),
        user=data.get("user"),
    )
    print(f"ORM = {favorite.uid} | {created}")
    # if created:
    #     await orm_make_record_favorite(data)
    #     return favorite
    return favorite, created


async def orm_make_record_favorite(data: dict):
    Favorite().create(**data).save()
