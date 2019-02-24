from functools import wraps

from django.urls import reverse
from django.shortcuts import render
from django.contrib.auth.views import (PasswordResetView,
                                       PasswordResetConfirmView,
                                       PasswordResetDoneView,
                                       PasswordResetCompleteView,
                                       PasswordChangeView,
                                       PasswordChangeDoneView,
                                       )
from django.contrib.auth.models import User
from mediaviewer.views.views_utils import setSiteWideContext
from mediaviewer.forms import (MVSetPasswordForm,
                               MVPasswordChangeForm,
                               PasswordResetFormWithBCC,
                               )


def reset_confirm(request, uidb64=None, token=None):
    return PasswordResetConfirmView(
            request,
            template_name='mediaviewer/password_reset_confirm.html',
            uidb64=uidb64,
            token=token,
            set_password_form=MVSetPasswordForm,
            post_reset_redirect=reverse('mediaviewer:password_reset_complete')
    ).as_view()


def reset(request):
    if request.method == 'POST' and request.POST['email']:
        email = request.POST['email']
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            return render(request,
                          'mediaviewer/password_reset_no_email.html',
                          {'email': email})

    return PasswordResetView(
            request,
            template_name='mediaviewer/password_reset_form.html',
            email_template_name='mediaviewer/password_reset_email.html',
            subject_template_name='mediaviewer/password_reset_subject.txt',
            post_reset_redirect=reverse('mediaviewer:password_reset_done'),
            password_reset_form=PasswordResetFormWithBCC,
            ).as_view()


def reset_done(request):
    return PasswordResetDoneView(
            request,
            template_name='mediaviewer/password_reset_done.html',
            ).as_view()


def reset_complete(request):
    return PasswordResetCompleteView(
            request,
            template_name='mediaviewer/password_reset_complete.html',
            ).as_view()


def create_new_password(request, uidb64=None, token=None):
    return PasswordResetConfirmView(
            request,
            template_name='mediaviewer/password_create_confirm.html',
            uidb64=uidb64,
            token=token,
            set_password_form=MVSetPasswordForm,
            post_reset_redirect=reverse('mediaviewer:password_reset_complete')
    ).as_view()


def change_password(request):
    context = {'force_change': request.user.settings().force_password_change}
    setSiteWideContext(context, request)
    context['active_page'] = 'change_password'
    return PasswordChangeView(
            request,
            template_name='mediaviewer/change_password.html',
            post_change_redirect=reverse('mediaviewer:change_password_submit'),
            password_change_form=MVPasswordChangeForm,
            extra_context=context,
            ).as_view()


def check_force_password_change(func):
    @wraps(func)
    def wrap(*args, **kwargs):
        request = args and args[0]
        if request and request.user:
            user = request.user
            if user.is_authenticated:
                settings = user.settings()
                if settings.force_password_change:
                    return change_password(request)
        res = func(*args, **kwargs)
        return res
    return wrap


def change_password_submit(request):
    context = {}
    context['active_page'] = 'change_password_submit'
    setSiteWideContext(context, request)
    return PasswordChangeDoneView(
            request,
            template_name='mediaviewer/change_password_submit.html',
            extra_context=context,
            ).as_view()
