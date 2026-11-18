from django.conf import settings
from django.contrib.auth import SESSION_KEY, get_user_model
from django.test import Client, TestCase
from django.urls import reverse


class SuperuserLoginTests(TestCase):
    password = "  Test-password-2026!  "

    @classmethod
    def setUpTestData(cls):
        users = get_user_model().objects
        cls.superuser = users.create_superuser("superuser@example.com", cls.password)
        cls.staff = users.create_user("staff@example.com", cls.password, is_staff=True)
        cls.member = users.create_user("member@example.com", cls.password)
        cls.inactive = users.create_superuser(
            "inactive@example.com", cls.password, is_active=False
        )

    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.login_url = reverse("accounts:login")

    def post_login(self, email, password):
        csrf_token = self.client.get(self.login_url).json()["csrf_token"]
        return self.client.post(
            self.login_url,
            data={"email": email, "password": password},
            content_type="application/json",
            headers={"X-CSRFToken": csrf_token},
        )

    def test_active_superuser_can_log_in_with_email(self):
        response = self.post_login("superuser@EXAMPLE.COM", self.password)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["user"],
            {"id": self.superuser.pk, "email": self.superuser.email},
        )
        self.assertEqual(self.client.session[SESSION_KEY], str(self.superuser.pk))
        self.assertEqual(self.client.get(reverse("admin:index")).status_code, 200)

    def test_invalid_credentials_share_the_same_error(self):
        rejected = [
            (self.member.email, self.password),
            (self.staff.email, self.password),
            (self.inactive.email, self.password),
            (self.superuser.email, "wrong-password"),
            ("unknown@example.com", self.password),
        ]
        for email, password in rejected:
            with self.subTest(email=email):
                response = self.post_login(email, password)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(
                    response.json(), {"non_field_errors": ["E-posta veya parola geçersiz."]}
                )
                self.assertNotIn(SESSION_KEY, self.client.session)

    def test_login_requires_csrf_even_without_a_session(self):
        response = self.client.post(
            self.login_url,
            data={"email": self.superuser.email, "password": self.password},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_session_can_be_restored_from_a_persistent_cookie(self):
        response = self.post_login(self.superuser.email, self.password)
        self.assertEqual(response.status_code, 200)
        cookie = response.cookies[settings.SESSION_COOKIE_NAME]
        self.assertTrue(cookie["httponly"])
        self.assertGreater(int(cookie["max-age"]), 0)

        reopened = Client()
        self.assertIsNone(reopened.get(self.login_url).json()["user"])
        reopened.cookies[settings.SESSION_COOKIE_NAME] = cookie.value
        self.assertEqual(reopened.get(self.login_url).json()["user"], response.json()["user"])

    def test_logout_requires_csrf_and_ends_the_session(self):
        response = self.post_login(self.superuser.email, self.password)
        logout_url = reverse("accounts:logout")
        self.assertEqual(self.client.post(logout_url).status_code, 403)
        self.assertIn(SESSION_KEY, self.client.session)

        response = self.client.post(
            logout_url, headers={"X-CSRFToken": response.json()["csrf_token"]}
        )
        self.assertEqual(response.status_code, 204)
        self.assertIsNone(self.client.get(self.login_url).json()["user"])

    def test_admin_login_also_rejects_staff_without_superuser_role(self):
        admin_login = reverse("admin:login")
        page = self.client.get(admin_login)
        response = self.client.post(
            admin_login,
            data={
                "username": self.staff.email,
                "password": self.password,
                "csrfmiddlewaretoken": page.context["csrf_token"],
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_revoking_superuser_role_blocks_existing_session(self):
        self.assertEqual(self.post_login(self.superuser.email, self.password).status_code, 200)
        get_user_model().objects.filter(pk=self.superuser.pk).update(is_superuser=False)

        self.assertRedirects(
            self.client.get(reverse("admin:index")),
            f'{reverse("admin:login")}?next={reverse("admin:index")}',
        )
