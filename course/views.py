import json
import os
import sys

from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.uploadedfile import UploadedFile

from course.models import Course, CourseMaterial
from course.forms import CourseForm, DeleteCourseForm, \
    CourseLongDescriptionForm, CourseLearningOutcomesForm, CourseMaterialForm
from learnpathology.settings import MEDIA_ROOT
from slide.models import Slide
from tag.models import Tag
from task.models import Task
from multiple_choice.views import new as new_mc
from user.decorators import teacher_required


def index(request):
    """
    Show index of available courses
    """

    courses = Course.objects.all()
    return render(request, "course/index.html",
                  {'courses': Course.objects.all().order_by('code')})


def course_page(request, course_id):
    """
    Display a course page with course information and related slides and tasks
    """

    course = Course.objects.get(id=course_id)
    tasks = Task.objects.filter(course=course)
    slides = Slide.objects.filter(course=course)
    course_materials = CourseMaterial.objects.filter(course=course)

    return render(request, 'course/course_page.html', {
        'course': course,
        'tasks': tasks,
        'slides': slides,
        'course_materials': course_materials,
    })


@teacher_required
def new(request):
    """
    Teacher form for creating a course
    """

    if request.method == 'POST':  # Form was submitted
        courseForm = CourseForm(request.POST)
        if courseForm.is_valid():
            course = courseForm.save(commit=False)
            course.save()
            # Give a message back to the user
            messages.add_message(request, messages.SUCCESS, 'Course added successfully!')
            return redirect('course:view', course_id=course.id)
        else:
            # Render form with errors
            pass
    else:
        courseForm = CourseForm()

    return render(request, 'course/new.html', {'form': courseForm})


@teacher_required
def edit(request, course_id):
    """
    Teacher form for editing a course
    """

    course = get_object_or_404(Course, id=course_id)
    courseForm = CourseForm(request.POST or None, instance=course)

    if request.method == 'POST':  # Form was submitted
        if courseForm.is_valid():
            courseForm.save()
            messages.add_message(request, messages.SUCCESS,
                 f'The course {course.code} - {course.title} was altered!')
            return redirect('course:view', course_id=course_id)

    return render(request, 'course/edit.html', {'form': courseForm})


@teacher_required
def edit_long_description(request, course_id):
    """
    Teacher form for editing the course (long) description
    """

    course = get_object_or_404(Course, id=course_id)
    form = CourseLongDescriptionForm(request.POST or None, instance=course)

    if request.method == 'POST':  # Form was submitted
        if form.is_valid():
            form.save()
            messages.add_message(request, messages.SUCCESS,
                 f'The course {course.code} - {course.title} was altered!')
            return redirect('course:view', course_id=course_id)

    return render(request, 'course/edit_course_description.html', {
        'course': course,
        'form': form
    })


@teacher_required
def edit_learning_outcomes(request, course_id):
    """
    Teacher form for editing the course learning outcomes
    """

    course = get_object_or_404(Course, id=course_id)
    form = CourseLearningOutcomesForm(request.POST or None, instance=course)

    if request.method == 'POST':  # Form was submitted
        if form.is_valid():
            form.save()
            messages.add_message(request, messages.SUCCESS,
                 f'The course {course.code} - {course.title} was altered!')
            return redirect('course:view', course_id=course_id)

    return render(request, 'course/edit_learning_outcomes.html', {
        'course': course,
        'form': form
    })


@teacher_required
def delete(request, course_id):
    """
    View to delete a course from the course database
    """

    if request.method == 'POST':  # Form was submitted
        form = DeleteCourseForm(request.POST)

        if form.is_valid():
            course = Course.objects.get(id=course_id)
            txt = f"{course.code} - {course.title}"

            if form.cleaned_data['confirmDelete']:
                course.delete()
                messages.add_message(request, messages.SUCCESS, f'The course {txt} was deleted')
            else:
                messages.add_message(request, messages.SUCCESS, f'The course {txt} was not deleted')

            return redirect('course:index')

    else:  # GET method
        # Render page with course info and "Delete? Yes/No"
        if course_id in Course.objects.all().values_list('id', flat=True):
            course = Course.objects.get(id=course_id)
            return render(request, 'course/delete.html',
                          {'form': DeleteCourseForm(), 'course': course})

        else:  # In case user enters invalid URL directly
            messages.add_message(request, messages.WARNING, 'Did not find course')
            return redirect('course:index')

    return redirect('course:index')


@teacher_required
def new_task_and_add_to_course(request, course_id, slide_id):
    # Call/render new task template from here for user to fill in
    http_response = new_mc(request, slide_id=slide_id, course_id=course_id)
    return http_response


@teacher_required
def slide_selection(request, course_id):
    """
    Teacher form for adding slide(s) to a course
    """

    course = get_object_or_404(Course, id=course_id)
    slidesInCourse = [slide for slide in course.slide.all()]

    # Filter slides by tags
    filteredSlides = Slide.objects.all()
    organs = request.GET.getlist('organ[]')
    if len(organs) > 0:
        filteredSlides = filteredSlides.filter(tags__in=organs)
    stains = request.GET.getlist('stain[]')
    if len(stains) > 0:
        filteredSlides = filteredSlides.filter(tags__in=stains)
    tags = request.GET.getlist('tag[]')
    if len(tags) > 0:
        filteredSlides = filteredSlides.filter(tags__in=tags)

    # Get list of the filtered slides that are NOT in course
    slidesXor = []
    for slide in filteredSlides:
        if slide not in slidesInCourse:
            slidesXor.append(slide)
    filteredSlides = slidesXor

    context = {
        'course': course,
        'slides_in_course': slidesInCourse,
        'filtered_slides': filteredSlides,
        'organ_tags': Tag.objects.filter(is_organ=True),
        'stain_tags': Tag.objects.filter(is_stain=True),
        'other_tags': Tag.objects.filter(is_stain=False, is_organ=False),
        'selected_organ_tags': organs,
        'selected_stain_tags': stains,
        'selected_other_tags': tags,
    }

    return render(request, 'course/slide_selection.html', context)


@teacher_required
def task_selection(request, course_id):
    """
    Teacher form for adding task(s) to a course
    """

    course = get_object_or_404(Course, id=course_id)
    tasksInCourse = [task for task in course.task.all()]

    # Filter slides by tags
    filteredTasks = Task.objects.all()
    organs = request.GET.getlist('organ[]')
    if len(organs) > 0:
        filteredTasks = filteredTasks.filter(tags__in=organs)
    stains = request.GET.getlist('stain[]')
    if len(stains) > 0:
        filteredTasks = filteredTasks.filter(tags__in=stains)
    tags = request.GET.getlist('tag[]')
    if len(tags) > 0:
        filteredTasks = filteredTasks.filter(tags__in=tags)

    # Get list of the tasks that are NOT in course
    tasksXor = []
    for task in filteredTasks:
        if task not in tasksInCourse:
            tasksXor.append(task)
    filteredTasks = tasksXor

    context = {
        'course': course,
        'tasks_in_course': tasksInCourse,
        'filtered_tasks': filteredTasks,
        'organ_tags': Tag.objects.filter(is_organ=True),
        'stain_tags': Tag.objects.filter(is_stain=True),
        'other_tags': Tag.objects.filter(is_stain=False, is_organ=False),
        'selected_organ_tags': organs,
        'selected_stain_tags': stains,
        'selected_other_tags': tags,
    }

    return render(request, 'course/task_selection.html', context)


@teacher_required
def add_to_course(request):
    """
    View to handle button for adding an item to a course
    """

    course_id = int(request.GET.get('course_id'))
    course = Course.objects.get(id=course_id)
    model_name = request.GET.get('model_name')
    instance_id = int(request.GET.get('instance_id'))

    if request.method == 'GET':

        model = getattr(sys.modules[__name__], model_name)
        item_to_add = model.objects.get(id=instance_id)

        # Have defined explicitly for each model to avoid name mismatch in course.<attribute>
        if model == Slide:
            course.slide.add(item_to_add)
        elif model == Task:
            course.task.add(item_to_add)

        course.save()

    return JsonResponse(data={})


@teacher_required
def remove_from_course(request):
    """
    View to handle button for removing an item from a course
    """

    course_id = int(request.GET.get('course_id'))
    course = Course.objects.get(id=course_id)
    model_name = request.GET.get('model_name')
    instance_id = int(request.GET.get('instance_id'))

    if request.method == 'GET':

        model = getattr(sys.modules[__name__], model_name)
        item_to_add = model.objects.get(id=instance_id)

        # Have defined explicitly for each model to avoid name mismatch in course.<attribute>
        if model == Slide:
            course.slide.remove(item_to_add)
        elif model == Task:
            course.task.remove(item_to_add)

        course.save()

    return JsonResponse(data={})


@teacher_required
def upload_material(request, course_id):
    if request.method == 'POST':
        form = CourseMaterialForm(request.POST, request.FILES)
        with transaction.atomic():
            if form.is_valid():
                # Store file
                file_path = store_file_in_db(f=form.files['file'])
                # Save form
                course_material = form.save(file_path=file_path, commit=False)
                course_material.course = Course.objects.get(id=course_id)
                course_material.save()

                messages.add_message(request, messages.SUCCESS, 'Course material added to database')
                return redirect('course:view', course_id=course_id)
    else:
        form = CourseMaterialForm()

    return render(request, 'course/upload_material.html', {
        'form': form
    })


def store_file_in_db(f: UploadedFile):
    upload_path = MEDIA_ROOT.joinpath('course_material')
    if not os.path.exists(upload_path):
        os.makedirs(upload_path)

    destination_path = os.path.join(upload_path, f.name)
    # TODO: Ask the user if to substitute or keep both files
    if os.path.exists(destination_path):
        os.remove(destination_path)

    with open(destination_path, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)

    return destination_path
