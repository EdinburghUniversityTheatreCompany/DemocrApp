"Plugin module for generating a human-readable HTML report."

## Copyright (C) 2003-2010 Jeffrey O'Neill
## Modified for improved legibility with candidate names and clear sections.
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.

from openstv.plugins import ReportPlugin


class HtmlReport(ReportPlugin):
    "Return a human-readable HTML report with candidate names and clear formatting."

    status = 1
    reportName = "HTML"

    def __init__(self, e, outputFile=None, test=False):
        ReportPlugin.__init__(self, e, outputFile, test)
        if self.e.methodName == "Condorcet":
            raise RuntimeError("HTML report not available for Condorcet elections.")

    def _get_candidate_name(self, index):
        """Get candidate name from index."""
        return self.cleanB.names[index]

    def _get_ordered_candidates(self):
        """
        Return candidates ordered for display:
        - Winners first (leftmost)
        - Then losers ordered by elimination round descending
          (last eliminated first, first eliminated rightmost)
        """
        winners = sorted(list(self.e.winners))
        losers = sorted(list(self.e.losers))

        # Sort losers by elimination round descending (last eliminated first)
        losers_with_round = [(c, self.e.lostAtRound[c]) for c in losers]
        losers_with_round.sort(key=lambda x: x[1], reverse=True)
        sorted_losers = [c for c, _ in losers_with_round]

        return winners + sorted_losers

    def _get_action_for_round(self, round_num):
        """Determine what action happened during/after this round."""
        actions = []

        # Check who was elected this round
        elected = [c for c in range(self.cleanB.numCandidates)
                   if self.e.wonAtRound[c] == round_num]
        if elected:
            names = [self._get_candidate_name(c) for c in elected]
            if len(names) == 1:
                actions.append('%s elected' % names[0])
            else:
                actions.append('%s elected' % ', '.join(names))

        # Check what happens next round (elimination or surplus transfer)
        if round_num < self.e.numRounds - 1:
            next_action = self.e.roundInfo[round_num + 1]["action"]
            if next_action[0] == "eliminate":
                eliminated = next_action[1]
                names = [self._get_candidate_name(c) for c in eliminated]
                if len(names) == 1:
                    actions.append('%s eliminated' % names[0])
                else:
                    actions.append('%s eliminated' % ', '.join(names))
            elif next_action[0] == "surplus":
                surplus_from = next_action[1]
                names = [self._get_candidate_name(c) for c in surplus_from]
                if len(names) == 1:
                    actions.append('Surplus from %s' % names[0])
                else:
                    actions.append('Surplus from %s' % ', '.join(names))

        if not actions:
            return ''
        return '; '.join(actions)

    def generateHeader(self):
        """Generate Winners and Eliminated sections with candidate names."""
        winners = sorted(list(self.e.winners))
        losers = sorted(list(self.e.losers))

        out = self.output

        # CSS styles
        out("""\
<style>
.stv-results { font-family: system-ui, sans-serif; }
.stv-results h3 { margin-top: 1em; margin-bottom: 0.5em; }
.stv-results ul { margin: 0; padding-left: 1.5em; }
.stv-results .winners-list li { font-weight: bold; }
.stv-table { border-collapse: collapse; margin-top: 0.5em; }
.stv-table th, .stv-table td { border: 1px solid #ccc; padding: 4px 8px; text-align: right; }
.stv-table th { background-color: #f5f5f5; text-align: center; }
.stv-table td:first-child { text-align: center; }
.stv-table td:last-child { text-align: left; }
.stv-table .eliminated-cell { color: #999; text-align: center; }
</style>
""")

        out('<div class="stv-results">\n')

        # Winners section
        out('<h3>Winners</h3>\n<ul class="winners-list">\n')
        for i, w in enumerate(winners, start=1):
            round_num = self.e.wonAtRound[w] + 1  # Convert from 0-indexed to 1-indexed
            out('  <li>%d. %s (round %d)</li>\n' % (i, self._get_candidate_name(w), round_num))
        out('</ul>\n')

        # Eliminated section
        if losers:
            out('<h3>Eliminated</h3>\n<ul class="eliminated-list">\n')
            # Sort by elimination round
            losers_with_round = [(l, self.e.lostAtRound[l]) for l in losers]
            losers_with_round.sort(key=lambda x: x[1])
            for l, round_num in losers_with_round:
                out('  <li>%s (Round %d)</li>\n' % (self._get_candidate_name(l), round_num + 1))
            out('</ul>\n')

    def generateReportNonIterative(self):
        """Generate report for non-iterative methods."""
        self.generateHeader()
        out = self.output

        out('<h3>Results</h3>\n')
        out('<table class="stv-table">\n')
        out('<tr><th>Candidate</th><th>Votes</th></tr>\n')

        for c in range(self.cleanB.numCandidates):
            name = self._get_candidate_name(c)
            votes = self.e.displayValue(self.e.count[c])
            out('<tr><td>%s</td><td>%s</td></tr>\n' % (name, votes))

        out('</table>\n</div>\n')

    def generateReportIterative(self):
        """Generate HTML table with round-by-round breakdown."""
        self.generateHeader()
        out = self.output

        ordered_candidates = self._get_ordered_candidates()

        out('<h3>Round Breakdown</h3>\n')
        out('<table class="stv-table">\n')

        # Header row
        out('<tr><th>Round</th>')
        for c in ordered_candidates:
            out('<th>%s</th>' % self._get_candidate_name(c))
        out('<th>Exhausted</th><th>Action</th></tr>\n')

        # Data rows for each round
        for r in range(self.e.numRounds):
            roundStage = r
            if self.e.methodName == "ERS97 STV":
                roundStage = self.e.roundToStage(r)

            out('<tr>')
            out('<td>%d</td>' % (roundStage + 1))

            # Vote counts for each candidate in display order
            for c in ordered_candidates:
                numVotes = self.e.count[r][c]
                # If candidate has lost and has no votes, show dash
                if c in self.e.losers and self.e.lostAtRound[c] <= r and numVotes == 0:
                    out('<td class="eliminated-cell">&mdash;</td>')
                else:
                    out('<td>%s</td>' % self.e.displayValue(numVotes))

            # Exhausted ballots
            out('<td>%s</td>' % self.e.displayValue(self.e.exhausted[r]))

            # Action column
            action = self._get_action_for_round(r)
            out('<td>%s</td>' % action)
            out('</tr>\n')

        out('</table>\n</div>\n')
