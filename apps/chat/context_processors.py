from .models import ChatRestriction


def restriction_status(request):
    """Добавляет в контекст информацию о текущем ограничении пользователя (если есть)."""
    if not request.user.is_authenticated:
        return {}

    try:
        restriction = getattr(request.user, 'chat_restriction', None)
        if restriction and restriction.is_active():
            return {
                'chat_restriction': {
                    'restricted_write': restriction.restricted_write,
                    'purchasable': restriction.purchasable,
                    'price': str(restriction.price) if restriction.price else None,
                    'restrict_forum_reply': restriction.restrict_forum_reply,
                    'restrict_server_view': restriction.restrict_server_view,
                }
            }
    except Exception:
        pass
    return {}
