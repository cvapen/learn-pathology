from django.contrib import messages
from django.shortcuts import render, redirect
from task.models import Task
from tag.models import Tag


def list(request):
    """
    Show list of tasks
    """

    tasks = Task.objects.all()

    # Filters
    organs = request.GET.getlist('organ[]')
    if len(organs) > 0:
        tasks = tasks.filter(tags__in=organs)
    systems = request.GET.getlist('system[]')
    if len(systems) > 0:
        tasks = tasks.filter(tags__in=systems)
    tags = request.GET.getlist('tag[]')
    if len(tags) > 0:
        tasks = tasks.filter(tags__in=systems)

    selected_pathology = request.GET.get('pathology', False)
    selected_histology = request.GET.get('histology', False)
    if not selected_pathology and not selected_histology:
        selected_pathology = True
        selected_histology = True
    if selected_pathology and not selected_histology:
        tasks = tasks.filter(pathology=True)
    elif not selected_pathology and selected_histology:
        tasks = tasks.filter(pathology=False)

    return render(request, "task/list.html", {
        'tasks': tasks.order_by('-id'),
        'organ_tags': Tag.objects.filter(is_organ=True),
        'system_tags': Tag.objects.filter(is_system=True),
        'other_tags': Tag.objects.filter(is_system=False, is_organ=False),
        'selected_organ_tags': organs,
        'selected_system_tags': systems,
        'selected_other_tags': tags,
        'selected_pathology': selected_pathology,
        'selected_histology': selected_histology,
    })


def delete(request, task_id):
    task = Task.objects.get(pk=task_id)
    task.type_model.delete()
    task.delete()
    messages.add_message(request, messages.SUCCESS, 'Task deleted.')
    return redirect(list)
