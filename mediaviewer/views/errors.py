from django.contrib.auth.decorators import login_required
from mediaviewer.models.error import Error
from mediaviewer.views.views_utils import setSiteWideContext
from django.shortcuts import render
from mediaviewer.utils import logAccessInfo
from mediaviewer.views.password_reset import check_force_password_change


@login_required(login_url='/mediaviewer/login/')
@check_force_password_change
@logAccessInfo
def errors(request, items):
    user = request.user
    if not user.is_staff:
        raise Exception("User is not a staffer!")

    items = int(items)
    if items:
        errors = Error.objects.order_by('-id')[:items]
    else:
        errors = Error.objects.order_by('-id')
    context = {
              'errors': errors,
              'view': 'errors',
              }
    context['active_page'] = 'errors'
    context['title'] = 'Errors'
    setSiteWideContext(context, request, includeMessages=True)
    return render(request, 'mediaviewer/errors.html', context)
