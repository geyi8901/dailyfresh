from django.conf.urls import  url
# from goods import views
from goods.views import IndexView, DetailView, ListView

urlpatterns = [
    #url(r'^$', views.index, name='index'),
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^goods/(?P<goods_id>\d+)$', DetailView.as_view(), name='detail'),#详情页
    url(r'^goods/(?P<type_id>\d+)/(?P<page>\d+)$', ListView.as_view(), name='list'),#列表页
]
