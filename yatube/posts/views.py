from django.core.paginator import Paginator
from django.views.decorators.cache import cache_page
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm

POST_NUM = 10


def paginator(request, post_list, post_num):
    paginator = Paginator(post_list, post_num)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


@cache_page(20, key_prefix="index_page")
def index(request):
    template = "posts/index.html"
    post_list = Post.objects.all()
    context = {'page_obj': paginator(request, post_list, POST_NUM)}
    return render(request, template, context)


def group_posts(request, slug):
    template = "posts/group_list.html"
    group = get_object_or_404(Group.objects.prefetch_related('posts'),
                              slug=slug)
    post_list = group.posts.all()
    context = {'group': group,
               'page_obj': paginator(request, post_list, POST_NUM)}
    return render(request, template, context)


def profile(request, username):
    template = "posts/profile.html"
    author = get_object_or_404(User.objects.prefetch_related('posts'),
                               username=username)
    post_list = author.posts.all()
    context = {'author': author,
               'page_obj': paginator(request, post_list, POST_NUM)}
    if not str(request.user) == 'AnonymousUser':
        following_authors = User.objects.filter(following__user=request.user)
        if author in following_authors:
            following = True
        else:
            following = False
        context = {'author': author, 'following': following,
                   'page_obj': paginator(request, post_list, POST_NUM)}
    return render(request, template, context)


def post_detail(request, post_id):
    template = "posts/post_detail.html"
    post = get_object_or_404(
        Post.objects.select_related('group', 'author'), pk=post_id)
    comment_list = post.comments.all()
    form = CommentForm(request.POST or None)
    context = {'post': post, 'comments': comment_list, 'form': form}
    return render(request, template, context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None)
    if form.is_valid():
        form = form.save(commit=False)
        form.author = request.user
        form.save()
        return redirect('posts:profile', username=request.user.username)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user == post.author:
        is_edit = True
        form = PostForm(
            request.POST or None,
            files=request.FILES or None,
            instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:post_detail', post_id=post_id)
        return render(request, 'posts/create_post.html',
                      {'form': form, 'is_edit': is_edit, 'post_id': post_id})
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def add_comment(request, post_id):
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = get_object_or_404(Post, pk=post_id)
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    template = "posts/follow.html"
    post_list = Post.objects.filter(author__following__user=request.user)
    context = {'page_obj': paginator(request, post_list, POST_NUM)}
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    if request.user == get_object_or_404(User, username=username):
        return redirect('posts:profile', username=username)
    follow = Follow(
        user=request.user,
        author=get_object_or_404(User, username=username)
    )
    follow.save()
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    follow = Follow.objects.get(
        user=request.user,
        author=get_object_or_404(User, username=username)
    )
    follow.delete()
    return redirect('posts:profile', username=username)
