from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
import logging

from ..models import Meeting, Vote, Option

logger = logging.getLogger(__name__)

@login_required(login_url='/api/admin/login')
@permission_required('Meeting.add_meeting')
def add_option(request, meeting_id, vote_id):
    meeting = get_object_or_404(Meeting, pk=meeting_id)
    vote = get_object_or_404(Vote, pk=vote_id)
    if vote.token_set.meeting != meeting or vote.state != Vote.READY or vote.method == Vote.YES_NO_ABS:
        return JsonResponse({"result": "failure"})
    o = Option(name=request.POST['name'], vote=vote)
    o.save()
    return JsonResponse({"result": "success",
                         "id": o.id, })

@login_required(login_url='/api/admin/login')
@permission_required('Meeting.add_meeting')
def remove_option(request, meeting_id, vote_id):
    meeting = get_object_or_404(Meeting, pk=meeting_id)
    vote = get_object_or_404(Vote, pk=vote_id)
    if vote.token_set.meeting != meeting or vote.state != Vote.READY or vote.method == Vote.YES_NO_ABS:
        return JsonResponse({"result": "failure"})

    # Prevent deletion of "None of the above" option
    option = get_object_or_404(Option, pk=request.POST['id'], vote=vote)
    if option.name == "None of the above":
        return JsonResponse({"result": "failure", "reason": "cannot_remove_none_of_the_above"})

    option.delete()
    return JsonResponse({"result": "success"})

@login_required(login_url='/api/admin/login')
@permission_required('Meeting.add_meeting')
def update_vote_field(request, meeting_id, vote_id):
    """Update majority_threshold or num_seats for a vote in READY state"""
    logger.info(f"update_vote_field called: meeting_id={meeting_id}, vote_id={vote_id}")
    logger.info(f"Request method: {request.method}")
    logger.info(f"POST data: {request.POST}")

    meeting = get_object_or_404(Meeting, pk=meeting_id)
    vote = get_object_or_404(Vote, pk=vote_id)

    logger.info(f"Vote state: {vote.state}, method: {vote.method}")

    if vote.token_set.meeting != meeting:
        logger.error("Vote does not belong to meeting")
        return JsonResponse({"result": "failure", "reason": "Vote does not belong to meeting"})

    if vote.state not in [Vote.READY, Vote.LIVE]:
        logger.error(f"Vote not in READY or LIVE state: {vote.state}")
        return JsonResponse({"result": "failure", "reason": f"Vote must be in READY or LIVE state (current: {vote.state})"})

    if request.method == 'POST':
        # Update majority_threshold for YNA votes
        if 'majority_threshold' in request.POST:
            logger.info(f"Updating majority_threshold to {request.POST['majority_threshold']}")
            if vote.method != Vote.YES_NO_ABS:
                logger.error(f"Wrong method for majority_threshold: {vote.method}")
                return JsonResponse({"result": "failure", "reason": "majority_threshold only applies to YNA votes"})
            vote.majority_threshold = request.POST['majority_threshold']
            vote.save()
            logger.info("Successfully updated majority_threshold")
            return JsonResponse({"result": "success"})

        # Update num_seats for STV votes
        if 'num_seats' in request.POST:
            logger.info(f"Updating num_seats to {request.POST['num_seats']}")
            if vote.method != Vote.STV:
                logger.error(f"Wrong method for num_seats: {vote.method}")
                return JsonResponse({"result": "failure", "reason": "num_seats only applies to STV votes"})

            # Validate num_seats is at least 1
            try:
                num_seats = int(request.POST['num_seats'])
                if num_seats < 1:
                    logger.error(f"Invalid num_seats value: {num_seats}")
                    return JsonResponse({"result": "failure", "reason": "Number of seats must be at least 1"})
                vote.num_seats = num_seats
                vote.save()
                logger.info("Successfully updated num_seats")
                return JsonResponse({"result": "success"})
            except ValueError:
                logger.error(f"Invalid num_seats format: {request.POST['num_seats']}")
                return JsonResponse({"result": "failure", "reason": "Number of seats must be a valid number"})

    logger.error("No valid field provided in POST data")
    return JsonResponse({"result": "failure", "reason": "No valid field provided"})
