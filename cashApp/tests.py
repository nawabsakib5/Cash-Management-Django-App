# cashApp/tests.py
"""
Step 2 - authentication hardening tests.

Run with:   python manage.py test cashApp -v 2
"""
from unittest.mock import AsyncMock, patch

from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from cashApp.consumers import DashboardConsumer
from cashApp.models import AuditLog
from cashApp.security import get_client_ip

User = get_user_model()
GOOD_PASSWORD = 'Tr1cky-Horse-Battery-77'


class AuthTestBase(TestCase):
    def setUp(self):
        cache.clear()   # lockout / rate-limit counters must not leak between tests
        self.alice = User.objects.create_user(
            username='alice', email='alice@example.com', password=GOOD_PASSWORD
        )

    def post_login(self, identifier='alice', password=GOOD_PASSWORD, **extra):
        return self.client.post(reverse('login'), {'username': identifier, 'password': password}, **extra)


class LoginTests(AuthTestBase):
    def test_login_with_username_and_with_email(self):
        self.assertRedirects(self.post_login('alice'), reverse('project_list'), fetch_redirect_response=False)
        self.client.logout()
        self.assertRedirects(self.post_login('ALICE@example.com'), reverse('project_list'), fetch_redirect_response=False)

    def test_wrong_password_and_unknown_user_get_the_same_message(self):
        r1 = self.post_login('alice', 'wrong-password')
        r2 = self.post_login('nobody-here', 'wrong-password')
        self.assertContains(r1, 'Invalid username/email or password')
        self.assertContains(r2, 'Invalid username/email or password')

    def test_password_is_not_stripped(self):
        User.objects.create_user(username='bob', email='bob@example.com', password=' spaced-Pass-1234 ')
        self.assertContains(self.post_login('bob', 'spaced-Pass-1234'), 'Invalid username/email or password')
        self.assertEqual(self.post_login('bob', ' spaced-Pass-1234 ').status_code, 302)

    def test_lockout_after_five_failures_even_for_correct_password(self):
        for _ in range(5):
            self.post_login('alice', 'wrong-password')
        locked = self.post_login('alice', GOOD_PASSWORD)           # correct password, still refused
        self.assertEqual(locked.status_code, 429)
        self.assertContains(locked, 'Too many failed attempts', status_code=429)

    def test_lockout_is_per_account_and_ip(self):
        for _ in range(5):
            self.post_login('alice', 'wrong-password')
        # a different account from the same IP is still allowed to try
        self.assertContains(self.post_login('someone-else', 'x'), 'Invalid username/email or password')
        # the same account from another IP is not locked
        other_ip = self.post_login('alice', GOOD_PASSWORD, REMOTE_ADDR='10.9.8.7')
        self.assertEqual(other_ip.status_code, 302)

    def test_nonexistent_user_locks_like_a_real_one(self):
        for _ in range(5):
            self.post_login('ghost', 'x')
        self.assertEqual(self.post_login('ghost', 'x').status_code, 429)

    def test_successful_login_resets_failure_counter(self):
        for _ in range(4):
            self.post_login('alice', 'wrong-password')
        self.assertEqual(self.post_login('alice', GOOD_PASSWORD).status_code, 302)
        self.client.logout()
        for _ in range(4):
            self.assertEqual(self.post_login('alice', 'wrong-password').status_code, 200)

    def test_frozen_account_message_only_after_correct_password(self):
        User.objects.filter(pk=self.alice.pk).update(is_frozen=True)
        self.assertContains(self.post_login('alice', GOOD_PASSWORD), 'frozen')
        wrong = self.post_login('alice', 'wrong-password')           # must NOT reveal it is frozen
        self.assertContains(wrong, 'Invalid username/email or password')
        self.assertNotContains(wrong, 'frozen')

    def test_next_redirect_only_to_same_site(self):
        url = reverse('login') + '?next=' + reverse('change_password')
        self.assertRedirects(self.client.post(url, {'username': 'alice', 'password': GOOD_PASSWORD}),
                             reverse('change_password'), fetch_redirect_response=False)
        self.client.logout()
        evil = reverse('login') + '?next=https://evil.example.com/'
        resp = self.client.post(evil, {'username': 'alice', 'password': GOOD_PASSWORD})
        self.assertRedirects(resp, reverse('project_list'), fetch_redirect_response=False)

    def test_spoofed_forwarded_header_cannot_break_or_poison_audit_log(self):
        resp = self.post_login(HTTP_X_FORWARDED_FOR="not-an-ip'; DROP TABLE x;--")
        self.assertEqual(resp.status_code, 302)
        entry = AuditLog.objects.filter(action='login').latest('timestamp')
        self.assertEqual(entry.ip_address, '127.0.0.1')


class LogoutTests(AuthTestBase):
    def test_get_does_not_log_out_but_post_does(self):
        self.client.force_login(self.alice)
        self.client.get(reverse('logout'))
        self.assertEqual(self.client.get(reverse('project_list')).status_code, 200)   # still signed in
        self.client.post(reverse('logout'))
        self.assertEqual(self.client.get(reverse('project_list')).status_code, 302)    # signed out

    def test_logout_form_in_page_has_csrf_token(self):
        self.client.force_login(self.alice)
        html = self.client.get(reverse('project_list')).content.decode()
        self.assertIn('action="%s"' % reverse('logout'), html)
        self.assertIn('csrfmiddlewaretoken', html)


class SignupTests(AuthTestBase):
    def signup(self, **over):
        data = {'username': 'newuser', 'full_name': 'New User', 'phone': '', 'email': 'new@example.com',
                'password': GOOD_PASSWORD, 'confirm_password': GOOD_PASSWORD}
        data.update(over)
        return self.client.post(reverse('signup'), data)

    def test_valid_signup(self):
        self.assertRedirects(self.signup(), reverse('project_list'), fetch_redirect_response=False)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_weak_passwords_rejected(self):
        self.assertContains(self.signup(password='1', confirm_password='1'), 'too short')
        self.assertContains(self.signup(password='password123', confirm_password='password123'), 'too common')
        self.assertContains(self.signup(password='12345678901', confirm_password='12345678901'), 'entirely numeric')
        self.assertFalse(User.objects.filter(username='newuser').exists())

    def test_at_sign_not_allowed_in_username(self):
        self.assertContains(self.signup(username='alice@example.com'), 'cannot contain')

    def test_duplicates_are_case_insensitive(self):
        self.assertContains(self.signup(username='ALICE'), 'username already exists')
        self.assertContains(self.signup(email='ALICE@example.com'), 'email already exists')

    def test_invalid_email_rejected(self):
        self.assertContains(self.signup(email='not-an-email'), 'valid e-mail')

    @override_settings(SIGNUP_MAX_PER_HOUR=2)
    def test_signup_is_rate_limited(self):
        self.signup(username='u1', email='u1@example.com')
        self.client.logout()
        self.signup(username='u2', email='u2@example.com')
        self.client.logout()
        self.assertEqual(self.signup(username='u3', email='u3@example.com').status_code, 429)


class ChangePasswordTests(AuthTestBase):
    def change(self, old=GOOD_PASSWORD, new='Another-Strong-Pass-55', con=None):
        return self.client.post(reverse('change_password'),
                                {'old_pass': old, 'new_pass': new, 'con_pass': con or new})

    def setUp(self):
        super().setUp()
        self.client.force_login(self.alice)

    def test_weak_new_password_rejected(self):
        self.assertContains(self.change(new='123'), 'too short')
        self.assertContains(self.change(new='password123'), 'too common')

    def test_must_differ_from_current(self):
        self.assertContains(self.change(new=GOOD_PASSWORD), 'different')

    def test_success_keeps_session_and_changes_password(self):
        self.assertRedirects(self.change(), reverse('project_list'), fetch_redirect_response=False)
        self.alice.refresh_from_db()
        self.assertTrue(self.alice.check_password('Another-Strong-Pass-55'))
        self.assertEqual(self.client.get(reverse('project_list')).status_code, 200)   # still logged in
        self.assertTrue(AuditLog.objects.filter(action='edit', detail='Password changed').exists())

    def test_wrong_current_password_is_rate_limited(self):
        for _ in range(10):
            self.change(old='wrong')
        self.assertEqual(self.change(old='wrong').status_code, 429)


class FrozenMiddlewareTests(AuthTestBase):
    def test_freezing_a_signed_in_user_logs_them_out_on_next_request(self):
        self.client.force_login(self.alice)
        self.assertEqual(self.client.get(reverse('project_list')).status_code, 200)
        User.objects.filter(pk=self.alice.pk).update(is_frozen=True)
        resp = self.client.get(reverse('project_list'))
        self.assertRedirects(resp, reverse('login'), fetch_redirect_response=False)
        # the session is really gone, not just redirected once
        User.objects.filter(pk=self.alice.pk).update(is_frozen=False)
        self.assertEqual(self.client.get(reverse('project_list')).status_code, 302)


class ClientIpTests(SimpleTestCase):
    def request(self, **meta):
        return RequestFactory().get('/', **meta)

    @override_settings(TRUSTED_PROXY_COUNT=0)
    def test_forwarded_header_ignored_without_trusted_proxy(self):
        self.assertEqual(get_client_ip(self.request(REMOTE_ADDR='9.9.9.9', HTTP_X_FORWARDED_FOR='6.6.6.6')), '9.9.9.9')

    @override_settings(TRUSTED_PROXY_COUNT=1)
    def test_only_proxy_appended_entry_is_trusted(self):
        req = self.request(REMOTE_ADDR='10.0.0.1', HTTP_X_FORWARDED_FOR='6.6.6.6, 203.0.113.7')
        self.assertEqual(get_client_ip(req), '203.0.113.7')

    def test_garbage_returns_none(self):
        self.assertIsNone(get_client_ip(self.request(REMOTE_ADDR='garbage')))


class DashboardSocketTests(SimpleTestCase):
    """The consumer must refuse anonymous and frozen users (get_stats is mocked: no DB)."""

    async def connect_as(self, user):
        comm = WebsocketCommunicator(DashboardConsumer.as_asgi(), '/ws/dashboard/')
        comm.scope['user'] = user
        with patch.object(DashboardConsumer, 'get_stats', new=AsyncMock(return_value={'ok': 1})):
            connected, _ = await comm.connect()
            payload = await comm.receive_json_from() if connected else None
            await comm.disconnect()
        return connected, payload

    async def test_anonymous_is_rejected(self):
        connected, _ = await self.connect_as(AnonymousUser())
        self.assertFalse(connected)

    async def test_frozen_user_is_rejected(self):
        connected, _ = await self.connect_as(User(username='f', is_frozen=True))
        self.assertFalse(connected)

    async def test_normal_user_is_accepted(self):
        connected, payload = await self.connect_as(User(username='ok', is_frozen=False))
        self.assertTrue(connected)
        self.assertEqual(payload, {'ok': 1})