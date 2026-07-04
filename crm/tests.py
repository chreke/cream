from django.contrib.auth import get_user_model
from django.test import TestCase


class UserModelTests(TestCase):
    def test_custom_user_model_is_active(self):
        self.assertEqual(get_user_model()._meta.label, "crm.User")

    def test_create_user_with_username_email_password(self):
        user = get_user_model().objects.create_user(
            username="anna", email="anna@example.com", password="hemligt123"
        )
        self.assertEqual(user.username, "anna")
        self.assertEqual(user.email, "anna@example.com")
        self.assertTrue(user.check_password("hemligt123"))
        self.assertNotEqual(user.password, "hemligt123")
