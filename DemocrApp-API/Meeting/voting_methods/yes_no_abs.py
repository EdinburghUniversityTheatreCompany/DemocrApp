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

        # Calculate majority status (excluding abstentions)
        yes_no_total = y + n
        has_majority = y > n if yes_no_total > 0 else False
        has_two_thirds = y >= (2 * n) if yes_no_total > 0 else False

        # Determine pass/fail based on threshold
        threshold = vote.majority_threshold
        if threshold == 'simple':
            passed = has_majority
            threshold_label = "Simple Majority"
        elif threshold == 'two_thirds':
            passed = has_two_thirds
            threshold_label = "Two-Thirds Majority (66.67%)"
        else:
            # Legacy votes without threshold set
            passed = None
            threshold_label = None

        # Choose card styling + header based on outcome
        if passed is True:
            card_class = "card border-start border-success border-4"
            header_class = "card-header bg-success-subtle text-success-emphasis"
            header_title = "✓ Motion Passed"
        elif passed is False:
            card_class = "card border-start border-danger border-4"
            header_class = "card-header bg-danger-subtle text-danger-emphasis"
            header_title = "✗ Motion Failed"
        else:
            card_class = "card"
            header_class = "card-header"
            header_title = "Vote Results"

        threshold_line = (
            '<div class="mt-1">Threshold: {}</div>'.format(threshold_label)
            if threshold_label else ''
        )

        html_results = """
        <div class="{card_class}">
            <div class="{header_class}">
                <h5 class="mb-0">{header_title}</h5>
                {threshold_line}
            </div>
            <div class="card-body">
                <table class="table table-sm mb-0">
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
                            <td><span class="badge bg-success">{y}</span></td>
                            <td>{y_pct:.1f}%</td>
                        </tr>
                        <tr>
                            <td><strong>No</strong></td>
                            <td><span class="badge bg-danger">{n}</span></td>
                            <td>{n_pct:.1f}%</td>
                        </tr>
                        <tr>
                            <td><strong>Abstain</strong></td>
                            <td><span class="badge bg-secondary">{a}</span></td>
                            <td>{a_pct:.1f}%</td>
                        </tr>
                        <tr class="table-light">
                            <td><strong>Total</strong></td>
                            <td><strong>{total}</strong></td>
                            <td><strong>100.0%</strong></td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
        """.format(
            card_class=card_class,
            header_class=header_class,
            header_title=header_title,
            threshold_line=threshold_line,
            y=y, y_pct=y_pct,
            n=n, n_pct=n_pct,
            a=a, a_pct=a_pct,
            total=total,
        )

        vote.results = html_results
        vote.results_data = {
            "yes": y,
            "no": n,
            "abstain": a,
            "total": total,
            "percentages": {
                "yes": round(y_pct, 1),
                "no": round(n_pct, 1),
                "abstain": round(a_pct, 1)
            },
            "yes_no_total": yes_no_total,
            "has_majority": has_majority,
            "has_two_thirds": has_two_thirds,
            "passed": passed,
            "majority_threshold": threshold,
        }
        vote.state = Vote.CLOSED
        vote.save()
