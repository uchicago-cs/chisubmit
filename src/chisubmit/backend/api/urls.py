from chisubmit.backend.api import views
from rest_framework.urlpatterns import format_suffix_patterns
from django.conf.urls import url

URL_PREFIX = r"^api/v1/"

urlpatterns = [
    url(URL_PREFIX + r'courses/$', views.CourseList.as_view(), name="course-list"),
    url(URL_PREFIX + r'courses/(?P<course>[a-zA-Z0-9_-]+)/$', views.CourseDetail.as_view(), name="course-detail"),

    url(URL_PREFIX + r'courses/(?P<course>[a-zA-Z0-9_-]+)/instructors/$', views.InstructorList.as_view(), name="instructor-list"),
    url(URL_PREFIX + r'courses/(?P<course>[a-zA-Z0-9_-]+)/instructors/(?P<username>[a-zA-Z0-9_-]+)$', views.InstructorDetail.as_view(), name="instructor-detail"),

    url(URL_PREFIX + r'courses/(?P<course>[a-zA-Z0-9_-]+)/graders/$', views.GraderList.as_view(), name="grader-list"),
    url(URL_PREFIX + r'courses/(?P<course>[a-zA-Z0-9_-]+)/graders/(?P<username>[a-zA-Z0-9_-]+)$', views.GraderDetail.as_view(), name="grader-detail"),

    url(URL_PREFIX + r'courses/(?P<course>[a-zA-Z0-9_-]+)/students/$', views.StudentList.as_view(), name="student-list"),
    url(URL_PREFIX + r'courses/(?P<course>[a-zA-Z0-9_-]+)/students/(?P<username>[a-zA-Z0-9_-]+)$', views.StudentDetail.as_view(), name="student-detail"),
    
]

urlpatterns = format_suffix_patterns(urlpatterns)