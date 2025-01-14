from django.db import models
from slide.models import Slide, AnnotatedSlide
from task.models import Task


class MultipleChoice(models.Model):
    """
    A multiple choice exercise task
    """
    task = models.OneToOneField(Task, on_delete=models.CASCADE)
    question = models.CharField(max_length=2048)
    instructions = models.CharField(max_length=2048, default='Choose the correct answer(s)')


class Choice(models.Model):
    """
    A choice in a multiple choice task
    """
    task = models.ForeignKey(MultipleChoice, on_delete=models.CASCADE)
    text = models.CharField(max_length=512)
    correct = models.BooleanField()


class RandomMCChoice(models.Model):
    """
    A choice in a RandomMultipleChoice task
    """
    slide = models.ForeignKey(Slide, on_delete=models.CASCADE)
    text = models.CharField(max_length=512)
    correct = models.BooleanField()


