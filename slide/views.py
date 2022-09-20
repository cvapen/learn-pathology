import os.path

import django.urls
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile

from tag.models import Tag
from user.decorators import student_required, teacher_required
from .models import Slide
from .forms import SlideForm


class SlideCache:
    """
    A class to keep a cache of slides in memory.
    """

    def __init__(self):
        # TODO load FAST once
        import fast
        test = fast.WholeSlideImageImporter.New() # Just to initialize FAST..
        self.slides = {}

    def load_slide_to_cache(self, slide_id):
        slide = Slide.objects.get(pk=slide_id)
        slide.load_image() # This will load slide with FAST, so it is ready to use
        self.slides[slide_id] = slide
        return slide

    def get_slide(self, slide_id):
        return self.slides[slide_id]


# Initialize global slide cache as a global variable. This should only happen once..
slide_cache = SlideCache()


def index(request):
    slides = Slide.objects.all()

    # Filters
    organs = request.GET.getlist('organ[]')
    if len(organs) > 0: slides = slides.filter(tags__in=organs)
    stains = request.GET.getlist('stain[]')
    if len(stains) > 0: slides = slides.filter(tags__in=stains)
    tags = request.GET.getlist('tag[]')
    if len(tags) > 0: slides = slides.filter(tags__in=tags)
    selected_pathology = request.GET.get('pathology', False)
    selected_histology = request.GET.get('histology', False)
    if not selected_pathology and not selected_histology:
        selected_pathology = True
        selected_histology = True
    if selected_pathology and not selected_histology:
        slides = slides.filter(pathology=True)
    elif not selected_pathology and selected_histology:
        slides = slides.filter(pathology=False)

    # Handle search and search results
    if request.GET.get('submit_button') == 'Clear search':
        search_query = None
        search_result = None
    else:
        search_query = request.GET.get('search')
        if search_query is not None and len(search_query) > 0:
            filter_result = Slide.objects.filter(
                Q(name__contains=search_query) | Q(description__contains=search_query)
            )
            search_result = filter_result
        else:
            search_query = None
            search_result = None

    return render(request, 'slide/index.html', {
        'slides': slides,
        'search_query': search_query,
        'search_result': search_result,
        'organ_tags': Tag.objects.filter(is_organ=True),
        'stain_tags': Tag.objects.filter(is_stain=True),
        'other_tags': Tag.objects.filter(is_organ=False, is_stain=False),
        'selected_organ_tags': organs,
        'selected_stain_tags': stains,
        'selected_other_tags': tags,
        'selected_pathology': selected_pathology,
        'selected_histology': selected_histology,
    })


def get_image_browser_context(request):
    """
    TODO:
        - Handle organ system/histology_pathology selected when clicking the
        other category. Can possibly do this with checking which tab is active
        and passing it back to the template.
        - Filter on both organ and hist/path simultaneously
        - Clicking on organ/histopathology catagory, the view chenges to grid
        despite list view being the last choice
    """
    slides = Slide.objects.all()

    # Filters
    try:
        organs = request.GET.get('organ-system', False)

        if not organs:
            raise Exception("check organ selection, something went wrong")
        if organs == 'all':
            #  slides = slides
            selected_organ_tags = ['all']
        else:
            slides = slides.filter(tags__in=organs)
            selected_organ_tags = Tag.objects.filter(id=organs)

    except Exception as exc:
        print(f'{exc.__class__.__name__}: {exc}')
        #organs = []
        selected_organ_tags = ['all']

    # Handle histology/pathology buttons
    try:
        histology_pathology = request.GET.get('histology-pathology', False)

        if histology_pathology == 'histology':
            selected_both = False
            selected_histology = True
            selected_pathology = False
            slides = slides.filter(pathology=False)
        elif histology_pathology == 'pathology':
            selected_both = False
            selected_histology = False
            selected_pathology = True
            slides = slides.filter(pathology=True)
        else:
            selected_both = True
            selected_histology = False
            selected_pathology = False
            # do not filter slides

    except Exception as exc:
        print(f'{exc.__class__.__name__}: {exc}')
        selected_both = True
        selected_histology = False
        selected_pathology = False

    # TODO later: Add search option

    return {
        'slides': slides,
        'organ_tags': Tag.objects.filter(is_organ=True).order_by('name'),
        'selected_organ_tags': selected_organ_tags,
        'selected_both': selected_both,
        'selected_histology': selected_histology,
        'selected_pathology': selected_pathology,
    }


def image_browser(request):
    """
    TODO:   - CLEAN UP FUNCTION
    """

    prev_context = request.session.get('context', {})
    if 'selected_organ_tag' in prev_context.keys():
        if 'selected_organ_tag_ids' not in prev_context.keys():
            prev_context['selected_organ_tag_ids'] = queryset_to_id_list(prev_context['selected_organ_tag'])
        del prev_context['selected_organ_tag']
    prev_context['slides'] = slide_id_list_to_queryset(prev_context['slide_ids'])
    prev_context['selected_organ_tag'] = organ_tag_id_list_to_queryset(prev_context['selected_organ_tag_ids'])

    organ_changed = ('organ-system' in request.GET)
    hist_path_changed = ('histology-pathology' in request.GET)

    context = {
        'organ_tags': Tag.objects.filter(is_organ=True).order_by('name')
    }

    if organ_changed:
        # TODO: Handle organ changed
        selected_organ = request.GET.get('organ-system')
        if selected_organ == 'all':
            slides = Slide.objects.all()
            selected_organ_tag = ['all']
            # Store changes in session
            request.session['context']['selected_organ_tag_ids'] = selected_organ_tag
        else:
            selected_organ_tag = Tag.objects.filter(id=selected_organ)
            slides = Slide.objects.filter(tags__in=selected_organ_tag)
            # Store changes in session
            request.session['context']['selected_organ_tag_ids'] = queryset_to_id_list(selected_organ_tag)

        # Store changes in session
        request.session['context']['slide_ids'] = queryset_to_id_list(slides)
        # Add to context
        context['slides'] = slides
        context['selected_organ_tag'] = selected_organ_tag

    elif hist_path_changed:
        # TODO: Handle histology/pathology changed
        # Use previously selected organ slides
        selected_organ_tag = organ_tag_id_list_to_queryset(
            prev_context['selected_organ_tag_ids']
        )
        slides = Slide.objects.filter(tags__in=selected_organ_tag)

        histology_pathology = request.GET.get('histology-pathology')
        if histology_pathology == 'histology':
            selected_both = False
            selected_histology = True
            selected_pathology = False
            slides = slides.filter(pathology=False)
        elif histology_pathology == 'pathology':
            selected_both = False
            selected_histology = False
            selected_pathology = True
            slides = slides.filter(pathology=True)
        else:
            selected_both = True
            selected_histology = False
            selected_pathology = False
            # do not filter slides

        # Store changes in session
        request.session['context']['slide_ids'] = queryset_to_id_list(slides)
        # Add to context
        context['slides'] = slides
        context['selected_both'] = selected_both
        context['selected_histology'] = selected_histology
        context['selected_pathology'] = selected_pathology

    else:
        slides = Slide.objects.all()
        selected_organ_tag = ['all']
        # Store changes in session
        request.session['context']['slide_ids'] = queryset_to_id_list(slides)
        request.session['context']['selected_organ_tag_ids'] = queryset_to_id_list(selected_organ_tag)
        # Add to context
        context['slides'] = slides
        context['selected_organ_tag'] = selected_organ_tag

    update_session_entry = False
    for key, val in prev_context.items():
        if key not in context.keys():
            if key == 'slide_ids':
                if 'slides' in context.keys(): continue
                context['slides'] = slide_id_list_to_queryset(val)
            elif key == 'selected_organ_tag_ids':   # replace with 'selected_organ_tag'
                if 'selected_organ_tag' in context.keys(): continue
                context['selected_organ_tag'] = organ_tag_id_list_to_queryset(val)
            elif key == 'selected_organ_tag':   # replace with 'selected_organ_tag_ids' in request.session
                if 'selected_organ_tag' in context.keys(): continue
                update_session_entry = True
                new_value = ['all']
                context['selected_organ_tag'] = new_value
            else:
                context[key] = val

    if update_session_entry:
        request.session['context']['selected_organ_tag_ids'] = new_value
        del request.session['context']['selected_organ_tag']

    return render(request, 'slide/image_browser.html', context)


def queryset_to_id_list(queryset):
    if isinstance(queryset, django.db.models.query.QuerySet):
        id_list = [i[0] for i in queryset.values_list('id')]
        return id_list
    return queryset


def slide_id_list_to_queryset(id_list):
    queryset = Slide.objects.filter(id__in=id_list)
    return queryset


def organ_tag_id_list_to_queryset(id_list):
    if 'all' in id_list:
        return id_list

    queryset = Tag.objects.filter(is_organ=True, id__in=id_list)
    return queryset


def grid_view(request):


    context = get_image_browser_context(request)
    context['view_grid'] = True

    return render(request, 'slide/grid_view.html', context)


def list_view(request):

    context = get_image_browser_context(request)
    context['view_grid'] = False

    return render(request, 'slide/list_view.html', context)


def whole_slide_view_full(request, slide_id):
    slide = slide_cache.load_slide_to_cache(slide_id)
    return render(request, 'slide/view_wsi_full.html', {
        'slide': slide,
    })


def whole_slide_viewer(request, slide_id):
    slide = slide_cache.load_slide_to_cache(slide_id)
    return render(request, 'slide/view_wsi.html', {
        'slide': slide,
    })


def tile(request, slide_id, osd_level, x, y):
    """
    Gets OSD tile from slide, converts to JPEG and sends to client
    """
    slide = slide_cache.get_slide(slide_id)
    try:
        buffer = slide.get_osd_tile_as_buffer(osd_level, x, y)
    except Exception as e:
        print(e)
        return HttpResponse(status=404)
    except:
        print('An error occured while loading a tile', osd_level, x, y)
        return HttpResponse(status=404)

    return HttpResponse(buffer.getvalue(), content_type='image/jpeg')


def create_thumbnail(slide_id):
    import fast
    slide = slide_cache.load_slide_to_cache(slide_id)
    access = slide.image.getAccess(fast.ACCESS_READ)
    image = access.getLevelAsImage(slide.image.getNrOfLevels()-1)
    scale = float(image.getHeight())/image.getWidth()
    resize = fast.ImageResizer.create(128, round(128*scale)).connect(image)
    fast.ImageFileExporter\
        .create(f'thumbnails/{slide_id}.jpg')\
        .connect(resize)\
        .run()

@teacher_required
def add(request):
    if request.method == 'POST':
        form = SlideForm(request.POST, request.FILES)
        with transaction.atomic():
            if form.is_valid():
                # Save form and create thumbnail
                file_path = store_file_in_db(form.files['image_file'])
                slide = form.save(file_path)
                create_thumbnail(slide.id)

                organ_tags = form.cleaned_data['organ_tags']
                stain_tags = form.cleaned_data['stain_tags']
                other_tags = form.cleaned_data['other_tags']
                slide.tags.set(organ_tags | stain_tags | other_tags)

                messages.add_message(request, messages.SUCCESS, 'Image added to database')
                return redirect('slide:view_full', slide.id)
    else:
        form = SlideForm()

    return render(request, 'slide/add.html', {'form': form})


def store_file_in_db(f: UploadedFile):
    destination_path = os.path.join(os.getcwd(), 'uploaded_images', f.name)  # TODO: improve destination path according to future DB
    # TODO: Ask the user if to substitute or keep both files
    if os.path.exists(destination_path):
        os.remove(destination_path)

    with open(destination_path, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)

    return destination_path
