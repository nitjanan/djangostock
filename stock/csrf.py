from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme


def csrf_failure(request, reason=""):
    """แทนหน้า 403 ของ Django เมื่อ CSRF token ไม่ตรง (มักเกิดจากฟอร์มเก่าที่เปิดค้างไว้ก่อน login ใหม่)"""
    # ส่งฟอร์ม login ซ้ำ (กดซ้ำ / หน้า login จาก cache) แต่ login สำเร็จไปแล้ว → ไปหน้าแรกเลย
    if request.path.rstrip('/') == reverse('signIn').rstrip('/'):
        if request.user.is_authenticated and 'company_code' in request.session:
            return redirect('home')
        return redirect('signIn')

    back_url = request.META.get('HTTP_REFERER', '')
    if not url_has_allowed_host_and_scheme(back_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        back_url = ''

    return render(request, 'csrf_failure.html', {'back_url': back_url}, status=403)
