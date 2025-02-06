from database.models import History, UserModel


def orm_make_record_detail(data: dict) -> None:
    History().create(**data).save()


def orm_make_record_user(user_id: int) -> None:
    History.create(user=user_id, command='start').save()


def orm_get_or_create_user(user) -> str:
    user, created = UserModel.get_or_create(
        user_id=user.id,
        user_name=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    if created:
        orm_make_record_user(user.id)
        return "🟨 🤚 Добро пожаловать"
    return "🤝 Рады снова видеть вас"


async def orm_get_history_list(user_id: int):
    return History.select().where(History.user == user_id).order_by(History.date)
