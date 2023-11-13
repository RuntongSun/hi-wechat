import os

import oss2

class OSSManager:
    def __init__(self):
        # 初始化auth对象和bucket对象
        endpoint = os.environ.get("OSS_ENDPOINT_PUBLIC")
        self.auth = oss2.Auth(os.environ.get("ALI_KEY_ID"), os.environ.get("ALI_ACCESS_KEY_SECRET"))
        self.bucket = oss2.Bucket(self.auth, endpoint, os.environ.get("OSS_BUCKET_NAME"))

    def upload_file(self, file_name, data):
        # 上传文件
        result = self.bucket.put_object(file_name, data)
        return result

    def download_file(self, key):
        # 下载文件
        result = self.bucket.get_object_to_file(key)
        return result

    def download_file_content(self, key):
        # 下载文件内容
        oss_object = self.bucket.get_object(key)
        return oss_object.read()

    def generate_presigned_url(self, key, expiration=3600):
        # 生成带签名的URL
        # expiration 时间为秒，例如3600秒，表示生成的签名URL有效期为1小时
        signed_url = self.bucket.sign_url('GET', key, expiration)
        return signed_url

    # ... 添加其他需要的方法，例如删除文件、列出bucket内容等 ...
