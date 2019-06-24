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
    subject = '今天的信息，请查收'
    message = '邮件正文，欢迎您关注我们,很高兴，您能收到这封邮件。谢谢'
    
    sender = settings.EMAIL_FROM
    #html_message = '<h1>%s，欢迎您成为天天生鲜注册会员！</h1><h1>请点击以下链接激活您的账户</h1><br/><a href="http:127.0.0.1:8000/users/active/%s">http:127.0.0.1:8000/users/active/%s</a>' % (
   # username, token, token)
    recvier = [to_email]
    send_mail(subject, message, sender, recvier)
    time.sleep(5)