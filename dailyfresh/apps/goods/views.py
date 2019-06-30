from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.views.generic import View #导入类视图
from goods.models import GoodsSKU, GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner
from order.models import OrderGoods
from django_redis import get_redis_connection
from django.core.cache import cache
from django.core.paginator import Paginator

# Create your views here.

def index(request):



    return render(request, 'index.html')

class IndexView(View):
    '''首页'''
    def get(self, request):
        '''显示首页'''
        #尝试从缓存中获取数据
        context = cache.get('index_page_data')
        if context is None:
            #缓存中没有数据:
            print('设置缓存')
            #获取商品的种类信息
            types = GoodsType.objects.all()
            for type in types:
                print('*******商品分类名称:'+type.name)
            #获取首页轮播商品信息
            goods_banners = IndexGoodsBanner.objects.all().order_by('index')

            #获取首页促销活动信息
            promotion_banners = IndexPromotionBanner.objects.all().order_by('index')

            #获取首页分类商品展示信息
            # type_goods_banners = IndexTypeGoodsBanner.objects.all()
            #获取每个种类信息
            for type in types: #GoodsType
                #获取type种类首页分类商品的图片的展示信息
                image_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1).order_by('index')
                #获取type种类首页分类商品的文字展示信息
                title_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0).order_by('index')
                # 动态给type增加属性,分别保存首页分类商品的图片展示信息和文字展示信息
                type.image_banners = image_banners
                type.title_banners = title_banners

            context = {'types': types,
                       'goods_banners': goods_banners,
                       'promotion_banners': promotion_banners}

            #设置缓存
            cache.set('index_page_data', context, 3600)

        #获取用户购物车种商品数目
        cart_count = 0
        user = request.user
        if user.is_authenticated():
            #用户已经登录
            conn = get_redis_connection('default')
            cart_key = 'cart_%d'%user.id
            cart_count = conn.hlen(cart_key)

        #组织模板上下文
        context.update(cart_count=cart_count)
        # context = {'types':types,
        #            'goods_banners':goods_banners,
        #            'promotion_banners':promotion_banners,
        #            'cart_count':cart_count}

        return render(request, 'index.html', context)


#/goods/商品id
class DetailView(View):
    '''详情页'''
    def get(self, request, goods_id):
        '''显示详情页'''
        try:
            sku = GoodsSKU.objects.get(id=goods_id)
        except GoodsSKU.DoesNotExist:
            #商品不存在
            return redirect(reverse('goods:index'))

        #获取商品的分类信息:
        types = GoodsType.objects.all()
        #获取商品的评论信息:
        sku_orders = OrderGoods.objects.filter(sku=sku).exclude(comment='')

        #获取新品推荐信息
        new_skus = GoodsSKU.objects.filter(type=sku.type).order_by('-create_time')[:2]
        #获取同一个spu的其他规格
        same_spu_skus = GoodsSKU.objects.filter(goods = sku.goods).exclude(id=goods_id)
        #购物车信息
        cart_count = 0
        user = request.user
        if user.is_authenticated():
            # 用户已经登录
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = conn.hlen(cart_key)
            #添加用户浏览的历史记录
            conn = get_redis_connection('default')
            history_key='history_%d'%user.id
            #从列表中移除goods_id的记录
            conn.lrem(history_key, 0, goods_id)
            #把goods_id插入列表左侧
            conn.lpush(history_key, goods_id)
            #只保存用户最新浏览的5条信息
            conn.ltrim(history_key, 0, 4)


        #上下文
        context = {'sku':sku, 'types':types,
                   'sku_orders':sku_orders,
                   'new_skus':new_skus,
                   'cart_count':cart_count,
                   'same_spu_skus':same_spu_skus}
        return render(request, 'detail.html', context)


class ListView(View):
    '''列表页面'''
    def get(self, request, type_id, page):
        '''显示列表页'''
        #获取种类信息
        try:
            type = GoodsType.objects.get(id=type_id)
        except GoodsType.DoesNotExist:
            return redirect(reverse('goods:index'))

        #获取商品的分类信息
        types = GoodsType.objects.all()

        #获取排序方式:
        sort = request.GET.get('sort')
        if sort == 'price':
            # 获取分类商品的信息
            skus = GoodsSKU.objects.filter(type=type).order_by('price')
        elif sort == 'hot':
            skus = GoodsSKU.objects.filter(type=type).order_by('-sales')
        else:
            sort = 'default'
            skus = GoodsSKU.objects.filter(type=type).order_by('-id')

        #对数据进行分页
        paginator = Paginator(skus, 1)

        #获取第page页的内容
        try:
            page = int(page)
        except Exception as e:
            page = 1

        if page > paginator.num_pages:
            page = 1

        #获取第page页的Page实例对象
        skus_page = paginator.page(page)

        # todo:进行页码的控制,页面上最多显示5个页码
        #1.总页数小于5页,  显示 所有页码
        #2.总数大于5页,当前页小于3页:显示1-5页
        #3.当前页是后三页:显示 后5页页码
        #4.其他情况,显示 当前页前两页 + 当前页+当前页后两页
        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1, num_pages+1)
        elif page <= 3:
            pages = range(1, 6)
        elif num_pages-page <=2:
            pages = range(num_pages-4, num_pages+1)
        else:
            pages = range(page-2, page+3)

        # 获取新品推荐信息
        new_skus = GoodsSKU.objects.filter(type=type).order_by('-create_time')[:2]

        # 购物车信息
        cart_count = 0
        user = request.user
        if user.is_authenticated():
            # 用户已经登录
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = conn.hlen(cart_key)

        #组织模板上下文
        context = {'type':type,
                   'types':types,
                   'skus_page':skus_page,
                   'new_skus':new_skus,
                   'cart_count':cart_count,
                   'sort':sort,
                   'pages':pages}

        return render(request, 'list.html', context)