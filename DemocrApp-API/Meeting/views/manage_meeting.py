from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

import urllib.parse

from Meeting.form import VoteForm
from ..models import Meeting, Vote, AuthToken, Option


@login_required(login_url='/api/admin/login')
@permission_required('Meeting.add_meeting', raise_exception=True)
def manage_meeting(request, meeting_id):
    context = {}
    meeting = get_object_or_404(Meeting, pk=meeting_id)
    if request.method == "POST":
        return JsonResponse({"result": "failure", "reason": "depreciated method. use /api/meeting/<id>/create_token"})
    else:
        form = VoteForm()
        context['meeting'] = meeting
        context['votes'] = Vote.objects.filter(token_set__meeting=meeting)
        context['form'] = form
        return render(request, 'meeting/meeting.html', context)


@login_required(login_url='/api/admin/login')
@permission_required('Meeting.add_meeting', raise_exception=True)
def close_meeting(request, meeting_id):
    if request.method == "POST":
        meeting = get_object_or_404(Meeting, pk=meeting_id)

        # Check all LIVE votes have required fields set
        votes_missing_fields = []
        for t_set in meeting.tokenset_set.all():
            for vote in t_set.vote_set.filter(state=Vote.LIVE):
                if vote.method == Vote.YES_NO_ABS and not vote.majority_threshold:
                    votes_missing_fields.append(f"{vote.name} (needs majority threshold)")
                elif vote.method == Vote.STV and not vote.num_seats:
                    votes_missing_fields.append(f"{vote.name} (needs number of seats)")

        # If any votes are missing required fields, return error
        if votes_missing_fields:
            return JsonResponse({
                "result": "failure",
                "reason": "Some votes are missing required fields",
                "votes": votes_missing_fields
            }, status=400)

        # All votes have required fields, proceed with closing
        for t_set in meeting.tokenset_set.all():
            for vote in t_set.vote_set.filter(state=Vote.LIVE):
                vote.close()
            for vote in t_set.vote_set.filter(state=Vote.READY):
                vote.delete()

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(meeting.channel_group_name(),
                                                {"type": "announcement",
                                                 "message": "This meeting has now closed"})
        meeting.close_time = timezone.now()
        meeting.save()
        return redirect("meeting/report/meeting", meeting_id=meeting_id)
    return JsonResponse({"result": "failure", "reason": "this endpoint requires POST as it changes state"})


@login_required(login_url='/api/admin/login')
@permission_required('Meeting.add_meeting')
def create_token(request, meeting_id):
    if request.method == "POST":
        meeting = get_object_or_404(Meeting, pk=meeting_id)
        proxy = request.POST['proxy'] == 'true'
        amount = int(request.POST['amount'])

        response = {
            "result": "success",
            "meeting_id": meeting_id,
            "meeting_name": meeting.name,
            "proxy": proxy, 
        }

        # If we just want one code, generate them receipt style.
        if amount == 1:
            authToken = AuthToken(token_set=meeting.tokenset_set.latest(), has_proxy=proxy)
            authToken.save()

            response["token"] = authToken.id
            response["print_url"] = "/print.html?" + urllib.parse.urlencode(
                {'t': authToken.id, 'h': meeting.name, 'p': proxy, 'm': meeting_id}, 
                quote_via=urllib.parse.quote
            )
    
            return JsonResponse(response)
        
        # Otherwise, generate a full page.
        else:
            authTokenIds = []
            for i in range(amount):
                authToken = AuthToken(token_set=meeting.tokenset_set.latest(), has_proxy=proxy)
                authToken.save()
                authTokenIds.append(authToken.id)

            response['tokens'] = authTokenIds
            response["print_url"] = "/bulk_tokens.html?" + urllib.parse.urlencode(
                { 't': authTokenIds, 'h': meeting.name, 'p': proxy }, 
                quote_via=urllib.parse.quote
            )
            return JsonResponse(response)
            
    return JsonResponse({"result": "failure", "reason": "this endpoint requires POST as it changes state"})


@login_required(login_url='/api/admin/login')
@permission_required('Meeting.add_meeting')
def deactivate_token(request, meeting_id):
    if request.method == "POST":
        meeting = get_object_or_404(Meeting, pk=meeting_id)
        at = AuthToken.objects.filter(id=request.POST['key'])
        if not at.exists():
            return JsonResponse({'result': 'failure',
                                 'reason': 'token doesnt exist'})
        elif at.filter(token_set__meeting=meeting).exists():
            at.filter(token_set__meeting=meeting).update(active=False)
            #TODO(close any open websockets (probably through any related sessions))
            return JsonResponse({'result': 'success'})
        else:
            return JsonResponse({'result': 'failure',
                                 'reason': 'token is for a different meeting'})
    return JsonResponse({"result": "failure", "reason": "this endpoint requires POST as it changes state"})


@login_required(login_url='/api/admin/login')
@permission_required('Meeting.add_meeting', raise_exception=True)
def get_ballot_candidates(request, meeting_id, vote_id):
    """Get ballot candidates as JSON for modal interface."""
    meeting = get_object_or_404(Meeting, pk=meeting_id)
    vote = get_object_or_404(Vote, pk=vote_id)

    if vote.token_set.meeting != meeting:
        return JsonResponse({"result": "failure"}, status=403)

    candidates = Option.objects.filter(vote=vote).values('id', 'name')
    candidates_list = list(candidates)

    response_data = {
        "ballot_id": vote.id,
        "ballot_name": vote.name,
        "state": vote.state,
        "method": vote.method,
        "candidates": candidates_list,
        "results": vote.results
    }

    # Add vote parameters if set
    if vote.majority_threshold:
        response_data["majority_threshold"] = vote.majority_threshold
    if vote.num_seats:
        response_data["num_seats"] = vote.num_seats

    return JsonResponse(response_data)
