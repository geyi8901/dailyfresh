from celery import Celery
from django.conf import settings
from django.core.mail import send_mail
import time

from django.template import loader, RequestContext
from django_redis import get_redis_connection
from django.shortcuts import render
import os
# import django
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dailyfresh.settings")#这一行在wsgi.py中有初始化
# django.setup()  #django初始化
from goods.models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner


app = Celery('celery_tasks.tasks', broker='redis://127.0.0.1:6379/8')

#定义任务函数
@app.task
def send_register_active_email(to_email, username, token):
    '''发送激活邮件'''
    # 发邮件
    subject = '照片已经发送,主'
    message = '照片已经通过扫描方式,发送给你,请查收,主'
    
    sender = settings.EMAIL_FROM
    html_message = '<h1>%s，欢迎您成为天天生鲜注册会员,感谢您的使用！</h1><h1>请点击以下链接激活您的账户</h1><br/><a href="http:127.0.0.1:8000/users/active/%s">http:127.0.0.1:8000/users/active/%s</a>' % (username, token, token)
    recvier = [to_email]
    send_mail(subject, message, sender, recvier, html_message=html_message)
    time.sleep(5)

@app.task
def generate_static_index_html():
    '''首页'''
    # 获取商品的种类信息
    types = GoodsType.objects.all()
    for type in types:
        print('*******商品分类名称:' + type.name)
    # 获取首页轮播商品信息
    goods_banners = IndexGoodsBanner.objects.all().order_by('index')

    # 获取首页促销活动信息
    promotion_banners = IndexPromotionBanner.objects.all().order_by('index')

    # 获取首页分类商品展示信息
    # type_goods_banners = IndexTypeGoodsBanner.objects.all()
    # 获取美各种累信息
    for type in types:  # GoodsType
        # 获取type种类首页分类商品的图片的展示信息
        image_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1).order_by('index')
        # 获取type种类首页分类商品的文字展示信息
        title_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0).order_by('index')
        # 动态给type增加属性,分别保存首页分类商品的图片展示信息和文字展示信息
        type.image_banners = image_banners
        type.title_banners = title_banners

    # 组织模板上下文
    context = {'types': types,
               'goods_banners': goods_banners,
               'promotion_banners': promotion_banners
               }

    # 使用模板
    # 1加载模板
    temp = loader.get_template(('static_index.html'))
    # 2定义上下文
    # context = RequestContext(request, context) #没有request所以忽略
    # 模板渲染
    static_index_html = temp.render(context)

    # 生成首页静态文件
    save_path = os.path.join(settings.BASE_DIR, 'static/index.html')
    print(save_path)
    with open(save_path, 'w') as f:
        f.write(static_index_html)