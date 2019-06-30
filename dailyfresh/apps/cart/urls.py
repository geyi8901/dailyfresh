from django.conf.urls import url
from cart.views import CartAddView, CartInfoView ,CartUpdateView, CartDeleteView
urlpatterns = [
    url('^add$', CartAddView.as_view(), name='add'),#购物车记录添加
    url('^$', CartInfoView.as_view(), name='show'),#购物车页面显示
    url('^update$', CartUpdateView.as_view(), name='update'),#更新购物车
    url('^delete$', CartDeleteView.as_view(), name='delete'),#购物车删除
]
