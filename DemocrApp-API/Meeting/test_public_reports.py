from django.test import TestCase, Client
from django.urls import reverse

from Meeting.models import Meeting, TokenSet, Vote, Option, VoterToken, BallotEntry, AuthToken


class PublicReportTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.client = Client()
        self.meeting = Meeting.objects.create(name="Test Meeting")
        self.token_set = TokenSet.objects.create(meeting=self.meeting)
        self.auth_token = AuthToken.objects.create(token_set=self.token_set)
        self.voter_token = VoterToken.objects.filter(auth_token=self.auth_token).first()


class PublicVoteReportTests(PublicReportTestCase):
    def test_public_vote_report_accessible_by_uuid(self):
        """Test that closed votes can be accessed via public_id"""
        vote = Vote.objects.create(
            token_set=self.token_set,
            name="Test Vote",
            method=Vote.YES_NO_ABS,
            state=Vote.CLOSED,
            majority_threshold='simple'
        )

        response = self.client.get(reverse('meeting/public_vote_report', args=[vote.public_id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Vote")

    def test_public_vote_report_not_accessible_for_non_closed(self):
        """Test that non-closed votes return 404"""
        vote = Vote.objects.create(
            token_set=self.token_set,
            name="Live Vote",
            method=Vote.YES_NO_ABS,
            state=Vote.LIVE,
            majority_threshold='simple'
        )

        response = self.client.get(reverse('meeting/public_vote_report', args=[vote.public_id]))
        self.assertEqual(response.status_code, 404)

    def test_public_vote_report_shows_anonymized_ballots(self):
        """Test that ballots show as 'Ballot 1', 'Ballot 2' without voter names"""
        vote = Vote.objects.create(
            token_set=self.token_set,
            name="YNA Vote",
            method=Vote.YES_NO_ABS,
            state=Vote.CLOSED,
            majority_threshold='simple'
        )
        yes_option = vote.option_set.get(name='yes')
        no_option = vote.option_set.get(name='no')

        # Create some ballots
        BallotEntry.objects.create(token=self.voter_token, option=yes_option, value=1)

        response = self.client.get(reverse('meeting/public_vote_report', args=[vote.public_id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ballot 1")
        # Verify ballots are anonymized (no voter token IDs in ballot display)
        self.assertNotContains(response, f"Token {self.voter_token.pk}")


class PublicMeetingReportTests(PublicReportTestCase):
    def test_public_meeting_report_accessible(self):
        """Test that meeting reports are accessible"""
        response = self.client.get(reverse('meeting/public_meeting_report', args=[self.token_set.public_id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Meeting")

    def test_hidden_votes_not_in_public_meeting_report(self):
        """Test that votes with hide_from_public_report=True don't appear"""
        vote1 = Vote.objects.create(
            token_set=self.token_set,
            name="Visible Vote",
            method=Vote.YES_NO_ABS,
            state=Vote.CLOSED,
            majority_threshold='simple',
            hide_from_public_report=False
        )
        vote2 = Vote.objects.create(
            token_set=self.token_set,
            name="Hidden Vote",
            method=Vote.YES_NO_ABS,
            state=Vote.CLOSED,
            majority_threshold='simple',
            hide_from_public_report=True
        )

        response = self.client.get(reverse('meeting/public_meeting_report', args=[self.token_set.public_id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Visible Vote")
        self.assertNotContains(response, "Hidden Vote")

    def test_meeting_summary_shows_yna_pass_fail(self):
        """Test that YNA votes show pass/fail in summary"""
        vote = Vote.objects.create(
            token_set=self.token_set,
            name="YNA Vote",
            method=Vote.YES_NO_ABS,
            state=Vote.CLOSED,
            majority_threshold='simple'
        )
        # Set up results_data with passed status
        vote.results_data = {
            'yes': 7,
            'no': 3,
            'abstain': 0,
            'percentages': {'yes': 70.0, 'no': 30.0, 'abstain': 0.0},
            'passed': True
        }
        vote.save()

        response = self.client.get(reverse('meeting/public_meeting_report', args=[self.token_set.public_id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "PASSED")
        self.assertContains(response, "70%")

    def test_meeting_summary_shows_stv_winners(self):
        """Test that STV votes show winners in summary"""
        vote = Vote.objects.create(
            token_set=self.token_set,
            name="Board Election",
            method=Vote.STV,
            state=Vote.CLOSED,
            num_seats=3
        )
        # Set up results_data with winners
        vote.results_data = {
            'winners': [
                {'name': 'Alice', 'order': 1},
                {'name': 'Bob', 'order': 2},
                {'name': 'Carol', 'order': 3}
            ],
            'seats': 3
        }
        vote.save()

        response = self.client.get(reverse('meeting/public_meeting_report', args=[self.token_set.public_id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alice, Bob, Carol (3)")

    def test_public_meeting_report_not_accessible_by_integer_id(self):
        """Test that integer IDs don't work - only UUIDs"""
        # Try to access via integer ID (should 404 after URL pattern change)
        response = self.client.get(f'/api/public/meeting/{self.token_set.id}/')
        self.assertEqual(response.status_code, 404)


class VoteFieldTests(PublicReportTestCase):
    def test_yna_vote_requires_majority_threshold_to_close(self):
        """Test that YNA votes require majority_threshold before closing"""
        vote = Vote.objects.create(
            token_set=self.token_set,
            name="YNA Vote",
            method=Vote.YES_NO_ABS,
            state=Vote.LIVE
            # No majority_threshold set
        )

        with self.assertRaises(ValueError) as context:
            vote.close()
        self.assertIn("majority_threshold", str(context.exception))

    def test_stv_vote_requires_num_seats_to_close(self):
        """Test that STV votes require num_seats before closing"""
        vote = Vote.objects.create(
            token_set=self.token_set,
            name="STV Vote",
            method=Vote.STV,
            state=Vote.LIVE
            # No num_seats set
        )

        with self.assertRaises(ValueError) as context:
            vote.close()
        self.assertIn("num_seats", str(context.exception))

    def test_yna_vote_closes_with_threshold_set(self):
        """Test that YNA votes close successfully when threshold is set"""
        vote = Vote.objects.create(
            token_set=self.token_set,
            name="YNA Vote",
            method=Vote.YES_NO_ABS,
            state=Vote.LIVE,
            majority_threshold='simple'
        )

        # Should not raise an exception
        vote.close()
        vote.refresh_from_db()
        self.assertEqual(vote.state, Vote.CLOSED)

    def test_stv_vote_closes_with_num_seats_set(self):
        """Test that STV votes close successfully when num_seats is set"""
        vote = Vote.objects.create(
            token_set=self.token_set,
            name="STV Vote",
            method=Vote.STV,
            state=Vote.LIVE,
            num_seats=3
        )

        # Should not raise an exception
        vote.close()
        vote.refresh_from_db()
        # STV counting runs in background thread, so state is COUNTING
        self.assertEqual(vote.state, Vote.COUNTING)


class YNAPassFailTests(PublicReportTestCase):
    def test_yna_vote_passed_simple_majority(self):
        """Test that vote passes with simple majority (6 yes, 4 no = 60%)"""
        vote = Vote.objects.create(
            token_set=self.token_set,
            name="YNA Vote",
            method=Vote.YES_NO_ABS,
            state=Vote.LIVE,
            majority_threshold='simple'
        )

        yes_option = vote.option_set.get(name='yes')
        no_option = vote.option_set.get(name='no')

        # Create 6 yes votes and 4 no votes
        for i in range(6):
            auth = AuthToken.objects.create(token_set=self.token_set)
            voter = VoterToken.objects.filter(auth_token=auth).first()
            BallotEntry.objects.create(token=voter, option=yes_option, value=1)

        for i in range(4):
            auth = AuthToken.objects.create(token_set=self.token_set)
            voter = VoterToken.objects.filter(auth_token=auth).first()
            BallotEntry.objects.create(token=voter, option=no_option, value=1)

        vote.close()
        vote.refresh_from_db()

        self.assertTrue(vote.results_data['passed'])
        self.assertTrue(vote.results_data['has_majority'])

    def test_yna_vote_failed_two_thirds_majority(self):
        """Test that vote fails with 2/3 threshold (6 yes, 4 no = 60% < 66.7%)"""
        vote = Vote.objects.create(
            token_set=self.token_set,
            name="YNA Vote",
            method=Vote.YES_NO_ABS,
            state=Vote.LIVE,
            majority_threshold='two_thirds'
        )

        yes_option = vote.option_set.get(name='yes')
        no_option = vote.option_set.get(name='no')

        # Create 6 yes votes and 4 no votes (60%, not enough for 2/3)
        for i in range(6):
            auth = AuthToken.objects.create(token_set=self.token_set)
            voter = VoterToken.objects.filter(auth_token=auth).first()
            BallotEntry.objects.create(token=voter, option=yes_option, value=1)

        for i in range(4):
            auth = AuthToken.objects.create(token_set=self.token_set)
            voter = VoterToken.objects.filter(auth_token=auth).first()
            BallotEntry.objects.create(token=voter, option=no_option, value=1)

        vote.close()
        vote.refresh_from_db()

        self.assertFalse(vote.results_data['passed'])
        self.assertFalse(vote.results_data['has_two_thirds'])
