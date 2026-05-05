from .views import is_admin_role, user_has_access


def navigation_access(request):
    user = request.user
    if not user.is_authenticated:
        return {
            'can_menu': False,
            'can_administrador': False,
            'can_comanda': False,
            'can_cocina': False,
            'can_bar': False,
            'can_entregas': False,
            'can_caja': False,
            'can_manage_users': False,
        }

    return {
        'can_menu': user_has_access(user, 'menu'),
        'can_administrador': user_has_access(user, 'administrador'),
        'can_comanda': user_has_access(user, 'comanda'),
        'can_cocina': user_has_access(user, 'cocina'),
        'can_bar': user_has_access(user, 'bar'),
        'can_entregas': user_has_access(user, 'entregas'),
        'can_caja': user_has_access(user, 'caja'),
        'can_manage_users': is_admin_role(user),
    }
