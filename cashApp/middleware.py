# cashApp/middleware.py
from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect


class FrozenUserMiddleware:
    """
    Log out any authenticated user whose account has been frozen.

    Login already refuses frozen accounts, but without this a user who is frozen
    while signed in keeps their session (and full access) until it expires.
    Because Django reloads the user from the database on every request, a freeze
    takes effect on that user's very next request.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if user is not None and user.is_authenticated and getattr(user, 'is_frozen', False):
            logout(request)
            messages.error(
                request, 'Your account has been frozen. Please contact the administrator.'
            )
            return redirect('login')
        return self.get_response(request)