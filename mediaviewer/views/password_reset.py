from django.core.urlresolvers import reverse
from django.contrib.auth.views import (password_reset,
                                       password_reset_confirm,
                                       password_reset_done,
                                       password_reset_complete,
                                       )

def reset_confirm(request, uidb64=None, token=None):
    return password_reset_confirm(request,
                                  template_name='mediaviewer/password_reset_confirm.html',
                                  uidb64=uidb64,
                                  token=token,
                                  post_reset_redirect=reverse('mediaviewer:password_reset_complete'))


def reset(request):
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
