from django.contrib.auth.models import User
from django.test import TestCase, Client, TransactionTestCase
from django.urls import reverse
import json
from django.utils import timezone


from Meeting.models import *

# Create your tests here.


class BaseTestCase(TestCase):
    def setUp(self):
        super(BaseTestCase, self).setUp()
        self.client = Client()
        self.m = Meeting()
        self.m.save()
        self.old_ts = TokenSet(meeting=self.m)
        self.old_ts.save()
        self.ts = TokenSet(meeting=self.m)
        self.ts.save()
        self.admin = User()
        self.admin.is_superuser = True
        self.admin.save()


class ManagementInterfaceCases(BaseTestCase):
    def setUp(self):
        super(ManagementInterfaceCases, self).setUp()
        self.client.force_login(self.admin)
        pass

    def test_create_yna_vote(self):
        x = Vote.objects.count()
        result = self.client.post(reverse('meeting/new_vote', args=[self.m.id]), {'name': 'name',
                        'description':'description',
                        'method':Vote.YES_NO_ABS})
        self.assertEqual(x+1, Vote.objects.count())
        v = Vote.objects.first()
        self.assertEqual(v.name, 'name')
        self.assertEqual(v.description, 'description')
        self.assertEqual(v.method, Vote.YES_NO_ABS)
        self.assertEqual(v.state, Vote.READY)
        self.assertEqual(v.token_set, self.ts)
        self.assertListEqual(list(v.option_set.all().values_list('name', flat=True)), ['abs', 'no', 'yes'])

    def test_create_stv_vote(self):
        x = Vote.objects.count()
        result = self.client.post(reverse('meeting/new_vote', args=[self.m.id]), {'name': 'name',
                        'description':'description',
                        'method':Vote.STV})
        self.assertEqual(x+1, Vote.objects.count())
        v = Vote.objects.first()
        self.assertEqual(v.name, 'name')
        self.assertEqual(v.description, 'description')
        self.assertEqual(v.method, Vote.STV)
        self.assertEqual(v.state, Vote.READY)
        self.assertEqual(v.token_set, self.ts)
        # STV votes should auto-create "None of the above" option
        self.assertEqual(v.option_set.count(), 1)
        self.assertEqual(v.option_set.first().name, "None of the above")

    def test_add_vote_option_YNA(self):
        v = Vote(name='name', token_set=self.ts, method=Vote.YES_NO_ABS)
        v.save()
        request_args = [reverse('meeting/add_vote_option', args=[self.m.id, v.id]),
                        {'name': 'name'}]
        result = self.client.post(*request_args)
        self.assertJSONEqual(result.content, json.dumps({'result': 'failure'}))
        self.assertEqual(3, v.option_set.count())

    def test_add_vote_option_non_ready_state(self):
        cant_add_option_states = [x[0] for x in Vote.states]
        cant_add_option_states.remove(Vote.READY)
        for s in cant_add_option_states:
            v = Vote(name='name', token_set=self.ts, method=Vote.STV, state=s)
            v.save()
            request_args = [reverse('meeting/add_vote_option', args=[self.m.id, v.id]),
                            {'name': 'name'}]
            result = self.client.post(*request_args)
            self.assertJSONEqual(result.content, json.dumps({'result': 'failure'}))
            self.assertEqual(0, v.option_set.count())

    def test_add_vote_option_predicted_success(self):
        v = Vote(name='name', token_set=self.ts, method=Vote.STV)
        v.save()
        # v.option_set.count() is now 1 (None of the above)
        request_args = [reverse('meeting/add_vote_option', args=[self.m.id, v.id]),
                        {'name': 'name'}]
        result = self.client.post(*request_args)
        # Find the newly added option (not "None of the above")
        new_option = v.option_set.get(name='name')
        self.assertJSONEqual(result.content, json.dumps({'result': 'success',
                                                         'id': new_option.id}))
        self.assertEqual(2, v.option_set.count())

    def test_remove_vote_option_YNA(self):
        v = Vote(name='name', token_set=self.ts, method=Vote.YES_NO_ABS)
        v.save()
        request_args = [reverse('meeting/remove_vote_option', args=[self.m.id, v.id]),
                        {'id': v.id}]
        result = self.client.post(*request_args)
        self.assertJSONEqual(result.content, json.dumps({'result': 'failure'}))
        self.assertEqual(3, v.option_set.count())

    def test_remove_vote_option_non_ready_state(self):
        cant_add_option_states = [x[0] for x in Vote.states]
        cant_add_option_states.remove(Vote.READY)
        for s in cant_add_option_states:
            v = Vote(name='name', token_set=self.ts, method=Vote.STV, state=s)
            v.save()
            Option(name='name', vote=v).save()
            self.assertEqual(1, v.option_set.count())
            request_args = [reverse('meeting/remove_vote_option', args=[self.m.id, v.id]),
                            {'id': v.option_set.first().id}]
            result = self.client.post(*request_args)
            self.assertJSONEqual(result.content, json.dumps({'result': 'failure'}))
            self.assertEqual(1, v.option_set.count())

    def test_remove_vote_option_predicted_success(self):
        v = Vote(name='name', token_set=self.ts, method=Vote.STV)
        v.save()
        # v.option_set.count() is now 1 (None of the above)
        custom_option = Option(name='custom_name', vote=v)
        custom_option.save()
        self.assertEqual(2, v.option_set.count())
        request_args = [reverse('meeting/remove_vote_option', args=[self.m.id, v.id]),
                        {'id': custom_option.id}]
        result = self.client.post(*request_args)
        self.assertJSONEqual(result.content, json.dumps({'result': 'success'}))
        self.assertEqual(1, v.option_set.count())
        # Verify "None of the above" still exists
        self.assertEqual(v.option_set.first().name, "None of the above")

    def test_cannot_remove_none_of_the_above(self):
        """Test that 'None of the above' option cannot be removed."""
        v = Vote(name='name', token_set=self.ts, method=Vote.STV)
        v.save()
        # Get the "None of the above" option
        none_of_above = v.option_set.get(name="None of the above")
        self.assertEqual(1, v.option_set.count())

        request_args = [reverse('meeting/remove_vote_option', args=[self.m.id, v.id]),
                        {'id': none_of_above.id}]
        result = self.client.post(*request_args)
        self.assertJSONEqual(result.content, json.dumps({'result': 'failure',
                                                         'reason': 'cannot_remove_none_of_the_above'}))
        self.assertEqual(1, v.option_set.count())
        # Verify option still exists
        self.assertTrue(v.option_set.filter(name="None of the above").exists())

    def test_open_vote(self):
        v = Vote(name='name', token_set=self.ts, method=Vote.STV)
        v.save()
        request_url = reverse('meeting/open_vote', args=[self.m.id, v.id])
        for x in range(0, 2):
            result = self.client.get(request_url)
            v.refresh_from_db()
            self.assertJSONEqual(result.content, json.dumps({'reason': 'insufficient_options',
                                                             'result': 'failure',
                                                             'message': 'This ballot needs at least 2 candidates to open. Please add more candidates and try again.'}))
            self.assertEqual(v.state, v.READY)
            o = Option(name=str(x), vote=v)
            o.save()
        result = self.client.get(request_url)
        assert(result.status_code == 302)
        v.refresh_from_db()
        self.assertEqual(v.LIVE, v.state)

    def test_open_already_opened_vote(self):
        non_ready_states = list(map(lambda x: x[0], Vote.states))
        non_ready_states.remove(Vote.READY)
        for state in non_ready_states:
            v = Vote(name='name', token_set=self.ts, method=Vote.YES_NO_ABS, state=state)
            v.save()
            request_url = reverse('meeting/open_vote', args=[self.m.id, v.pk])
            result = self.client.get(request_url)
            self.assertJSONEqual(result.content, json.dumps({'result': 'failure'}))
            v.refresh_from_db()
            self.assertEqual(v.state, state)

    def test_close_vote(self):
        v = Vote(name='name', token_set=self.ts, method=Vote.YES_NO_ABS, majority_threshold='simple')
        v.save()
        self.assertEqual(3, v.option_set.count())
        non_live_states = [x[0] for x in Vote.states]
        non_live_states.remove(Vote.LIVE)
        request_args = [reverse('meeting/close_vote', args=[self.m.id, v.id]), {}]
        for s in non_live_states:
            v.state = s
            v.save()
            result = self.client.post(*request_args)
            self.assertJSONEqual(result.content, json.dumps({'result': 'failure'}))
            v.refresh_from_db()
            self.assertEqual(s, v.state)
        v.state = v.LIVE
        v.save()
        result = self.client.post(*request_args)
        v.refresh_from_db()
        # TODO(check broadcast to UI)
        self.assertIn(v.state, [v.COUNTING, v.NEEDS_TIE_BREAKER, v.CLOSED])

    def test_deactivating_tokens(self):
        active = AuthToken(token_set=self.ts, has_proxy=False)
        active.save()
        for x in [True, False]:
            t = AuthToken(token_set=self.ts, has_proxy=x)
            t.save()
            self.assertTrue(t.active)
            request_args = [reverse('meeting/deactivate_token', args=[self.m.id]),
                            {'key': t.id}]
            result = self.client.post(*request_args)
            self.assertJSONEqual(result.content, json.dumps({'result': 'success'}))
            t.refresh_from_db()
            self.assertFalse(t.active)
            active.refresh_from_db()
            self.assertTrue(active.active)

    def test_deactivating_tokens_non_existent_token(self):
        request_args = [reverse('meeting/deactivate_token', args=[self.m.id]),
                        {'key': 12345678}]
        result = self.client.post(*request_args)
        self.assertJSONEqual(result.content, json.dumps({'result': 'failure',
                                                         'reason': 'token doesnt exist'}))

    def test_deactivating_tokens_wrong_meeting(self):
        t = AuthToken(token_set=self.ts, has_proxy=False)
        t.save()
        other_m = Meeting(name="hi")
        other_m.save()
        self.assertTrue(t.active)
        request_args = [reverse('meeting/deactivate_token', args=[other_m.pk]),
                        {'key': t.id}]
        result = self.client.post(*request_args)
        t.refresh_from_db()
        self.assertTrue(t.active)
        self.assertJSONEqual(result.content, json.dumps({'result': 'failure',
                                                         'reason': 'token is for a different meeting'}))

    def test_announcement(self):
        request_args = [reverse('meeting/announcement', args=[self.m.pk]),
                        {'message': 'hello'}]
        result = self.client.post(*request_args)
        self.assertJSONEqual(result.content, json.dumps({'result': 'success'}))

    def test_announcement_closed_meeting(self):
        self.m.close_time = timezone.now()
        self.m.save()
        request_args = [reverse('meeting/announcement', args=[self.m.pk]),
                        {'message': 'hello'}]
        result = self.client.post(*request_args)
        self.assertJSONEqual(result.content, json.dumps({'result': 'failure', "error": "meeting closed"}))

    def test_open_meeting_list(self):
        request_args = [reverse('meeting/list')]
        result = self.client.get(*request_args)
        self.assertJSONEqual(result.content, json.dumps({'meetings': [{'id': self.m.pk,
                                                                      'name': self.m.name}]}))
        m2 = Meeting(name="meeting 2")
        m2.save()
        request_args = [reverse('meeting/list')]
        result = self.client.get(*request_args)
        self.assertJSONEqual(result.content, json.dumps({'meetings': [{'id': self.m.pk,
                                                                       'name': self.m.name},
                                                                      {'id': m2.pk,
                                                                       'name': m2.name}]}))
        m2.close_time = timezone.now()
        m2.save()
        request_args = [reverse('meeting/list')]
        result = self.client.get(*request_args)
        self.assertJSONEqual(result.content, json.dumps({'meetings': [{'id': self.m.pk,
                                                                       'name': self.m.name}]}))
        self.m.close_time = timezone.now()
        self.m.save()
        request_args = [reverse('meeting/list')]
        result = self.client.get(*request_args)
        self.assertJSONEqual(result.content, json.dumps({'meetings': []}))

    def test_get_ballot_candidates(self):
        """Test the new JSON endpoint for getting ballot candidates."""
        v = Vote(name='Test Ballot', token_set=self.ts, method=Vote.STV)
        v.save()
        # v should have "None of the above" auto-created
        Option(name='Candidate 1', vote=v).save()
        Option(name='Candidate 2', vote=v).save()

        request_url = reverse('meeting/get_ballot_candidates', args=[self.m.id, v.id])
        result = self.client.get(request_url)
        data = json.loads(result.content)

        self.assertEqual(data['ballot_id'], v.id)
        self.assertEqual(data['ballot_name'], 'Test Ballot')
        self.assertEqual(data['state'], Vote.READY)
        self.assertEqual(data['method'], Vote.STV)
        self.assertEqual(len(data['candidates']), 3)
        # Check that candidates include "None of the above"
        candidate_names = [c['name'] for c in data['candidates']]
        self.assertIn('None of the above', candidate_names)
        self.assertIn('Candidate 1', candidate_names)
        self.assertIn('Candidate 2', candidate_names)

    def test_meeting_management(self):
        request_args = [reverse('meeting/manage', args=[self.m.pk])]
        result = self.client.get(*request_args)
        self.assertEqual(200, result.status_code)
        for type in list(map(lambda x: x[0], Vote.methods)):
            for state in list(map(lambda x: x[0], Vote.states)):
                Vote(token_set=self.ts, method=type, state=state).save()
                request_args = [reverse('meeting/manage', args=[self.m.pk])]
                result = self.client.get(*request_args)
                self.assertEqual(200, result.status_code)

    def test_create_one_token(self):
        for proxy in [True, False]:
            request_args = [reverse('meeting/create_token', args=[self.m.pk]),
                            {'proxy': proxy.__str__().lower(), 'amount': '1'}]
            result = json.loads(self.client.post(*request_args).content)

            expected_dict = { "result": "success", "meeting_id": self.m.pk, "meeting_name": self.m.name, "proxy": proxy }

            self.assertEqual(result, expected_dict | result)

            token = AuthToken.objects.filter(pk=result['token']).first()
            self.assertEqual(self.ts, token.token_set)
            self.assertEqual(proxy, token.has_proxy)
            assert token.active

    def test_create_multiple_tokens(self):
        for proxy in [True, False]:
            request_args = [reverse('meeting/create_token', args=[self.m.pk]),
                            {'proxy': proxy.__str__().lower(), 'amount': '5'}]
            result = json.loads(self.client.post(*request_args).content)

            expected_dict = { "result": "success", "meeting_id": self.m.pk, "meeting_name": self.m.name, "proxy": proxy }

            self.assertEqual(result, expected_dict | result)

            tokens = AuthToken.objects.filter(pk__in=result['tokens'])
            self.assertEqual(5, tokens.count())

            for token in tokens:
                self.assertEqual(self.ts, token.token_set)
                self.assertEqual(proxy, token.has_proxy)
                assert token.active

    def test_close_meeting(self):
        v1 = self.ts.vote_set.create(method=Vote.YES_NO_ABS, state=Vote.LIVE, majority_threshold='simple')
        v2 = self.ts.vote_set.create(method=Vote.YES_NO_ABS, state=Vote.READY)
        before = timezone.now()
        out = self.client.post(reverse('meeting/close', args=[self.m.pk]))
        after = timezone.now()
        self.assertRedirects(out, reverse('meeting/report/meeting', args=[self.m.pk]))
        v1.refresh_from_db()
        self.assertFalse(Vote.objects.filter(pk=v2.pk).exists())
        self.assertEqual(v1.state, Vote.CLOSED)
        self.m.refresh_from_db()
        self.assertGreater(self.m.close_time, before)
        self.assertLess(self.m.close_time, after)
