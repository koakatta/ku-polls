import datetime

import django.test
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Question


class QuestionModelTests(TestCase):

    def test_was_published_recently_with_future_question(self):
        """
        was_published_recently() returns False for questions whose pub_date
        is in the future.
        """
        time = timezone.now() + datetime.timedelta(days=30)
        future_question = Question(pub_date=time)
        self.assertIs(future_question.was_published_recently(), False)

    def test_was_published_recently_with_old_question(self):
        """
        was_published_recently() returns False for questions whose pub_date
        is older than 1 day.
        """
        time = timezone.now() - datetime.timedelta(days=1, seconds=1)
        old_question = Question(pub_date=time)
        self.assertIs(old_question.was_published_recently(), False)

    def test_was_published_recently_with_recent_question(self):
        """
        was_published_recently() returns True for questions whose pub_date
        is within the last day.
        """
        time = timezone.now() - datetime.timedelta(hours=23, minutes=59, seconds=59)
        recent_question = Question(pub_date=time)
        self.assertIs(recent_question.was_published_recently(), True)


def create_question(question_text, days):
    """
    Create a question with the given `question_text` and published the
    given number of `days` offset to now (negative for questions published
    in the past, positive for questions that have yet to be published).
    """
    time = timezone.now() + datetime.timedelta(days=days)
    return Question.objects.create(question_text=question_text, pub_date=time)


class QuestionIndexViewTests(TestCase):
    def test_no_questions(self):
        """
        If no questions exist, an appropriate message is displayed.
        """
        response = self.client.get(reverse('polls:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No polls are available.")
        self.assertQuerysetEqual(response.context['latest_question_list'], [])

    def test_past_question(self):
        """
        Questions with a pub_date in the past are displayed on the
        index page.
        """
        question = create_question(question_text="Past question.", days=-30)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'],
            [question],
        )

    def test_future_question(self):
        """
        Questions with a pub_date in the future aren't displayed on
        the index page.
        """
        create_question(question_text="Future question.", days=30)
        response = self.client.get(reverse('polls:index'))
        self.assertContains(response, "No polls are available.")
        self.assertQuerysetEqual(response.context['latest_question_list'], [])

    def test_future_question_and_past_question(self):
        """
        Even if both past and future questions exist, only past questions
        are displayed.
        """
        question = create_question(question_text="Past question.", days=-30)
        create_question(question_text="Future question.", days=30)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'],
            [question],
        )

    def test_two_past_questions(self):
        """
        The questions index page may display multiple questions.
        """
        question1 = create_question(question_text="Past question 1.", days=-30)
        question2 = create_question(question_text="Past question 2.", days=-5)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'],
            [question2, question1],
        )


class QuestionDetailViewTests(TestCase):
    def test_future_question(self):
        """
        The detail view of a question with a pub_date in the future
        returns a 404 not found.
        """
        future_question = create_question(question_text='Future question.', days=5)
        url = reverse('polls:detail', args=(future_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_past_question(self):
        """
        The detail view of a question with a pub_date in the past
        displays the question's text.
        """
        past_question = create_question(question_text='Past Question.', days=-5)
        url = reverse('polls:detail', args=(past_question.id,))
        response = self.client.get(url)
        self.assertContains(response, past_question.question_text)


class VotingTest(TestCase):
    def test_voting_can_vote(self):
        """user time is after publish date and before end date so user can vote"""
        time = timezone.now() + datetime.timedelta(days=30)
        question = Question(pub_date=timezone.now() + datetime.timedelta(days=-30), end_date=time)
        self.assertTrue(question.can_vote())

    def test_voting_before_pub(self):
        """user time is before publish date so user cannot vote"""
        time = timezone.now() + datetime.timedelta(days=30)
        question = Question(pub_date=time)
        self.assertFalse(question.can_vote())
        question = Question(pub_date=time, end_date=timezone.now() + datetime.timedelta(days=-10))
        self.assertFalse(question.can_vote())
        question = Question(pub_date=time, end_date=timezone.now() + datetime.timedelta(days=10))
        self.assertFalse(question.can_vote())

    def test_voting_exact_time(self):
        """one test is with user time is exactly publish date
        and another test is with user time exactly end date so user can vote in both"""
        time = timezone.now()
        question = Question(pub_date=time, end_date=time + datetime.timedelta(hours=2))
        self.assertTrue(question.can_vote())
        question = Question(pub_date=time)
        self.assertTrue(question.can_vote())
        question = Question(pub_date=time + datetime.timedelta(days=-10), end_date=time)
        self.assertTrue(question.can_vote())

    def test_voting_after_end_date(self):
        """user time is after end date so user cannot vote"""
        time = timezone.now()
        question = Question(pub_date=time + datetime.timedelta(days=-20), end_date=time + datetime.timedelta(days=-10))
        self.assertFalse(question.can_vote())

    def test_voting_no_end_date(self):
        """voting in poll with no end date so user can vote"""
        time = timezone.now()
        question = Question(pub_date=time + datetime.timedelta(hours=-1))
        self.assertTrue(question.can_vote())


class UserAuthTest(django.test.TestCase):

    def setUp(self):
        # superclass setUp creates a Client object and initializes test database
        super().setUp()
        self.username = "testuser"
        self.password = "FatChance!"
        self.user1 = User.objects.create_user(
            username=self.username,
            password=self.password,
            email="testuser@nowhere.com"
        )
        self.user1.first_name = "Tester"
        self.user1.save()
        # we need a poll question to test voting
        # q = Question.create("First Poll Question")
        # q.save()
        # # a few choices
        # for n in range(1, 4):
        #     choice = Choice(choice_text=f"Choice {n}", question=q)
        #     choice.save()
        # self.question = q

    def test_logout(self):
        """a user can logout using the logout url.

        As an authenticated user,
        when I visit /accounts/logout/
        then I am logged out
        and then redirected to the login page.
        """
        logout_url = reverse("logout")
        # Authenticate the user.
        # We want to logout this user, so we need to associate the
        # user user with a session.  Setting client.user = ... doesn't work.
        # Use Client.login(username, password) to do that.
        # Client.login returns true on success
        self.assertTrue(
            self.client.login(username=self.username, password=self.password)
        )
        # visit the logout page
        response = self.client.get(logout_url)
        self.assertEqual(302, response.status_code)

        # should redirect us to where? Polls index? Login?
        self.assertRedirects(response, reverse('login'))

    def test_login_view(self):
        """a user can login using the login view."""
        login_url = reverse("login")
        # Can get the login page
        response = self.client.get(login_url)
        self.assertEqual(200, response.status_code)
        # Can login using a POST request
        # usage: client.post(url, {'key1":"value", "key2":"value"})
        form_data = {"username": "testuser",
                     "password": "FatChance!"
                     }
        response = self.client.post(login_url, form_data)
        self.assertEqual(302, response.status_code)
        # should redirect us to the polls index page ("polls:index")
        self.assertRedirects(response, reverse("polls:index"))

    # def test_auth_required_to_vote(self):
    #     """Authentication is required to submit a vote.
    #
    #     As an unauthenticated user,
    #     when I submit a vote for a question,
    #     then I am redirected to the login page
    #       or I receive a 403 response (FORBIDDEN)
    #     """
    #     vote_url = reverse('polls:vote', args=[self.question.id])
    #
    #     # what choice to vote for?
    #     choice = self.question.choice_set.first()
    #     # the polls detail page has a form, each choice is identified by its id
    #     form_data = {"choice": f"{choice.id}"}
    #     response = self.client.post(vote_url, form_data)
    #     # should be redirected to the login page
    #     self.assertEqual(response.status_code, 302)  # could be 303
    #     # the query parameter ?next=/polls/1/vote/
    #     # How to fix it?
    #     self.assertRedirects(response, reverse('login') )
    #     login_with_next = f"{reverse('login')}?next={vote_url}"
    #     self.assertRedirects(response, login_with_next)
