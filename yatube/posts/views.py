from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post
from .utils import get_paginator

TITLE_FIRST_CHARS = 30


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
    following = request.user.is_authenticated and Follow.objects.filter(
        user=request.user.id,
        author=author
    ).exists()
    context = {
        'author': author,
        'page_obj': get_paginator(request, posts),
        'all_posts': posts.count(),
        'following': following,
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


@login_required
def delete_comment(requset, post_id, comment_id):
    comment = Comment.objects.get(id=comment_id)
    if requset.user == comment.author:
        comment.delete()
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
def post_detele(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user == post.author:
        post.delete()
    return render(request, 'posts/delete_post.html')


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
    if request.user.username != username:
        Follow.objects.get_or_create(
            user=request.user,
            author=get_object_or_404(User, username=username)
        )
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    Follow.objects.filter(
        user=request.user,
        author=get_object_or_404(User, username=username)
    ).delete()
    return redirect('posts:profile', username)


def search(request):
    if 'search' in request.GET and request.GET['search']:
        search_term = request.GET.get('search')
        posts = Post.objects.filter(
            Q(text__iregex=search_term)
            | Q(author__username__iregex=search_term)
            | Q(author__first_name__iregex=search_term)
            | Q(group__title__iregex=search_term)
        ).distinct()
        context = {
            'page_obj': get_paginator(request, posts),
            'search_term': search_term,
        }
        return render(request, 'posts/search_results.html', context)
    else:
        return redirect('posts:index')
