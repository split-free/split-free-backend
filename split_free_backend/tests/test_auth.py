# Copyright (c) 2023 SplitFree Org.

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from split_free_backend.core.helpers import get_auth_headers
from split_free_backend.core.models import User


class UserTests(APITestCase):
    def test_create_user(self):
        """
        Ensure we can create a new user.
        """
        url = reverse("user-list")
        data = {"email": "test_user@hotmail.com", "password": "test_password"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().email, "test_user@hotmail.com")
        user = User.objects.get()
        self.assertTrue(user.check_password("test_password"))
        self.assertTrue("id" in response.data)

    def test_create_user_without_password(self):
        """
        Ensure we can't create a new user without a password.
        """
        url = reverse("user-list")
        data = {
            "email": "test_user@hotmail.com",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(response.data, {"password": ["This field is required."]})

    def test_create_user_without_email(self):
        """
        Ensure we can't create a new user without an email.
        """
        url = reverse("user-list")
        data = {
            "password": "test_password",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(response.data, {"email": ["This field is required."]})

    def test_create_user_with_existing_email(self):
        """
        Ensure we can't create a new user with an existing email.
        """
        url = reverse("user-list")
        data = {"email": "test_user@hotmail.com", "password": "test_password"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(response.data, {"email": ["A user with this email already exists."]})

    def test_create_user_with_invalid_email(self):
        """
        Ensure we can't create a new user with an invalid email.
        """
        url = reverse("user-list")
        data = {"email": "test_user", "password": "test_password"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(response.data, {"email": ["Enter a valid email address."]})

    def test_create_user_with_short_password(self):
        """
        Ensure we can't create a new user with a short password.
        """
        url = reverse("user-list")
        data = {"email": "test_user@hotmail.com", "password": "test"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(
            response.data,
            {"password": ["This password is too short. It must contain at least 8 characters."]},
        )


class AuthTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test_user@hotmail.com",
            password="test_password",
            is_active=True,
        )

    def test_login(self):
        """
        Ensure we can login a user.
        """
        url = reverse("token_obtain_pair")
        data = {"email": "test_user@hotmail.com", "password": "test_password"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue("access" in response.data)
        self.assertTrue("refresh" in response.data)

    def test_login_with_invalid_email(self):
        """
        Ensure we can't login a user with an invalid email.
        """
        url = reverse("token_obtain_pair")
        data = {"email": "test_user_wrong@hotmail.com", "password": "test_password"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data,
            {"detail": "No active account found with the given credentials"},
        )

    def test_login_with_invalid_password(self):
        """
        Ensure we can't login a user with an invalid password.
        """
        url = reverse("token_obtain_pair")
        data = {"email": "test_user@hotmail.com", "password": "test_password_wrong"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data,
            {"detail": "No active account found with the given credentials"},
        )

    def test_refresh_token(self):
        """
        Ensure we can refresh a token.
        """
        url = reverse("token_obtain_pair")
        data = {"email": "test_user@hotmail.com", "password": "test_password"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        refresh_token = response.data["refresh"]
        url = reverse("token_refresh")
        data = {"refresh": refresh_token}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue("access" in response.data)
        self.assertTrue("refresh" in response.data)

    def test_refresh_token_with_invalid_token(self):
        """
        Ensure we can't refresh a token with an invalid token.
        """
        url = reverse("token_refresh")
        data = {"refresh": "invalid_token"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["detail"], "Token is invalid or expired")

    def test_logout(self):
        """
        Ensure we can logout a user.
        """
        url = reverse("token_obtain_pair")
        data = {"email": "test_user@hotmail.com", "password": "test_password"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        refresh_token = response.data["refresh"]
        url = reverse("logout")
        data = {"refresh": refresh_token}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"detail": "Token is blacklisted"})

    def test_logout_with_invalid_token(self):
        """
        Ensure we can't logout a user with an invalid token.
        """
        url = reverse("logout")
        data = {"refresh": "invalid_token"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"detail": "Token is invalid or expired"})

    def test_logout_with_expired_token(self):
        """
        Ensure we can't logout a user with an expired token.
        """
        url = reverse("token_obtain_pair")
        data = {"email": "test_user@hotmail.com", "password": "test_password"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        refresh_token = response.data["refresh"]
        url = reverse("token_refresh")
        data = {"refresh": refresh_token}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        refresh_token = response.data["refresh"]
        url = reverse("logout")
        data = {"refresh": refresh_token}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"detail": "Token is blacklisted"})
        url = reverse("logout")
        data = {"refresh": refresh_token}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"detail": "Token is invalid or expired"})

    def test_logout_with_blacklisted_token(self):
        """
        Ensure we can't logout a user with a blacklisted token.
        """
        url = reverse("token_obtain_pair")
        data = {"email": "test_user@hotmail.com", "password": "test_password"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        refresh_token = response.data["refresh"]
        url = reverse("logout")
        data = {"refresh": refresh_token}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"detail": "Token is blacklisted"})
        url = reverse("logout")
        data = {"refresh": refresh_token}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"detail": "Token is invalid or expired"})

    def test_signup(self):
        """
        Ensure we can sign up a user.
        """
        url = reverse("user-list")
        data = {"email": "test_user2@hotmail.com", "password": "test_password"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue("id" in response.data)

    def test_user_info(self):
        """
        Ensure we can get user name and id
        """
        url = reverse("token_obtain_pair")
        data = {"email": "test_user@hotmail.com", "password": "test_password"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        access_token = response.data["access"]
        response = self.client.get(
            "/api/user_info/",
            format="json",
            headers=get_auth_headers(access_token),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue("id" in response.data)
        self.assertTrue("name" in response.data)


class EmailActivationTests(APITestCase):
    def test_valid_activation_token(self):
        # Test case for a valid activation token
        User.objects.create(email="test@example.com", activation_token="valid_token")
        response = self.client.get(reverse("email-activate", kwargs={"token": "valid_token"}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "User activated successfully")

    def test_invalid_activation_token(self):
        # Test case for an invalid activation token
        response = self.client.get(reverse("email-activate", kwargs={"token": "invalid_token"}))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Invalid activation token")

    def test_user_signup_results_in_inactive_account(self):
        url = reverse("user-list")
        data = {"email": "test_user2@hotmail.com", "password": "test_password"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().is_active, False)

        activation_token = User.objects.get().activation_token

        response = self.client.get(reverse("email-activate", kwargs={"token": str(activation_token)}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "User activated successfully")
        self.assertEqual(User.objects.get().is_active, True)
