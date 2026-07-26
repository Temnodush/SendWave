from django.contrib.auth.mixins import UserPassesTestMixin


class OwnerRequiredMixin(UserPassesTestMixin):
    """
    Проверяет, что текущий пользователь — владелец объекта.
    """
    def test_func(self):
        obj = self.get_object()
        return obj.owner == self.request.user


class OwnerQuerysetMixin:
    """
    Фильтрует queryset по владельцу.
    Менеджеры видят все объекты.
    """
    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        # Менеджеры и админы видят всё
        if user.is_staff or getattr(user, 'is_manager', False):
            return qs
        return qs.filter(owner=user)


class ManagerRequiredMixin(UserPassesTestMixin):
    """
    Доступ только для менеджеров и админов.
    """
    def test_func(self):
        user = self.request.user
        return user.is_staff or getattr(user, 'is_manager', False)
