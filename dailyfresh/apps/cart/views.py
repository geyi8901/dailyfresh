from django.shortcuts import render
from django.views.generic import View #导入类视图
from django.http import JsonResponse
from goods.models import GoodsSKU
from django_redis import get_redis_connection
from utils.mixin import LoginRequiredMixin
# Create your views here.

class CartAddView(View):
    '''购物车记录添加'''
    def post(self, request):
        '''购物车记录的添加'''
        #接收数据
        user = request.user
        if not user.is_authenticated():
            #用户未登录
            return JsonResponse({'res':0, 'errmsg':'请先登录'})
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')
        #数据校验
        if not all([sku_id, count]):
            return JsonResponse({'res':1, 'errmsg':'数据不完整'})
        #校验添加商品的数量
        try:
            count = int(count)
        except Exception as e:
            #数目出错
            return JsonResponse({'res':2, 'errmsg':'商品数目出错'})
        #校验商品是否存在

        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res':3, 'errmsg':'商品不存在'})

        #业务处理:添加购物车记录

        conn = get_redis_connection('default')
        cart_key = 'cart_%d'%user.id
        # 先尝试获取sku_id的值
        #如果sku_id在hash中不存在,函数返回None
        cart_count = conn.hget(cart_key, sku_id)
        if cart_count:
            #累加购物车商品的数目
            count += int(cart_count)
        #校验商品的库存
        if count > sku.stock:
            return JsonResponse({'res':4, 'errmsg':'商品库存不足'})
        #设置hash中sku_id对应的值
        conn.hset(cart_key, sku_id, count)
        #统计计算用户购物车中商品的条目数
        total_count = conn.hlen(cart_key)
        #返回应答
        return JsonResponse({'res':5, 'total_count':total_count,  'message':'添加成功'})

#/cart/
class CartInfoView(LoginRequiredMixin, View):
    '''购物车页面显示'''
    def get(self, request):
        '''显示'''
        # 获取登录的用户
        user = request.user
        # 获取用户购物车商品的信息
        conn = get_redis_connection('default')
        cart_key = 'cart_%d'%user.id
        # 获取{'商品id':'数量'}
        cart_dict = conn.hgetall(cart_key)
        # 遍历获取商品的信息
        skus=[]
        # 保存购物车总数目,总价格
        total_count=0
        total_price=0
        for sku_id, count in cart_dict.items():
            #根据商品id获取商品的信息
            sku = GoodsSKU.objects.get(id=sku_id)
            #计算商品的小计
            amount = sku.price*int(count)
            # 动态给sku增加属性amount,保存小计
            sku.amount = amount

            sku.count = count
            skus.append(sku)
            #累计总数目,总价格
            total_count += int(count)
            total_price += amount

        #组织上下文
        context = {
            'total_count':total_count,
            'total_price':total_price,
            'skus':skus
        }
        return render(request, 'cart.html', context)