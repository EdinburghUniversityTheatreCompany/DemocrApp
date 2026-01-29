"""
Management command to regenerate Yes/No/Abstain vote reports by re-closing the vote.

Usage:
    python manage.py regenerate_yna_report <vote_id>
    python manage.py regenerate_yna_report --all
"""
from django.core.management.base import BaseCommand

from Meeting.models import Vote


class Command(BaseCommand):
    help = 'Regenerate Yes/No/Abstain vote report by re-closing the vote'

    def add_arguments(self, parser):
        parser.add_argument('vote_id', nargs='?', type=int, help='ID of the vote to regenerate')
        parser.add_argument('--all', action='store_true', help='Regenerate all closed YNA votes')

    def handle(self, *args, **options):
        if options['all']:
            votes = Vote.objects.filter(method=Vote.YES_NO_ABS, state=Vote.CLOSED)
            self.stdout.write(f"Found {votes.count()} closed YNA votes")
            for vote in votes:
                self.regenerate_vote(vote)
        elif options['vote_id']:
            try:
                vote = Vote.objects.get(pk=options['vote_id'])
            except Vote.DoesNotExist:
                self.stderr.write(f"Vote with ID {options['vote_id']} not found")
                return
            self.regenerate_vote(vote)
        else:
            self.stderr.write("Please provide a vote_id or use --all")

    def regenerate_vote(self, vote):
        if vote.method != Vote.YES_NO_ABS:
            self.stderr.write(f"Vote {vote.pk} is not a YNA vote (method: {vote.method})")
            return

        self.stdout.write(f"Regenerating vote {vote.pk}: {vote.name}")

        # Set back to LIVE
        vote.state = Vote.LIVE
        vote.save()

        # Re-close (YNA votes use num_seats=1)
        vote.close(1)

        self.stdout.write(self.style.SUCCESS(f"  Vote {vote.pk} regenerated successfully"))
