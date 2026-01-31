import logging
from queue import Queue
from threading import Thread
from time import sleep

from openstv.ballots import Ballots
from openstv.MethodPlugins.ScottishSTV import ScottishSTV
from openstv.ReportPlugins.HtmlReport import HtmlReport
from Meeting.voting_methods.vote_method import VoteMethod

logger = logging.getLogger(__name__)


class STV(VoteMethod):

    @classmethod
    def count(cls, vote_id, **kwargs):
        from Meeting.models import Vote
        vote = Vote.objects.get(pk=vote_id)
        seats = kwargs.get("num_seats", 1)
        assert vote.method == Vote.STV
        count_thread = Thread(target=cls._count, args=(vote_id, seats), daemon=True)
        count_thread.start()

    @classmethod
    def _count(cls, vote_id, seats):
        from Meeting.models import Vote, BallotEntry, Tie, Option
        vote = Vote.objects.get(pk=vote_id)
        ballots = Ballots()

        options = vote.option_set.all().order_by('pk')
        option_translation = {}
        names = []
        for index, option in enumerate(options):
            option_translation[option.id] = index
            names.append(option.name)
        ballots.setNames(names)
        ballots.numSeats = seats

        voter = -1
        ballot = []
        for be in BallotEntry.objects.filter(option__vote=vote).order_by('token_id', 'value').all():
            if voter != be.token_id and ballot != []:
                ballots.appendBallot(ballot)
                ballot = []
            voter = be.token_id
            ballot.append(option_translation[be.option_id])
        if ballots != []:
            ballots.appendBallot(ballot)

        electionCounter = ScottishSTV(ballots)
        electionCounter.strongTieBreakMethod = "manual"
        electionCounter.breakTieRequestQueue = Queue(1)
        electionCounter.breakTieResponseQueue = Queue(1)
        countThread = Thread(target=electionCounter.runElection)
        countThread.start()
        while countThread.is_alive():
            sleep(0.1)
            if not electionCounter.breakTieRequestQueue.empty():
                [tiedCandidates, names, what] = electionCounter.breakTieRequestQueue.get()
                c = cls.ask_user_to_break_tie(tiedCandidates, names, what, vote)
                electionCounter.breakTieResponseQueue.put(c)
            if "R" in vars(electionCounter):
                status = "Counting votes using {}\nRound: {}".format(electionCounter.longMethodName,
                                                                     electionCounter.R + 1)
            else:
                status = "Counting votes using %s\nInitializing..." % \
                         electionCounter.longMethodName
            logger.debug(status)
        logger.info(electionCounter.winners)
        vote.refresh_from_db()
        vote.state = Vote.CLOSED
        r = HtmlReport(electionCounter)
        r.generateReport()
        vote.results = r.outputText

        # Store structured results data including round breakdown
        # Build winners list with order and round information
        winners = []
        for i, w in enumerate(electionCounter.winners, start=1):
            winners.append({
                "name": electionCounter.b.names[w],
                "order": i,
                "round": electionCounter.wonAtRound[w] + 1  # Convert to 1-indexed
            })
        loser_names = [electionCounter.b.names[l] for l in electionCounter.losers] if hasattr(electionCounter, 'losers') else []

        vote.results_data = {
            "winners": winners,
            "losers": loser_names,
            "seats": seats,
            "num_ballots": ballots.numBallots if hasattr(ballots, 'numBallots') else 0,
            "rounds": [
                {
                    "round": round_num + 1,
                    "counts": {electionCounter.b.names[c]: float(electionCounter.count[round_num][c]) for c in range(electionCounter.b.numCandidates)},
                    "exhausted": float(electionCounter.exhausted[round_num]),
                }
                for round_num in range(electionCounter.numRounds)
            ]
        }
        vote.save()

    @classmethod
    def ask_user_to_break_tie(cls, tied_candidates, names, what, vote):
        from Meeting.models import Option, Tie
        for candidate in names:
            option = Option.objects.filter(name=candidate, vote=vote).first()
            tie = Tie(vote=vote, option=option)
            tie.save()
        vote.state = vote.NEEDS_TIE_BREAKER
        vote.save()
        while vote.state == vote.NEEDS_TIE_BREAKER:
            sleep(1)
            vote.refresh_from_db()

        if Tie.objects.filter(vote=vote)[:1].count() > 1:
            logger.error('multiple tie objects after vote')
        tie = Tie.objects.filter(vote=vote).first()
        i = names.index(tie.option.name)
        tie.delete()
        return tied_candidates[i]

    @classmethod
    def _handle_ballot(cls, vote, voter_token_id, ballot_entries):
        """
        Handle STV ballot submission with consecutive number validation.

        STV requires preferences to be consecutive integers starting from 1:
        - Valid: {opt1: 1, opt2: 2, opt3: 3}
        - Valid: {opt1: 1, opt2: 2} (partial ranking)
        - Invalid: {opt1: 1, opt2: 3} (skipped 2)
        - Invalid: {opt1: 2, opt2: 3} (didn't start at 1)
        """
        from Meeting.models import BallotEntry

        # Extract and validate preference values
        preferences = []
        for option_id, pref_value in ballot_entries.items():
            try:
                value = int(pref_value)
                if value >= 1:  # Only consider positive preferences
                    preferences.append((option_id, value))
            except (ValueError, TypeError):
                raise ValueError(f"Invalid preference value: {pref_value}")

        # Sort by preference value to check consecutiveness
        preferences.sort(key=lambda x: x[1])

        # Validate consecutive numbering starting from 1
        expected_pref = 1
        for option_id, pref_value in preferences:
            if pref_value != expected_pref:
                raise ValueError(
                    f"Preferences must be consecutive whole numbers starting from 1. "
                    f"Expected {expected_pref}, got {pref_value}"
                )
            expected_pref += 1

        # Save validated ballot entries
        for option_id, pref_value in preferences:
            option = vote.option_set.filter(pk=option_id).first()
            if option is not None:
                be = BallotEntry(option=option, token_id=voter_token_id, value=pref_value)
                be.save()
