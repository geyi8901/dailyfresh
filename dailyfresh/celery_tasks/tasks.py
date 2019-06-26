from celery import Celery
from django.conf import settings
from django.core.mail import send_mail
import time
import os
import django


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
