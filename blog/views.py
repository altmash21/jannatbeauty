from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import BlogPost

def blog_list(request):
    posts = BlogPost.objects.filter(published=True)
    category = request.GET.get('category')
    
    if category:
        posts = posts.filter(category=category)
    
    paginator = Paginator(posts, 6)  # 6 posts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = BlogPost.objects.values_list('category', flat=True).distinct()
    
    return render(request, 'blog/list.html', {
        'page_obj': page_obj,
        'categories': categories,
        'selected_category': category,
    })

def blog_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug, published=True)
    recent_posts = BlogPost.objects.filter(published=True).exclude(id=post.id)[:3]
    
    return render(request, 'blog/detail.html', {
        'post': post,
        'recent_posts': recent_posts,
    })
