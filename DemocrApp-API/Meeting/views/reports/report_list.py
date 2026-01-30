from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from ...models import Meeting


@login_required(login_url='/api/admin/login')
@permission_required('Meeting.add_meeting', raise_exception=True)
def report_list(request):
    context = {'meetings': Meeting.objects.filter(close_time__isnull=False)}
    return render(request, 'meeting/reports/list.html', context)
