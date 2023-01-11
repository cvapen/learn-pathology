import random
from copy import deepcopy

from django.contrib import messages
from django.db import transaction
from django.forms import formset_factory, inlineformset_factory, modelformset_factory
from django.shortcuts import render, redirect, HttpResponse, get_object_or_404
from django.utils.datastructures import MultiValueDictKeyError

from course.models import Course
from multiple_choice.models import MultipleChoice, Choice, RandomMCChoice
from multiple_choice.forms import MultipleChoiceForm, ChoiceForm, TaskForm
from slide.models import Slide, Pointer, AnnotatedSlide
from slide.views import slide_cache
from user.decorators import teacher_required
from task.models import Task
from multiple_choice.forms import TaskForm, MultipleChoiceForm, ChoiceForm


def do(request, task_id):
    """
    Student form for answering/viewing a multiple choice task
    """
    task = MultipleChoice.objects.get(task=task_id)

    answered = 'no'
    if request.method == 'POST':
        print('POST')
        # Process form
        print(request.POST['choice'])
        try:
            choice = Choice.objects.get(task=task, id=request.POST['choice'])
            if choice.correct:
                answered = 'correct'
            else:
                answered = 'incorrect'
        except Choice.DoesNotExist:
            raise ValueError

    slide_cache.load_slide_to_cache(task.task.annotated_slide.slide.id)
    return render(request, 'multiple_choice/do.html', {
        'task': task,
        'answered': answered,
    })


def do_random(request, slide_id=None):
    """
    Student form for answering/viewing a random multiple choice task
    """


    if request.method == 'GET':  # If the request is GET
        # make a random question
        slides = Slide.objects.all()
        num_images = len(slides)
        slide_id = random.randrange(1, num_images + 1)


    slide = Slide.objects.get(id=slide_id)
    slide_cache.load_slide_to_cache(slide_id)
    # Load all choices for this slide
    answers = RandomMCChoice.objects.filter(slide=slide_id)

    answered = 'no'
    if request.method == 'POST':
        print('POST')
        # Process form

        try:
            choice = RandomMCChoice.objects.get(slide=slide, id=request.POST['choice'])
            if choice.correct:
                answered = 'correct'
            else:
                answered = 'incorrect'
        except MultiValueDictKeyError:
            answered = 'no_choice'


    return render(request, 'multiple_choice/random_quest.html', {
        'answers': answers,
        'answered': answered,
        'slide': slide
    })


@teacher_required
def new(request, slide_id, course_id=None):
    """
    Teacher form for creating a multiple choice task
    """

    # Get slide
    slide = Slide.objects.get(pk=slide_id)
    slide_cache.load_slide_to_cache(slide.id)

    # Process forms
    ChoiceFormset = formset_factory(ChoiceForm, extra=5)
    if request.method == 'POST': # Form was submitted
        print("POST")
        task_form = TaskForm(request.POST)
        multiple_choice_form = MultipleChoiceForm(request.POST)
        choice_formset = ChoiceFormset(request.POST)

        with transaction.atomic():  # Make save operation atomic
            if multiple_choice_form.is_valid() and task_form.is_valid() and choice_formset.is_valid():
                # Create annotated slide
                annotated_slide = AnnotatedSlide()
                annotated_slide.slide = slide
                annotated_slide.save()

                # Create task
                task = task_form.save(commit=False)
                task.annotated_slide = annotated_slide
                task.save()

                organ_tags = task_form.cleaned_data['organ_tags']
                other_tags = [tag for tag in task_form.cleaned_data['other_tags']]
                task.tags.set([organ_tags] + other_tags)

                # Create multiple choice
                multiple_choice = multiple_choice_form.save(commit=False)
                multiple_choice.task = task
                multiple_choice.save()

                for choiceForm in choice_formset:
                    choice = choiceForm.save(commit=False)
                    if len(choice.text) > 0:
                        choice.task = multiple_choice
                        choice.save()

                # Store annotations (pointers)
                for key in request.POST:
                    print(key, request.POST[key])
                    if key.startswith('pointer-') and key.endswith('-text'):
                        prefix = key[:-len('text')]
                        pointer = Pointer()
                        pointer.text = request.POST[key]
                        pointer.position_x = float(request.POST[prefix+'x'])
                        pointer.position_y = float(request.POST[prefix+'y'])
                        pointer.annotated_slide = annotated_slide
                        pointer.save()

                # Give a message back to the user
                messages.add_message(request, messages.SUCCESS, 'Task added successfully!')
                if course_id is not None and course_id in Course.objects.values_list('id', flat=True):
                    course = Course.objects.get(id=course_id)
                    course.task.add(task)
                    return redirect('course:view', course_id=course_id)
                return redirect('task_list')
    else:
        task_form = TaskForm()
        multiple_choice_form = MultipleChoiceForm()
        choice_formset = ChoiceFormset()


    return render(request, 'multiple_choice/new.html', {
        'slide': slide,
        'multipleChoiceForm': multiple_choice_form,
        'taskForm': task_form,
        'choiceFormset': choice_formset,
    })




    # Process forms
    ChoiceFormset = formset_factory(ChoiceForm, extra=5)
    if request.method == 'POST': # Form was submitted
        print("POST")
        task_form = TaskForm(request.POST)
        multiple_choice_form = MultipleChoiceForm(request.POST)
        choice_formset = ChoiceFormset(request.POST)

        with transaction.atomic():  # Make save operation atomic
            if multiple_choice_form.is_valid() and task_form.is_valid() and choice_formset.is_valid():
                # Create annotated slide
                annotated_slide = AnnotatedSlide()
                annotated_slide.slide = slide
                annotated_slide.save()

                # Create task
                task = task_form.save(commit=False)
                task.annotated_slide = annotated_slide
                task.save()

                organ_tags = task_form.cleaned_data['organ_tags']
                other_tags = [tag for tag in task_form.cleaned_data['other_tags']]
                task.tags.set([organ_tags] + other_tags)

                # Create multiple choice
                multiple_choice = multiple_choice_form.save(commit=False)
                multiple_choice.task = task
                multiple_choice.save()

                for choiceForm in choice_formset:
                    choice = choiceForm.save(commit=False)
                    if len(choice.text) > 0:
                        choice.task = multiple_choice
                        choice.save()

                # Store annotations (pointers)
                for key in request.POST:
                    print(key, request.POST[key])
                    if key.startswith('pointer-') and key.endswith('-text'):
                        prefix = key[:-len('text')]
                        pointer = Pointer()
                        pointer.text = request.POST[key]
                        pointer.position_x = float(request.POST[prefix+'x'])
                        pointer.position_y = float(request.POST[prefix+'y'])
                        pointer.annotated_slide = annotated_slide
                        pointer.save()

                # Give a message back to the user
                messages.add_message(request, messages.SUCCESS, 'Task added successfully!')
                if course_id is not None and course_id in Course.objects.values_list('id', flat=True):
                    course = Course.objects.get(id=course_id)
                    course.task.add(task)
                    return redirect('course:view', course_id=course_id)
                return redirect('task_list')
    else:
        task_form = TaskForm()
        multiple_choice_form = MultipleChoiceForm()
        choice_formset = ChoiceFormset()

    return render(request, 'multiple_choice/new.html', {
        'slide': slide,
        'multipleChoiceForm': multiple_choice_form,
        'taskForm': task_form,
        'choiceFormset': choice_formset,
    })

def new_random(num_choices = 5):
    """
    Teacher form for creating a multiple choice task


    Should return:
    - task
    - slide_id

    """

    # Get slide
    slides = Slide.objects.all()
    for i in range(len(slides)):
        new_choices= []


        slide = Slide.objects.get(pk=i+1)

        # Add correct answer
        choice = RandomMCChoice()
        choice.slide = slide
        choice.text = slide.description
        choice.correct = True
        new_choices.append(choice)


        slides_exclude = slides.exclude(id=i)
        excluded_list = []
        for slide_ex in slides_exclude.iterator():
            excluded_list.append(slide_ex.description)
        answers = random.sample(excluded_list, k=4)

        for answer in answers:
            choice = RandomMCChoice()
            choice.slide = slide
            choice.text = answer
            choice.correct = False
            new_choices.append(choice)

        random.seed()
        random.shuffle(new_choices)
        for choice in new_choices:
            choice.save()




    """
    # From Ingrid:
    slide_names = [name for name in Slide.objects.values_list('name', flat=True)]
    
    
    for each slide id:
    
        slide = Slide.get....

        # Add correct answer
        choice = RandomMCChoice()
        choice.slide = slide
        choice.text = slide.description
        choice.correct = True
        choice.save()
    
        # Add remaining options at random
        for i in range(num_choices - 1):
            choice = RandomMCChoice()
            choice.multiple_choice = multiple_choice
    
            random_idx = random.choice(range(len(slide_names)))
            choice.text = slide_names[random_idx]
            slide_names.pop(random_idx)
            choices.append(choice)

    """

    pass


@teacher_required
def edit(request, task_id):
    """
    Teacher form for editing a multiple choice task
    """

    ChoiceFormset = modelformset_factory(Choice, form=ChoiceForm, extra=5)

    # Get model instances from database
    task = get_object_or_404(Task, id=task_id)
    multiple_choice = get_object_or_404(MultipleChoice, task=task)
    choices = Choice.objects.filter(task=multiple_choice)

    # Get slide and pointers
    annotated_slide = task.annotated_slide
    slide = annotated_slide.slide
    slide_cache.load_slide_to_cache(slide.id)

    # Process forms
    if request.method == 'POST': # Form was submitted

        # Get submitted forms
        task_form = TaskForm(request.POST or None, instance=task)
        multiple_choice_form = MultipleChoiceForm(request.POST or None, instance=multiple_choice)
        choice_formset = ChoiceFormset(request.POST)

        #pointers = Pointer.objects.filter(annotated_slide=task.annotated_slide)

        with transaction.atomic():  # Make save operation atomic
            if task_form.is_valid() and multiple_choice_form.is_valid() and choice_formset.is_valid():

                # Save instance data to database
                task = task_form.save()

                organ_tags = task_form.cleaned_data['organ_tags']
                other_tags = [tag for tag in task_form.cleaned_data['other_tags']]
                task.tags.set([organ_tags] + other_tags)

                multiple_choice = multiple_choice_form.save()

                for choiceForm in choice_formset:
                    choice = choiceForm.save(commit=False)
                    if len(choice.text) > 0:
                        choice.task = multiple_choice
                        choice.save()

                # Store annotations (pointers)
                # Delete old pointers first
                Pointer.objects.filter(annotated_slide=annotated_slide).delete()
                # Add all current pointers
                for key in request.POST:
                    print(key, request.POST[key])
                    if key.startswith('pointer-') and key.endswith('-text'):
                        prefix = key[:-len('text')]
                        pointer = Pointer()
                        pointer.text = request.POST[key]
                        pointer.position_x = float(request.POST[prefix + 'x'])
                        pointer.position_y = float(request.POST[prefix + 'y'])
                        pointer.annotated_slide = annotated_slide
                        pointer.save()

                messages.add_message(request, messages.SUCCESS,
                     f'The task {task.name} was altered!')

        return redirect('task_list')

    else:  # GET
        task_form = TaskForm(instance=task)#, initial=task.tags.all())
        task_form.fields['organ_tags'].initial = task.tags.filter(is_organ=True)
        task_form.fields['other_tags'].initial = task.tags.filter(is_stain=False, is_organ=False)

        multiple_choice_form = MultipleChoiceForm(instance=task.multiplechoice)
        choice_formset = ChoiceFormset(queryset=choices)

    context = {
        'slide': slide,
        'annotated_slide': annotated_slide,
        'taskForm': task_form,
        'multipleChoiceForm': multiple_choice_form,
        'choiceFormset': choice_formset,
        'pointers': Pointer.objects.filter(annotated_slide=annotated_slide),
    }
    return render(request, 'multiple_choice/edit.html', context)
