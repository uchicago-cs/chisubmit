from chisubmit.backend.api import views
from django.conf.urls import url

URL_PREFIX = r"^api/v1/"

urlpatterns = [
    url(URL_PREFIX + r'courses/$', views.course_list),
    url(URL_PREFIX + r'courses/(?P<course_slug>[a-zA-Z0-9_-]+)/$', views.course_detail),
]