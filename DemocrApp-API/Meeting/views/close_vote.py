from django.contrib.auth.decorators import permission_required, login_required
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from ..models import Meeting, Vote


@login_required(login_url='/api/admin/login')
@permission_required('Meeting.add_meeting')
def close_vote(request, meeting_id, vote_id):
    meeting = get_object_or_404(Meeting, pk=meeting_id)
    vote = get_object_or_404(Vote, pk=vote_id)
    if vote.token_set.meeting != meeting or vote.state != vote.LIVE:
        return JsonResponse({'result': 'failure'}, status=401)
    try:
        vote.close()
    except ValueError as e:
        return JsonResponse({'result': 'failure', 'error': str(e)}, status=400)
    message = {'type': 'success'}
    return HttpResponseRedirect(reverse('meeting/manage', args=[meeting.id]))

@login_required(login_url='/api/admin/login')
@permission_required('Meeting.add_meeting')
def close_vote_stv(request, meeting_id, vote_id):
    context = {}
    vote = get_object_or_404(Vote, pk=vote_id)
    meeting = get_object_or_404(Meeting, pk=meeting_id)
    context['vote'] = vote
    context['meeting'] = meeting
    return render(request, 'meeting/close_stv.html', context)
