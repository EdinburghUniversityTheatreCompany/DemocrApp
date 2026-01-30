import random
from django.shortcuts import get_object_or_404, render
from Meeting.models import Vote, TokenSet, BallotEntry


def public_vote_report(request, public_id):
    """Public view of single vote with anonymized ballots"""
    vote = get_object_or_404(Vote, public_id=public_id, state=Vote.CLOSED)

    # Anonymize ballots
    anonymized_ballots = _anonymize_ballots(vote)

    context = {
        'vote': vote,
        'ballots': anonymized_ballots,
        'is_public': True,
    }
    return render(request, 'meeting/public_vote_report.html', context)


def public_meeting_report(request, token_set_id):
    """Public view of meeting with summary + all vote details"""
    token_set = get_object_or_404(TokenSet, id=token_set_id)
    votes = token_set.vote_set.filter(
        state=Vote.CLOSED,
        hide_from_public_report=False
    ).order_by('id')

    # Build summary data
    summary_rows = []
    for vote in votes:
        outcome = _format_outcome(vote)
        summary_rows.append({
            'name': vote.name,
            'outcome': outcome,
            'public_id': vote.public_id,
        })

    context = {
        'token_set': token_set,
        'summary_rows': summary_rows,
        'votes': votes,
        'is_public': True,
    }
    return render(request, 'meeting/public_meeting_report.html', context)


def _anonymize_ballots(vote):
    """Convert ballots to sequential anonymous IDs with random order"""
    ballots = list(BallotEntry.objects.filter(option__vote=vote).select_related('option').all())
    random.shuffle(ballots)

    anonymized = []
    for idx, ballot in enumerate(ballots, 1):
        anonymized.append({
            'id': f"Ballot {idx}",
            'option': ballot.option,
            'value': ballot.value,
            'ballot': ballot,  # For template access to related data
        })

    return anonymized


def _format_outcome(vote):
    """Format outcome string for summary table"""
    if vote.method == Vote.YES_NO_ABS:
        passed = vote.results_data.get('passed')
        percentages = vote.results_data.get('percentages', {})
        yes_pct = percentages.get('yes', 0)
        if passed is not None:
            status = 'PASSED' if passed else 'FAILED'
            return f"{status} ({yes_pct:.0f}%)"
        else:
            # Legacy votes without threshold or not yet counted
            return f"Results: {yes_pct:.0f}% Yes"
    else:  # STV
        winners = vote.results_data.get('winners', [])
        winner_names = [w['name'] for w in winners]
        return f"{', '.join(winner_names)} ({len(winners)})"
