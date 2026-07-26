from django.urls import resolve


def navigation_context(request):
    """Добавляет контекст навигации на все страницы"""

    # Страницы без навигации
    excluded_paths = ['/', '/dashboard/']
    excluded_names = ['home', 'dashboard', 'login', 'register', 'logout']

    try:
        current_url = resolve(request.path)
        url_name = current_url.url_name
    except:
        url_name = None

    show_nav = (
            request.path not in excluded_paths and
            url_name not in excluded_names and
            request.user.is_authenticated
    )

    # Определяем родительскую страницу
    parent_map = {
        # Клиенты
        'client_list': {'parent_name': None, 'parent_url': None, 'current_name': 'Клиенты'},
        'client_detail': {'parent_name': 'Клиенты', 'parent_url': '/dashboard/clients/', 'current_name': 'Просмотр'},
        'client_create': {'parent_name': 'Клиенты', 'parent_url': '/dashboard/clients/', 'current_name': 'Добавление'},
        'client_update': {'parent_name': 'Клиенты', 'parent_url': '/dashboard/clients/',
                          'current_name': 'Редактирование'},

        # Сообщения
        'message_list': {'parent_name': None, 'parent_url': None, 'current_name': 'Сообщения'},
        'message_detail': {'parent_name': 'Сообщения', 'parent_url': '/dashboard/messages/',
                           'current_name': 'Просмотр'},
        'message_create': {'parent_name': 'Сообщения', 'parent_url': '/dashboard/messages/',
                           'current_name': 'Создание'},
        'message_update': {'parent_name': 'Сообщения', 'parent_url': '/dashboard/messages/',
                           'current_name': 'Редактирование'},

        # Рассылки
        'mailing_list': {'parent_name': None, 'parent_url': None, 'current_name': 'Рассылки'},
        'mailing_detail': {'parent_name': 'Рассылки', 'parent_url': '/dashboard/mailings/', 'current_name': 'Просмотр'},
        'mailing_create': {'parent_name': 'Рассылки', 'parent_url': '/dashboard/mailings/', 'current_name': 'Создание'},
        'mailing_update': {'parent_name': 'Рассылки', 'parent_url': '/dashboard/mailings/',
                           'current_name': 'Редактирование'},

        # Статистика
        'user_stats': {'parent_name': None, 'parent_url': None, 'current_name': 'Журнал отправки'},
    }

    nav_data = parent_map.get(url_name, {})

    return {
        'show_nav': show_nav,
        'parent_name': nav_data.get('parent_name'),
        'parent_url': nav_data.get('parent_url'),
        'current_name': nav_data.get('current_name'),
    }
