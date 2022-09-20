from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views import generic

import polls
from .models import Question, Choice, Vote


class IndexView(generic.ListView):
    template_name = 'polls/index.html'
    context_object_name = 'latest_question_list'

    def get_queryset(self):
        """Return the last five published questions."""
        return Question.objects.filter(
            pub_date__lte=timezone.now()
        ).order_by('-pub_date')[:5]


class DetailView(LoginRequiredMixin, generic.DetailView):
    model = Question
    template_name = 'polls/detail.html'

    def get_queryset(self):
        """
        Excludes any questions that aren't published yet.
        """
        return Question.objects.filter(pub_date__lte=timezone.now())


class ResultsView(generic.DetailView):
    model = Question
    template_name = 'polls/results.html'


@login_required
def vote(request, question_id):
    """get choice by POST and add 1 score to choice"""
    question = get_object_or_404(Question, pk=question_id)
    user = request.user
    q_set = question.choice_set.all()
    if not user.is_authenticated:
        return redirect('login')
    try:
        selected_choice = question.choice_set.get(pk=request.POST['choice'])
    except (KeyError, Choice.DoesNotExist):
        return render(request, 'polls/detail.html', {'question': question,
                                                     'error_message': "You didn't select a choice.", })
    else:
        vote_ticket = Vote(choice=selected_choice, user_id=user.id)
        try:
            vote_get = Vote.objects.get(choice=selected_choice, user_id=user.id)
        except (polls.models.Vote.DoesNotExist):
            vote_ticket.save()
        else:
            if vote_ticket.user_id == user.id and vote_ticket.choice_id == selected_choice.id:
                return render(request, 'polls/detail.html', {'question': question,
                                                             'error_message': "You voted same choice", })
            else:
                for i in q_set:
                    for j in Vote.objects.filter(user_id=user.id):
                        if i.id == Vote.objects.get(choice_id=i.id, user_id=user.id):
                            print('hit')
                            Vote.objects.get(choice_id=j.choice_id, user_id=user.id).delete()
                        else:
                            print('not hit')
                vote_ticket.save()
    return HttpResponseRedirect(reverse('polls:results', args=(question.id,)))


def detail_access(request, pk):
    """check question can still vote or not then return the page or redirect back with error message"""
    question = get_object_or_404(Question, pk=pk)
    user = request.user
    if question.can_vote():
        return render(request, 'polls/detail.html', {'question': question, 'user': user, 'vote': Vote})
    else:
        messages.error(request, "Not available for voting")
        return HttpResponseRedirect(reverse("polls:index"))
