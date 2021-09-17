from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, redirect

from course.models import Course, CourseForm, DeleteCourseForm
from slide.models import Slide
from task.models import Task
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
    tasks = Task.objects.filter(course__code=course.code)
    slides = Slide.objects.filter(course__code=course.code)

    return render(request, 'course/course_page.html', {
        'course': course,
        'tasks': tasks,
        'slides': slides,
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
            return redirect('course:index')
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

    if request.method == 'POST':  # Form was submitted
        courseForm = CourseForm(request.POST)
        if courseForm.is_valid():

            course = courseForm.save(commit=False)
            # TODO: Calling .save() generates new DB entry? Options:
            #   - Check each field if altered
            #   - Find alternative solution --> see django's UpdateView?
            course.save()

            # Give a message back to the user
            messages.add_message(request, messages.SUCCESS, 'Course was altered!')
            print("Changed course")
            return redirect('course:index')

        else:
            # Render form with errors
            pass

    else:  # GET method
        # Check if course_id is valid (i.e. exists)
        if course_id in Course.objects.all().values_list('id', flat=True):
            course = Course.objects.all().get(id=course_id)
            courseForm = CourseForm(instance=course)

        else:
            # TODO: Decide on action. Let user create new course??
            courseForm = CourseForm()

    return render(request, 'course/edit.html', {'form': courseForm})


@teacher_required
def delete(request, course_id):
    """
    View to delete a course from the course database
    """

    if request.method == 'POST':  # Form was submitted

        form = DeleteCourseForm(request.POST)
        if form.is_valid():

            course = Course.objects.get(id=course_id)
            course_code = course.code
            course_title = course.title
            txt = f"{course_code} - {course_title}"

            if form.cleaned_data['confirmDelete'] is True:
                # TODO Add code to delete database entry

                messages.add_message(request, messages.SUCCESS, f'The course {txt} was deleted')
            else:
                messages.add_message(request, messages.SUCCESS, f'The course {txt} was not deleted')

            # Return to course index
            return redirect('course:index')


    else:  # GET method
        # Render page with course info and "Delete? Yes/No"
        if course_id in Course.objects.all().values_list('id', flat=True):
            course = Course.objects.all().get(id=course_id)
            return render(request, 'course/delete.html',
                          {'form': DeleteCourseForm(), 'course': course})

        else:
            messages.add_message(request, messages.WARNING, 'Did not find course')
            return redirect('course:index')

    return redirect('course:index')
