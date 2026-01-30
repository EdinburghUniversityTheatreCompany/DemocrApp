from django.contrib.auth.decorators import permission_required, login_required
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from ..form import VoteForm
from ..models import Meeting, Vote


@login_required(login_url='/api/admin/login')
@permission_required('Meeting.add_meeting')
def new_vote(request, meeting_id):
    meeting = get_object_or_404(Meeting, pk=meeting_id)
    token_sets = meeting.tokenset_set.order_by('created_at').all()
    if request.method == 'POST':
        form = VoteForm(request.POST)
        if form.is_valid():
            data = form.data
            vote = Vote(name=data['name'],
                        description=data['description'],
                        method=data['method'],
                        token_set=token_sets.latest())

            # Set majority_threshold for YNA votes
            if data.get('majority_threshold'):
                vote.majority_threshold = data['majority_threshold']

            # Set num_seats for STV votes
            if data.get('num_seats'):
                vote.num_seats = int(data['num_seats'])

            vote.save()
            pass
    return HttpResponseRedirect(reverse('meeting/manage', args=[meeting_id]))
