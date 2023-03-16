from django.core.paginator import Paginator

LAST_POSTS_NUMBER = 10


def get_paginator(request, posts):
    paginator = Paginator(posts, LAST_POSTS_NUMBER)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
