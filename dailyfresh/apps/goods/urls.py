from django.conf.urls import  url
# from goods import views
from goods.views import IndexView

urlpatterns = [
    #url(r'^$', views.index, name='index'),
    url(r'^$', IndexView.as_view(), name='index'),
]
