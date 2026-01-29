import yaml
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404
from ...models import Meeting, Vote


def meeting_report(request, meeting_id):
    context = {}
    meeting = get_object_or_404(Meeting, pk=meeting_id)
    context['meeting'] = meeting
    context['votes'] = Vote.objects.filter(token_set__meeting=meeting)
    context['token_sets'] = meeting.tokenset_set.all()
    return render(request, 'meeting/reports/meeting.html', context)


def _build_meeting_data(meeting):
    """Build structured data dict for a meeting and its votes."""
    votes = Vote.objects.filter(token_set__meeting=meeting)

    votes_data = []
    for vote in votes:
        vote_data = {
            "id": vote.id,
            "name": vote.name,
            "method": vote.method,
            "method_display": vote.get_method_display(),
            "responses": vote.responses(),
            "options": [
                {"id": opt.id, "name": opt.name}
                for opt in vote.option_set.all()
            ],
            "results": vote.results_data or {},
        }
        # Add majority_threshold for YNA votes
        if vote.method == Vote.YES_NO_ABS:
            vote_data["majority_threshold"] = vote.majority_threshold
        # Add num_seats for STV votes
        if vote.method == Vote.STV:
            vote_data["num_seats"] = vote.num_seats
        votes_data.append(vote_data)

    return {
        "meeting": {
            "id": meeting.id,
            "name": meeting.name,
            "time": meeting.time.isoformat() if meeting.time else None,
            "close_time": meeting.close_time.isoformat() if meeting.close_time else None,
        },
        "votes": votes_data,
    }


def meeting_report_json(request, meeting_id):
    meeting = get_object_or_404(Meeting, pk=meeting_id)
    data = _build_meeting_data(meeting)
    response = JsonResponse(data, json_dumps_params={'indent': 2})
    response['Content-Disposition'] = f'attachment; filename="meeting_{meeting_id}_report.json"'
    return response


def meeting_report_yaml(request, meeting_id):
    meeting = get_object_or_404(Meeting, pk=meeting_id)
    data = _build_meeting_data(meeting)
    yaml_content = yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)
    response = HttpResponse(yaml_content, content_type='application/x-yaml')
    response['Content-Disposition'] = f'attachment; filename="meeting_{meeting_id}_report.yaml"'
    return response
