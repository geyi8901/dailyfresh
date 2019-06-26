# dailyfresh
DailyFresh
天天生鲜：小型电商购物网站，基于Python3.x和Django1.8.2

项目尽量使用Django内部提供的API，后台管理为Django自带的管理系统django-admin。适合Django的小型实战项目。

功能简介：
商品浏览：商品的图片，售价，种类，简介以及库存等信息。
全文检索：支持对商品种类以及商品名称，简介的检索。
登录注册：用户的登录与注册。
用户中心：支持用户个人信息，收货地址等信息的更新，商品加入购物车，订单生成。
商品下单：在支付接口和企业资质的支持下可完成商品的下单功能，按照原子事务处理，下单异常则终止此次下单过程。
后台管理：支持后台管理功能，商品及用户信息的增加，更新与删除，可自定制样式与功能，日志，以及权限的管理和分配。

预览：
首页
index

登录
login

商品详情
goods

购物车
cart

安装：
依赖包安装
下载文件进入项目目录之后，使用pip安装依赖包

pip install -Ur plis**.txt

数据库配置
数据库默认使用Django项目生成时自动创建的小型数据库sqlite

也可自行配置连接使用MySQL

创建超级用户
终端下执行:

./python manage.py createsuperuser

然后输入相应的超级用户名以及密码，邮箱即可。

开始运行
终端下执行:

./python manage.py runserver

------------------------------------------
命令总结:
django项目启动: python manage.py runserver
redis服务启动:
redis客户端启动: redis-cli -h 192.168.0.108    或者本机直接 redis-cli
celery启动,在celery服务器上粘贴自己项目代码,然后项目目录中执行: celery -A celery_tasks.tasks worker -l info

