from .models import Category

def forum_categories(request):
    return {
        'forum_categories': Category.objects.all().order_by('order', 'name')
    }