import logging

from Meeting.voting_methods.vote_method import VoteMethod

logger = logging.getLogger(__name__)


class YNA(VoteMethod):

    @classmethod
    def count(cls, vote_id, **kwargs):
        from Meeting.models import Vote, BallotEntry
        vote = Vote.objects.get(pk=vote_id)
        assert vote.method == Vote.YES_NO_ABS
        counts = {
            vote.option_set.filter(name="yes").first().id: 0,
            vote.option_set.filter(name="no").first().id: 0,
            vote.option_set.filter(name="abs").first().id: 0,
        }
        for be in BallotEntry.objects.filter(option__vote=vote, value=1).order_by('token_id', 'value').all():
            if be.option_id in counts.keys():
                counts[be.option_id] += 1
            else:
                logger.error("suspicious ballot entry with id: {} had non y n a option in a y n a vote")
        y, n, a = counts.values()
        total = y + n + a

        # Calculate percentages
        y_pct = (y / total * 100) if total > 0 else 0
        n_pct = (n / total * 100) if total > 0 else 0
        a_pct = (a / total * 100) if total > 0 else 0

        # Generate HTML results
        html_results = """
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Vote Results</h5>
                <table class="table table-sm">
                    <thead class="table-light">
                        <tr>
                            <th>Option</th>
                            <th>Votes</th>
                            <th>Percentage</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><strong>Yes</strong></td>
                            <td><span class="badge bg-success">{}</span></td>
                            <td>{:.1f}%</td>
                        </tr>
                        <tr>
                            <td><strong>No</strong></td>
                            <td><span class="badge bg-danger">{}</span></td>
                            <td>{:.1f}%</td>
                        </tr>
                        <tr>
                            <td><strong>Abstain</strong></td>
                            <td><span class="badge bg-secondary">{}</span></td>
                            <td>{:.1f}%</td>
                        </tr>
                        <tr class="table-light">
                            <td><strong>Total</strong></td>
                            <td><strong>{}</strong></td>
                            <td><strong>100.0%</strong></td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
        """.format(y, y_pct, n, n_pct, a, a_pct, total)

        vote.results = html_results
        vote.state = Vote.CLOSED
        vote.save()
