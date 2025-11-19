from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponseRedirect
from django.urls import reverse

def anonymous_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            return HttpResponseRedirect(reverse('dashboard'))
        return view_func(request, *args, **kwargs)
    return wrapper

def staff_required(view_func):
    return user_passes_test(lambda u: u.is_staff)(view_func)
