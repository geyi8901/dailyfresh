from django.shortcuts import render,redirect
from django.core.urlresolvers import reverse #反向解析
from django.contrib.auth import authenticate, login, logout
from django.views.generic import View #导入类视图
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from django.conf import settings #下面加密的秘钥，需要使用setting里面的key
from itsdangerous import SignatureExpired #秘钥过期的异常
from django.core.mail import send_mail
from django.http import HttpResponse
from utils.mixin import LoginRequiredMixin
from django_redis import get_redis_connection
from goods.models import GoodsSKU
from celery_tasks.tasks import send_register_active_email
import re
from user.models import User, Address

# Create your views here.
#类视图使用方法：
class RegisterView(View):
    '''注册类'''
    def get(self,request):
        return render(request, 'register.html')
    def post(self,request):
        # 进行注册处理
        # 接收数据
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')
        # 进行数据校验
        if not all([username, password, email]):
            # 数据不完整
            return render(request, 'register.html', {'errmsg': '数据不完整'})
        # 校验邮箱
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})

        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请同意协议'})

        # 校验用户名是否重复
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # 用户名不存在
            user = None
        if user:
            # 用户名已经存在
            return render(request, 'register.html', {'errmsg': '用户名已存在'})

        # 进行业务处理：注册用户

        # user.username = username
        # user.password = password
        # user.save()
        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()

        # 邮箱激活，发送激活邮件
        serializer = Serializer(settings.SECRET_KEY, 3600)
        info = {'confirm': user.id}
        token = serializer.dumps(info) #这个是bytes数据格式,如果不解码，导致发送邮件激活链接中，有 b'....' 格式
        token = token.decode('utf8') #进行编码 bytes转为str类型
        # # # 发邮件
        # subject = '天天生鲜欢迎信息'
        # message = '很高兴能认识你。非常感谢'
        # sender = settings.EMAIL_FROM
        # # html_message = '<h1>%s，欢迎您成为天天生鲜注册会员！</h1><h1>请点击以下链接激活您的账户</h1><br/><a href="http:127.0.0.1:8000/user/active/%s">http:127.0.0.1:8000/user/active/%s</a>'%(username,token,token)
        # print('^^^^^^^^^^^^setting:' + sender)
        # recvier = [email]
        # print('^^^^^^^^^^^email信息：' + str(recvier))
        # send_mail(subject, message, sender, recvier)


        #使用celery发送邮件
        send_register_active_email.delay(email,username,token)




        # 返回应答
        return redirect(reverse('goods:index'))

class ActiveView(View):
    '''用户激活'''
    def get(self, request, token):
        '''进行用户激活'''
        #获取激活的信息
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:
            info = serializer.loads(token)
            #获取激活用户的id
            user_id = info['confirm']
            #根据id获取用户信息
            user = User.objects.get(id = user_id)
            user.is_active = 1
            user.save()
            #跳转到登录页面
            return redirect(reverse('user:login'))
        except SignatureExpired as e:
            #激活链接过期
            return HttpResponse('激活链接已经过期')

class LoginView(View):
    '''登录'''
    def get(self, request):
        '''显示登录页面'''
        # 判断是否记住了用户名
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checked = 'checked'
        else:
            username = ''
            checked = ''

        # 使用模板
        return render(request, 'login.html', {'username':username, 'checked':checked})

    def post(self, request):
        '''登录校验'''
        # 接收数据
        username = request.POST.get('username')
        password = request.POST.get('pwd')

        # 校验数据
        if not all([username, password]):
            return render(request, 'login.html', {'errmsg':'数据不完整'})

        # 业务处理:登录校验
        user = authenticate(username=username, password=password)
        if user is not None:
            # 用户名密码正确
            if user.is_active:
                # 用户已激活
                # 记录用户的登录状态
                login(request, user)
                #获取登陆后将要跳转的地址： #如果没值，用后面这个默认值
                #默认跳转到首页goods:index
                next_url = request.GET.get('next', reverse('goods:index'))
                # 跳转到首页
                response = redirect(next_url) # HttpResponseRedirect

                # 判断是否需要记住用户名
                remember = request.POST.get('remember')

                if remember == 'on':
                    # 记住用户名
                    response.set_cookie('username', username, max_age=7*24*3600)
                else:
                    response.delete_cookie('username')

                # 返回response
                return response
            else:
                # 用户未激活
                return render(request, 'login.html', {'errmsg':'账户未激活'})
        else:
            # 用户名或密码错误
            return render(request, 'login.html', {'errmsg':'用户名或密码错误'})


class LogoutView(View):
    '''用户退出'''
    def get(self, request):
        '''退出登录'''
        #清楚用户session信息
        logout(request)

        return redirect(reverse('goods:index'))


# /user
class UserInfoView(LoginRequiredMixin, View):
    '''用户中心信息页面'''
    def get(self, request):

        user = request.user
        address = Address.objects.get_default_address(user)

        #page = 'user'
        #request.user.is_authenticated()

        #获取用户浏览记录
        # from redis import StrictRedis
        # sr = StrictRedis(host='127.0.0.1', port='6379', db=1)
        con = get_redis_connection('default')
        history_key = 'history_%d'%user.id
        #H获取用户最新浏览的5条商品id
        sku_ids = con.lrange(history_key, 0, 4)

        #从数据库中查询用户浏览的商品具体信息
        # goods_li = GoodsSKU.objects.filter(id__in=sku_ids)
        #遍历获取浏览的商品信息
        goods_li = []
        for id in sku_ids:
            goods = GoodsSKU.objects.get(id=id)
            goods_li.append(goods)


        #除了给模板传递变量外，django也会把request.user也传给模板
        return render(request, 'user_center_info.html',{'page':'user','address':address,'goods_li':goods_li})


#/user/order
class UserOrderView(LoginRequiredMixin, View):
    '''订单信息页面'''
    def get(self, request):
        return render(request, 'user_center_order.html',{'page':'order'})


#/user/address
class AddressView(LoginRequiredMixin, View):
    '''地址信息页面'''
    def get(self, request):
        # 获取登录用户的对应user对象
        user = request.user
        #获取用户的默认收货地址：

        # try:
        #     address = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        #     # 不存在默认收货地址
        #     address = None
        address = Address.objects.get_default_address(user)

        #使用模板
        print('**********默认地址address:'+str(address))
        return render(request, 'user_center_site.html',{'page':'address','address':address})

    def post(self, request):
        print('&&&&&&&&&&&&&&&&&&')
        '''地址添加'''
        #接收数据
        receiver = request.POST.get('receiver')
        addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')
        #校验数据
        if not all([receiver, addr, phone]):
            return render(request, 'user_center_site.html', {'errmsg':'数据不完整'})

        if not re.match(r'^1[3456789]\d{9}$', phone):
            return render(request, 'user_center_site.html', {'errmsg':'手机格式不正确'})

        #业务处理，添加地址
        #获取登录用户的对应user对象
        user = request.user
        # try:
        #     address = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        #     #不存在默认收货地址
        #     address = None
        address = Address.objects.get_default_address(user)

        #查到默认收货地址：
        if address:
            is_default = False
        else:
            is_default = True

        #添加地址：
        Address.objects.create(user=user, addr=addr, receiver=receiver,zip_code=zip_code,phone=phone,is_default=is_default)

        print('************更新的地址：'+str(user)+'****'+receiver)
        #返回应答，刷新地址页面
        return redirect(reverse('user:address'))
