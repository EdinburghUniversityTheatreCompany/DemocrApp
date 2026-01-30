from django import template
from django.template import context
from django.urls import reverse
from django.utils.html import format_html
from ..models import Vote

register = template.Library()


@register.simple_tag(name="vote_action_button")
def vote_action_button(vote):
    args = [vote.token_set.meeting_id, vote.id]

    if vote.state == Vote.READY:
        return format_html("<a class='btn btn-sm btn-success' href='{}'>{}</a>",
            reverse('meeting/open_vote', args=args),
            "Open Vote")
    elif vote.state == Vote.LIVE:
        # Check if vote has required fields set, if not redirect to fallback page
        if vote.method == Vote.STV and not vote.num_seats:
            return format_html("<a class='btn btn-sm btn-warning' href='{}'>{}</a>",
                reverse('meeting/close_vote/stv', args=args),
                "Close Vote")
        elif vote.method == Vote.YES_NO_ABS and not vote.majority_threshold:
            return format_html("<a class='btn btn-sm btn-warning' href='{}'>{}</a>",
                reverse('meeting/close_vote/yna', args=args),
                "Close Vote")
        else:
            # Has required fields, can close directly
            return format_html("<a class='btn btn-sm btn-warning' href='{}'>{}</a>",
                reverse('meeting/close_vote', args=args),
                "Close Vote")
    elif vote.state == Vote.COUNTING:
        return format_html("{}", "Counting")
    elif vote.state == Vote.NEEDS_TIE_BREAKER:
        return format_html("<a class='btn btn-sm btn-secondary' href='{}'>{}</a>",
            reverse('meeting/break_tie', args=args),
            "Needs Tie Breaker")
    elif vote.state == Vote.CLOSED:
        return format_html("{}", "-")

    return format_html("{}", "")


@register.simple_tag(name="vote_responses_or_remove")
def vote_responses_or_remove(vote, token):
    if vote.state == Vote.READY:
        return format_html("""<form action='{}' method='POST'>
        <input type='hidden' name='csrfmiddlewaretoken' value='{}' />
        <input type='hidden' name='_method' value='DELETE'>
        <input class='btn btn-sm btn-danger' type='submit' value='Delete'>
        </form>""",
            reverse('meeting/manage_vote', args=[vote.token_set.meeting_id, vote.id]),
            token)
    else:
        return vote.responses()


@register.simple_tag(name="option_remove_button")
def option_remove_button(option):
    if option.vote.method != Vote.YES_NO_ABS and option.vote.state == Vote.READY:
        return format_html("<button class='btn btn-sm btn-danger m-1' type='button' onclick='remove_option({})'>remove</button>", option.id)
    return format_html("{}", "")
