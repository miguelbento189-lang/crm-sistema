from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.views.generic import RedirectView


admin.site.site_header = 'CRM de Leads'
admin.site.site_title = 'CRM de Leads'
admin.site.index_title = 'Administracao do CRM'


urlpatterns = [
    path('admin/', admin.site.urls),
    path('login', RedirectView.as_view(url='/sistema/login/', permanent=False), name='root_login_no_slash'),
    path('login/', RedirectView.as_view(url='/sistema/login/', permanent=False), name='root_login'),
    path('', RedirectView.as_view(pattern_name='product_login', permanent=False), name='root_redirect'),
    path('sistema/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='product_login'),
    path('sistema/logout/', auth_views.LogoutView.as_view(), name='product_logout'),
    path('sistema/', include(('crm.urls', 'crm'), namespace='crm')),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
