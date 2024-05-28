import json
import os

from django.contrib.auth import login
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.http import Http404, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from guardian.shortcuts import get_objects_for_user

from nodeodm.models import ProcessingNode
from app.models import Project, Task, ModelFiles
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django import forms
from webodm import settings
from app.utils import uploadImage  
from dotenv import load_dotenv
load_dotenv()

def index(request):
    # Check first access
    if User.objects.filter(is_superuser=True).count() == 0:
        if settings.SINGLE_USER_MODE:
            # Automatically create a default account
            User.objects.create_superuser('admin', 'admin@localhost', 'admin')
        else:
            # the user is expected to create an admin account
            return redirect('welcome')

    if settings.SINGLE_USER_MODE and not request.user.is_authenticated:
        login(request, User.objects.get(username="admin"), 'django.contrib.auth.backends.ModelBackend')

    return redirect(settings.LOGIN_REDIRECT_URL if request.user.is_authenticated
                    else settings.LOGIN_URL)

@login_required
def upload(request):
      if(request.method == "GET"):
        models = ModelFiles.objects.filter(owner=request.user.id).values('name', 'page_url', 'file_url')
        for model in models:
            print(model)

        context = {
            'models': models
        }
        return render(request, 'app/uploads.html', context) 
     
      if(request.method == "POST"): 
        try:   
           if(request.user.is_authenticated is False):
             return Http404()
        
           name = request.POST.get('name', None)
           file = request.FILES.get('file')
           file_name = request.FILES.get('file').name
           user_id = request.user.id
         
           file_url = uploadImage(request.FILES.get('file'))
           page_url = f"{os.getenv('APP_URL')}/3d_models/{user_id}/{file_name}"
           print(name, file_name, file_url, page_url)
           
           newFile = ModelFiles(owner=request.user, name=name, file_name=file_name, file_url=file_url, page_url=page_url)
           newFile.save()
           message = {
             'message': f"saved {file_name}",
           }
           
           return JsonResponse(message)
        
        except Exception as e:
            return JsonResponse({'error': e}) 

@login_required
def model_view(request, user_id,file_name):
    models = ModelFiles.objects.filter(owner=user_id, file_name=file_name).values("name","file_url")
    name = models[0]['name']
    file_url = models[0]['file_url']
    return render(request, 'app/model_view.html', {'model_name':name, 'file_url': file_url})

@login_required
def dashboard(request):
    no_processingnodes = ProcessingNode.objects.count() == 0
    if no_processingnodes and settings.PROCESSING_NODES_ONBOARDING is not None:
        return redirect(settings.PROCESSING_NODES_ONBOARDING)

    no_tasks = Task.objects.filter(project__owner=request.user).count() == 0
    no_projects = Project.objects.filter(owner=request.user).count() == 0

    # Create first project automatically
    if no_projects and request.user.has_perm('app.add_project'):
        Project.objects.create(owner=request.user, name=_("First Project"))

    return render(request, 'app/dashboard.html', {'title': _('Dashboard'),
        'no_processingnodes': no_processingnodes,
        'no_tasks': no_tasks
    })


@login_required
def map(request, project_pk=None, task_pk=None):
    title = _("Map")

    if project_pk is not None:
        project = get_object_or_404(Project, pk=project_pk)
        if not request.user.has_perm('app.view_project', project):
            raise Http404()
        
        if task_pk is not None:
            task = get_object_or_404(Task.objects.defer('orthophoto_extent', 'dsm_extent', 'dtm_extent'), pk=task_pk, project=project)
            title = task.name or task.id
            mapItems = [task.get_map_items()]
        else:
            title = project.name or project.id
            mapItems = project.get_map_items()

    return render(request, 'app/map.html', {
            'title': title,
            'params': {
                'map-items': json.dumps(mapItems),
                'title': title,
                'public': 'false',
                'share-buttons': 'false' if settings.DESKTOP_MODE else 'true'
            }.items()
        })


@login_required
def model_display(request, project_pk=None, task_pk=None):
    title = _("3D Model Display")
    print(project_pk, task_pk)
    if project_pk is not None:
        project = get_object_or_404(Project, pk=project_pk)
        if not request.user.has_perm('app.view_project', project):
            raise Http404()

        if task_pk is not None:
            task = get_object_or_404(Task.objects.defer('orthophoto_extent', 'dsm_extent', 'dtm_extent'), pk=task_pk, project=project)
            title = task.name or task.id
        else:
            raise Http404()
    
    print(json.dumps(task.get_model_display_params()))
    return render(request, 'app/3d_model_display.html', {
            'title': title,
            'params': {
                'task': json.dumps(task.get_model_display_params()),
                'public': 'false',
                'share-buttons': 'false' if settings.DESKTOP_MODE else 'true'
            }.items()
        })

def about(request):
    return render(request, 'app/about.html', {'title': _('About'), 'version': settings.VERSION})

@login_required
def processing_node(request, processing_node_id):
    pn = get_object_or_404(ProcessingNode, pk=processing_node_id)
    if not pn.update_node_info():
        messages.add_message(request, messages.constants.WARNING, _('%(node)s seems to be offline.') % {'node': pn})

    return render(request, 'app/processing_node.html', 
            {
                'title': _('Processing Node'), 
                'processing_node': pn,
                'available_options_json': pn.get_available_options_json(pretty=True)
            })

class FirstUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'password', )
        widgets = {
            'password': forms.PasswordInput(),
        }


def welcome(request):
    if User.objects.filter(is_superuser=True).count() > 0:
        return redirect('index')

    fuf = FirstUserForm()

    if request.method == 'POST':
        fuf = FirstUserForm(request.POST)
        if fuf.is_valid():
            admin_user = fuf.save(commit=False)
            admin_user.password = make_password(fuf.cleaned_data['password'])
            admin_user.is_superuser = admin_user.is_staff = True
            admin_user.save()

            # Log-in automatically
            login(request, admin_user, 'django.contrib.auth.backends.ModelBackend')
            return redirect('dashboard')

    return render(request, 'app/welcome.html',
                  {
                      'title': _('Welcome'),
                      'firstuserform': fuf
                  })


def handler404(request, exception):
    return render(request, '404.html', status=404)

def handler500(request):
    return render(request, '500.html', status=500)
