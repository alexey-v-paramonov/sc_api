from django.conf.urls import url
from users.views import Users

urlpatterns = [
    url(r'^users/(?P<pk>[0-9]+)/$', Users.as_view()),
    url(r'^users/$', Users.as_view()),
]
