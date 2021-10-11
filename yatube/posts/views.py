from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http.response import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, settings.PAGE_VOL)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, settings.PAGE_VOL)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'posts': posts,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    count = posts.count()
    paginator = Paginator(posts, settings.PAGE_VOL)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    following = (
        request.user.is_authenticated
        and request.user.username != username
        and Follow.objects.filter(user=request.user, author=author).exists()
    )
    context = {
        'author': author,
        'posts': posts,
        'count': count,
        'page_obj': page_obj,
        'following': following
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    context = {
        'post': post,
        'form': form,
        'comments': post.comments.all(),
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/post_create.html'
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', request.user)
    context = {'form': form}
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    template = 'posts/post_create.html'
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'GET':
        if request.user != post.author:
            return redirect('posts:post_detail', post_id=post_id)
        form = PostForm(
            request.POST or None,
            files=request.FILES or None,
            instance=post
        )
    if request.method == 'POST':
        form = PostForm(
            request.POST,
            instance=post,
            files=request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            form.save()
        return redirect('posts:post_detail', post_id=post_id)
    return render(request, template, {
                  'form': form, 'post': post, 'is_edit': True
                  })


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


def paginator_view(request, post_list):
    paginator = Paginator(post_list, settings.PAGE_VOL)
    page_nubmer = request.GET.get('page')
    return paginator.get_page(page_nubmer)


@login_required
def follow_index(request):
    page_obj = paginator_view(request, Post.objects.filter(
        author__following__user=request.user
    ))
    return render(request, 'posts/follow.html', {
        'page_obj': page_obj,
    })


@login_required
def profile_follow(request, username):
    if request.user.username != username:
        author = get_object_or_404(User, username=username)
        Follow.objects.get_or_create(user=request.user, author=author)
        return redirect('posts:profile', username)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required
def profile_unfollow(request, username):
    get_object_or_404(
        Follow,
        user=request.user,
        author__username=username
    ).delete()
    return redirect('posts:profile', username=username)
