from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.contrib.auth.views import (password_reset,
                                       password_reset_confirm,
                                       password_reset_done,
                                       password_reset_complete,
                                       )
from django.contrib.auth.models import User
from mediaviewer.models.usersettings import change_user_password, InvalidPasswordException
from mediaviewer.views.home import setSiteWideContext, generateHeader

def reset_confirm(request, uidb64=None, token=None):
    return password_reset_confirm(request,
                                  template_name='mediaviewer/password_reset_confirm.html',
                                  uidb64=uidb64,
                                  token=token,
                                  post_reset_redirect=reverse('mediaviewer:password_reset_complete'))


def reset(request):
    if request.method == 'POST' and request.POST['email']:
        email = request.POST['email']
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            return render(request, 'mediaviewer/password_reset_no_email.html', {'email': email})

    return password_reset(request,
                          template_name='mediaviewer/password_reset_form.html',
                          email_template_name='mediaviewer/password_reset_email.html',
                          subject_template_name='mediaviewer/password_reset_subject.txt',
                          post_reset_redirect=reverse('mediaviewer:password_reset_done'),
                          )

def reset_done(request):
    return password_reset_done(request,
                               template_name='mediaviewer/password_reset_done.html',
                               )

def reset_complete(request):
    return password_reset_complete(request,
                                   template_name='mediaviewer/password_reset_complete.html',
                                   )

def change_password(request):
    context = {'err': ''}
    setSiteWideContext(context, request)
    context['header'] = generateHeader('change_password', request)
    return render(request,
                  'mediaviewer/change_password.html',
                  context)

def change_password_submit(request):
    currentPassword = request.POST['currentPassword']
    newPassword = request.POST['newPassword']
    confirmNewPassword = request.POST['confirmNewPassword']

    context = {}
    template = 'mediaviewer/change_password_submit.html'

    context['header'] = generateHeader('change_password_submit', request)

    try:
        change_user_password(request.user,
                             currentPassword,
                             newPassword,
                             confirmNewPassword)
    except InvalidPasswordException as e:
        context = {'err': str(e)}
        template = 'mediaviewer/change_password.html'

    setSiteWideContext(context, request)
    return render(request,
                  template,
                  context)
