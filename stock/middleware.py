from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import reverse

EXEMPT_PATHS = {'/account/login', '/account/create', '/account/logout'}


class RequireCompanyCodeMiddleware:
    """ถ้า user ล็อกอินอยู่แต่ session ไม่มี company_code ให้บังคับ logout และไปหน้า login ใหม่"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path.rstrip('/')
        if (
            request.user.is_authenticated
            and 'company_code' not in request.session
            and path not in EXEMPT_PATHS
            and not path.startswith('/static')
        ):
            logout(request)
            return redirect(reverse('signIn'))

        return self.get_response(request)
