import base64
import hmac
import os
from datetime import datetime
from hashlib import sha1

import requests


class OssRestful:
    def __init__(self):
        self.oss_access_key_id = os.environ.get('ALI_KEY_ID')
        self.oss_access_key_secret = os.environ.get('ALI_ACCESS_KEY_SECRET')
        self.oss_bucket_name = os.environ.get('OSS_BUCKET_NAME')
        self.oss_endpoint = os.environ.get('OSS_ENDPOINT_PUBLIC')

    def download_from_oss(self, file_name):
        date_str = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
        signature = self.create_signature_for_download(file_name, date_str)

        headers = {
            'Authorization': f'OSS {self.oss_access_key_id}:{signature}',
            'Date': date_str
        }

        oss_url = f'http://{self.oss_bucket_name}.{self.oss_endpoint}/{file_name}'
        response = requests.get(oss_url, headers=headers)
        if response.status_code == 200:
            print("File downloaded successfully from OSS.")
            return response.content
        else:
            print("Failed to download file from OSS.")
            return None

    def create_signature_for_download(self, file_name, date_str):
        # 签名字符串
        signature_string = f"GET\n\n\n{date_str}\n/{self.oss_bucket_name}/{file_name}"
        # 使用HMAC-SHA1算法生成签名
        signature = base64.b64encode(
            hmac.new(self.oss_access_key_secret.encode(), signature_string.encode(), sha1).digest()).decode()
        return signature

    def upload_to_oss(self, file_name, file_content):

        # 创建签名
        date_str = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
        signature = self.create_signature(file_name, date_str)

        headers = {
            'Authorization': f'OSS {self.oss_access_key_id}:{signature}',
            'Date': date_str,
            'Content-Type': 'audio/mpeg'
        }

        oss_url = f'http://{self.oss_bucket_name}.{self.oss_endpoint}/{file_name}'
        response = requests.put(oss_url, data=file_content, headers=headers, verify=False)
        if response.status_code == 200:
            print("File uploaded successfully to OSS.")
        else:
            print("Failed to upload file to OSS.")

    def create_signature(self, file_name, date_str):
        # 签名字符串
        signature_string = f"PUT\n\naudio/mpeg\n{date_str}\n/{self.oss_bucket_name}/{file_name}"
        # 使用HMAC-SHA1算法生成签名
        signature = base64.b64encode(
            hmac.new(self.oss_access_key_secret.encode(), signature_string.encode(), sha1).digest()).decode()
        return signature
