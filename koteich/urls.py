from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls')),
    path('dashboard/', include('apps.dashboard.urls')),
    path('chat/', include('apps.chat.urls')),
    path('servers/', include('apps.servers.urls')),
    path('auction/', include('apps.auction.urls')),
    path('forum/', include('apps.forum.urls')),
    path('monitoring/', include('apps.monitoring.urls')),
    path('about/', TemplateView.as_view(template_name='about.html'), name='about'),
    path('', TemplateView.as_view(template_name='about.html'), name='home'),
    path('promo/', include('apps.promo.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)