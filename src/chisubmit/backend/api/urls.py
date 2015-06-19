from chisubmit.backend.api import views
from rest_framework.urlpatterns import format_suffix_patterns
from django.conf.urls import url

URL_PREFIX = r"^api/v1/"

urlpatterns = [
    url(URL_PREFIX + r'courses/$', views.CourseList.as_view(), name="course-list"),
    url(URL_PREFIX + r'courses/(?P<course_slug>[a-zA-Z0-9_-]+)/$', views.CourseDetail.as_view(), name="course-detail"),
]

urlpatterns = format_suffix_patterns(urlpatterns)