from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client
from django.conf import settings


class FDFSStorage(Storage):

    def __init__(self, client_conf=None, base_url=None):
        '''初始化'''
        if client_conf is None:
            client_conf = settings.FDFS_CLIENT_CONF
        self.client_conf = client_conf

        if base_url is None:
            base_url = settings.FDFS_URL
        self.base_url = base_url

    def _open(self, name,mode='rb'):
        pass
    def _save(self, name, content):
        #保存文件时使用
        #name保存的上传文件的名字
        #conteng包含你上传文件内容的File对象
        #创建一个Fdfs_client对象
        client = Fdfs_client('./utils/fdfs/client.conf')
        #上传文件
        res = client.upload_by_buffer(content.read())
        # dict
        # {
        #     'Group name': group_name,
        #     'Remote file_id': remote_file_id,
        #     'Status': 'Upload successed.',
        #     'Local file name': '',
        #     'Uploaded size': upload_size,
        #     'Storage IP': storage_ip
        # }
        if res.get('Status') != 'Upload successed.':
            #上传失败
            raise Exception('上传文件到fdfs失败')
        #获取返回文件的id
        filename = res.get('Remote file_id')
        return filename

    def exists(self, name):
        #django判断文件名是否可用
        return False

    def url(self, name):
        '''返回访问url文件路径'''
        return 'http://192.168.0.108:8888/'+name