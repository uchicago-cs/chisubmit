from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    url(r'^', include('chisubmit.backend.api.urls')),
    url(r'^admin/', include(admin.site.urls)),
]
