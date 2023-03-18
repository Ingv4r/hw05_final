from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post
from .utils import get_paginator

TITLE_FIRST_CHARS = 30
CACHE_TIME_IN_SEC = 20


@cache_page(CACHE_TIME_IN_SEC, key_prefix='index_page')
def index(request):
    posts = Post.objects.all()
    context = {
        'page_obj': get_paginator(request, posts),
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    context = {
        'group': group,
        'page_obj': get_paginator(request, posts),
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = Post.objects.filter(
        author=author
    ).all()
    following = Follow.objects.filter(
        user=request.user.id,
        author=author
    ).exists()
    context = {
        'author': author,
        'page_obj': get_paginator(request, posts),
        'all_posts': posts.count(),
        'following': following,
        'button': request.user.is_authenticated,
        # Сделал отдельно, чтобы в шаблон switcher
        # не нужно было сильно менять
    }
    return render(request, 'posts/profile.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect('posts:post_detail', post_id)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    posts_number = Post.objects.select_related(
        'author'
    ).filter(author__username=post.author).count()
    title = post.text[:TITLE_FIRST_CHARS]
    context = {
        'post': post,
        'title': title,
        'posts_number': posts_number,
        'image': post.image or None,
        'form': CommentForm(request.POST or None),
        'comments': post.comments.all(),
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if form.is_valid():
        temp_form = form.save(commit=False)
        temp_form.author = request.user
        temp_form.save()
        return redirect('posts:profile', temp_form.author)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post,
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    context = {
        'form': form,
        'is_edit': True,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def follow_index(request):
    authors_posts = Post.objects.select_related(
        'author',
    ).filter(author__following__user=request.user)
    context = {'page_obj': get_paginator(request, authors_posts)}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    try:
        Follow.objects.create(
            user=request.user,
            author=get_object_or_404(User, username=username)
        )
    except IntegrityError:
        pass
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    Follow.objects.filter(
        user=request.user,
        author=get_object_or_404(User, username=username)
    ).delete()
    return redirect('posts:profile', username)
