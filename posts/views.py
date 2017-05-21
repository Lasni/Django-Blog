from urllib.parse import quote_plus
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Post
from .forms import PostForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from comments.models import Comment
from comments.forms import CommentForm

# Create your views here.


def posts_create(request):
    if not request.user.is_staff or not request.user.is_superuser:
        raise Http404
    form = PostForm(request.POST or None, request.FILES or None)
    context = {
        "form": form,
    }

    if form.is_valid():
        instance = form.save(commit=False)
        instance.user = request.user
        instance.save()
        messages.success(request, "Successfully created")  # a message
        return HttpResponseRedirect(instance.get_absolute_url())
    return render(request, "post-form.html", context)


def posts_detail(request, slug=None):
    instance = get_object_or_404(Post, slug=slug)
    if instance.publish > timezone.now().date() or instance.draft:
        if not request.user.is_staff or not request.user.is_superuser:
            raise Http404
    share_string = quote_plus(instance.content)

    initial_data = {"content_type": instance.get_content_type,
                    "object_id": instance.id}

    comments = instance.comments
    form = CommentForm(request.POST or None, initial=initial_data)
    if form.is_valid():
        c_type = form.cleaned_data.get("content_type")
        content_type = ContentType.objects.get(model=c_type)
        obj_id = form.cleaned_data.get("object_id")
        content_data = form.cleaned_data.get("content")

        new_comment, created = Comment.objects.get_or_create(user=request.user,
                                                             content_type=content_type,
                                                             object_id=obj_id,
                                                             content=content_data)

    context = {
        "title": instance.title,
        "instance": instance,
        "share_string": share_string,
        "comments": comments,
        "comment_form": form
    }
    return render(request, "posts-detail.html", context)


def posts_list(request):
    today = timezone.now().date()
    queryset_list = Post.objects.active()
    if request.user.is_staff or request.user.is_superuser:
        queryset_list = Post.objects.all()

    query = request.GET.get("query")
    if query:
        queryset_list = queryset_list.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query)).distinct()
    paginator = Paginator(queryset_list, 2)  # Show 5 contacts per page
    page_request_var = 'page'
    page = request.GET.get(page_request_var)
    try:
        queryset = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        queryset = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        queryset = paginator.page(paginator.num_pages)

    context = {
        'title': 'List',
        'object_list': queryset,
        'page_request_var': page_request_var,
        'today': today
    }

    return render(request, "post-list.html", context)


def posts_update(request, slug=None):
    if not request.user.is_staff or not request.user.is_superuser:
        raise Http404
    # first we need an already existing instance
    instance = get_object_or_404(Post, slug=slug)
    # we also need a form
    form = PostForm(request.POST or None,
                    request.FILES or None, instance=instance)
    context = {  # context to render the html
        "title": instance.title,
        "instance": instance,
        "form": form,
    }

    if form.is_valid():  # if the form is valid
        # overwrite the instance with the new data
        instance = form.save(commit=False)
        instance.save()  # save it to the DB
        messages.success(request, "Successfully updated")  # message
        # redirect to that post
        return HttpResponseRedirect(instance.get_absolute_url())
    return render(request, "post-form.html", context)


def posts_delete(request, slug=None):
    if not request.user.is_staff or not request.user.is_superuser:
        raise Http404
    instance = get_object_or_404(Post, slug=slug)
    instance.delete()
    messages.success(request, "Successfully deleted")
    return redirect("posts:list")


def listing(request):
    contact_list = Contacts.objects.all()
    return render(request, 'list.html', {'contacts': contacts})
