import datetime

import django.contrib.auth.models
from django.contrib import admin
from django.db import models
from django.db.models import AutoField
from django.utils import timezone


class Question(models.Model):
    """Model of a Question object"""
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published')
    end_date = models.DateTimeField('ending date', null=True)

    def __str__(self):
        return self.question_text

    @admin.display(
        boolean=True,
        ordering='pub_date',
        description='Published recently?',
    )
    def was_published_recently(self):
        """check whether question was published not long ago"""
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.pub_date <= now

    def can_vote(self):
        """check end date and publish date with time now and return true if can still vote and return false if end
        date is passed or publish date not reached """
        now = timezone.now()
        if self.end_date is not None:
            if self.pub_date <= now:
                return now <= self.end_date
            else:
                return False
        else:
            if self.pub_date <= now:
                return True
            else:
                return False

    def is_published(self):
        """check question publish date is after time now or not"""
        return timezone.now() >= self.pub_date


class Choice(models.Model):
    """Choice for question model"""
    id = AutoField(primary_key=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)

    @property
    def votes(self):
        """count vote for this choice"""
        return len(Vote.objects.filter(choice_id=self.id))

    def __str__(self):
        return self.choice_text


class User(django.contrib.auth.models.User):
    """user model"""


class Vote(models.Model):
    user_id = models.IntegerField('user_id', default=0)
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE)

# def get_user(lazy):
#     return User.objects.get(id=lazy.id)
