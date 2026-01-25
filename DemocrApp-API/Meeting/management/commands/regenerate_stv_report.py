"""
Management command to regenerate STV vote reports by re-closing the vote.

Usage:
    python manage.py regenerate_stv_report <vote_id>
    python manage.py regenerate_stv_report --all
"""
import re
from django.core.management.base import BaseCommand

from Meeting.models import Vote


class Command(BaseCommand):
    help = 'Regenerate STV vote report by re-closing the vote'

    def add_arguments(self, parser):
        parser.add_argument('vote_id', nargs='?', type=int, help='ID of the vote to regenerate')
        parser.add_argument('--all', action='store_true', help='Regenerate all closed STV votes')
        parser.add_argument('--seats', type=int, help='Override number of seats (default: infer from existing results)')

    def handle(self, *args, **options):
        if options['all']:
            votes = Vote.objects.filter(method=Vote.STV, state=Vote.CLOSED)
            self.stdout.write(f"Found {votes.count()} closed STV votes")
            for vote in votes:
                self.regenerate_vote(vote, options.get('seats'))
        elif options['vote_id']:
            try:
                vote = Vote.objects.get(pk=options['vote_id'])
            except Vote.DoesNotExist:
                self.stderr.write(f"Vote with ID {options['vote_id']} not found")
                return
            self.regenerate_vote(vote, options.get('seats'))
        else:
            self.stderr.write("Please provide a vote_id or use --all")

    def infer_num_seats(self, vote):
        """Infer number of seats from the old results format."""
        # Old format: "Winners: ['Apple', 'Banana'] \nLosers:..."
        # Try to parse the winners list
        results = vote.results or ""

        # Match "Winners: ['name1', 'name2']" or "Winners: [0, 1]"
        match = re.search(r"Winners:\s*\[([^\]]*)\]", results)
        if match:
            winners_str = match.group(1)
            if winners_str.strip():
                # Count comma-separated items
                winners = [w.strip() for w in winners_str.split(",") if w.strip()]
                return len(winners)

        return None

    def regenerate_vote(self, vote, seats_override=None):
        if vote.method != Vote.STV:
            self.stderr.write(f"Vote {vote.pk} is not an STV vote (method: {vote.method})")
            return

        # Determine number of seats
        if seats_override:
            num_seats = seats_override
        else:
            num_seats = self.infer_num_seats(vote)
            if num_seats is None:
                self.stderr.write(f"  Could not infer num_seats for vote {vote.pk}, skipping. Use --seats to specify.")
                return

        self.stdout.write(f"Regenerating vote {vote.pk}: {vote.name} ({num_seats} seat(s))")

        # Set back to LIVE
        vote.state = Vote.LIVE
        vote.save()

        # Re-close with the inferred number of seats
        vote.close(num_seats)

        self.stdout.write(self.style.SUCCESS(f"  Vote {vote.pk} re-closing..."))
