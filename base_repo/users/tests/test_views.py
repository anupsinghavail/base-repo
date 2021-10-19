import pytest
import unittest
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpRequest
from django.test import RequestFactory
from django.urls import reverse

from base_repo.users.forms import UserChangeForm
from base_repo.users.models import User
from base_repo.users.tests.factories import UserFactory
from base_repo.users.views import (
    UserRedirectView,
    UserUpdateView,
    user_detail_view,
)

pytestmark = pytest.mark.django_db


class TestUserUpdateView(unittest.TestCase):
    """
    TODO:
        extracting view initialization code as class-scoped fixture
        would be great if only pytest-django supported non-function-scoped
        fixture db access -- this is a work-in-progress for now:
        https://github.com/pytest-dev/pytest-django/pull/258
    """

    def setUp(self):
        self.user = UserFactory()
        self.rf = RequestFactory()
        return super().setUp()

    def dummy_get_response(self, request: HttpRequest):
        return None

    def test_get_success_url(self):
        view = UserUpdateView()
        request = self.rf.get("/fake-url/")
        request.user = self.user

        view.request = request
        assert view.get_success_url() == f"/users/{self.user.username}/"

    def test_get_object(self):
        view = UserUpdateView()
        request = self.rf.get("/fake-url/")
        request.user = self.user

        view.request = request

        assert view.get_object() == self.user

    def test_form_valid(self):
        view = UserUpdateView()
        request = self.rf.get("/fake-url/")

        # Add the session/message middleware to the request
        SessionMiddleware(self.dummy_get_response).process_request(request)
        MessageMiddleware(self.dummy_get_response).process_request(request)
        request.user = self.user

        view.request = request

        # Initialize the form
        form = UserChangeForm()
        form.cleaned_data = []
        view.form_valid(form)

        messages_sent = [m.message for m in messages.get_messages(request)]
        assert messages_sent == ["Information successfully updated"]


class TestUserRedirectView(unittest.TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.rf = RequestFactory()
        return super().setUp()

    def test_get_redirect_url(self):
        view = UserRedirectView()
        request = self.rf.get("/fake-url")
        request.user = self.user

        view.request = request

        assert view.get_redirect_url() == f"/users/{self.user.username}/"


class TestUserDetailView(unittest.TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.rf = RequestFactory()
        return super().setUp()

    def test_authenticated(self):
        request = self.rf.get("/fake-url/")
        request.user = self.user

        response = user_detail_view(request, username=self.user.username)

        assert response.status_code == 200

    def test_not_authenticated(self):
        user = AnonymousUser()
        request = self.rf.get("/fake-url/")
        request.user = user

        response = user_detail_view(request, username=user.username)
        login_url = reverse(settings.LOGIN_URL)

        assert response.status_code == 302
        assert response.url == f"{login_url}?next=/fake-url/"
