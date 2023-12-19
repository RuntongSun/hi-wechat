import json
import mimetypes
import os
import requests

from wxcloudrun.oss_restful import OssRestful

oss_restful = OssRestful()

class WeChatManager:
    def send_text_message(self, open_id, message):
        url = f"http://api.weixin.qq.com/cgi-bin/message/custom/send"
        headers = {'Content-Type': 'application/json'}
        message_data = {
            "touser": open_id,
            "msgtype": "text",
            "text": {
                "content": message
            }
        }
        # json_message = message_data.dumps(message, ensure_ascii=False)
        # response = requests.post(url, headers=headers,
        #                          json=message_data, verify=False)
        response = requests.post(url, headers=headers,
                                 data=json.dumps(message_data, ensure_ascii=False).encode('utf-8'), verify=False)
        return response.json()  # 这个调用将返回微信API的响应，您可能想要检查这个来确保消息已发送

    def send_image_message(self, user_id, media_id):
        url = f"https://api.weixin.qq.com/cgi-bin/message/custom/send"
        message_data = {
            "touser": user_id,
            "msgtype": "image",
            "image": {
                "media_id": media_id
            }
        }
        response = requests.post(url, json=message_data, verify=False)
        return response.json()

    def send_voice_message(self, user_id, media_id):
        """
        发送语音消息

        :param user_id: 用户的 OpenID
        :param media_id: 通过微信上传音频文件得到的 media_id
        :return: 微信服务器返回的响应
        """
        url = "https://api.weixin.qq.com/cgi-bin/message/custom/send"
        message_data = {
            "touser": user_id,
            "msgtype": "voice",
            "voice": {
                "media_id": media_id
            }
        }
        response = requests.post(url, json=message_data, verify=False)
        return response.json()

    def upload_image_from_oss(self, file_path):
        """
        从OSS下载图片并上传到微信服务器

        :param oss_restful: OssRestful的实例
        :param file_path: OSS上的文件路径
        :return: 微信服务器返回的media_id或错误信息
        """
        try:
            # 从OSS下载图片
            image_content = oss_restful.download_from_oss(file_path)
            if image_content is None:
                return {'error': 'Failed to download image from OSS'}

            # 猜测图片类型
            file_type = mimetypes.guess_type(file_path)[0] or 'image/jpeg'
            file_name = file_path.split('/')[-1]

            # 准备上传到微信服务器
            upload_url = f"https://api.weixin.qq.com/cgi-bin/media/upload?type=image"
            files = {'media': (file_name, image_content, file_type)}
            upload_response = requests.post(upload_url, files=files, verify=False)
            upload_response.raise_for_status()  # 如果上传失败，抛出异常
            result = upload_response.json()
            media_id = result.get('media_id')

            if media_id:
                return {'media_id': media_id}
            else:
                # 返回一个包含错误信息的字典
                return {'error': 'Media ID not found in response', 'details': result}
        except requests.RequestException as e:
            return {'error': 'Operation failed', 'details': str(e)}

    def upload_image_file(self, file):
        """
        上传文件到微信服务器

        :param file: 文件对象，比如从 request.files['media'] 获取的
        :return: 微信服务器返回的media_id
        """
        url = f"https://api.weixin.qq.com/cgi-bin/media/upload?type=image"
        file_type = mimetypes.guess_type(file.filename)[0]  # 猜测真实文件类型
        files = {'media': (file.filename, file, file_type)}  # 使用真实文件类型
        try:
            response = requests.post(url, files=files, verify=False)
            response.raise_for_status()  # 如果发送失败，抛出异常
            result = response.json()
            media_id = result.get('media_id')
            if media_id:
                return {'media_id': media_id}
            else:
                # 返回一个包含错误信息的字典
                return {'error': 'Media ID not found in response', 'details': result}
        except requests.RequestException as e:
            return {'error': 'Upload failed', 'details': str(e)}

    def upload_voice_from_oss(self, file_path):
        """
        从OSS下载语音文件并上传到微信服务器

        :param file_path: OSS上的文件路径
        :return: 微信服务器返回的media_id或错误信息
        """
        try:
            # 从OSS下载语音文件
            voice_content = oss_restful.download_from_oss(file_path)
            if voice_content is None:
                return {'error': 'Failed to download voice from OSS'}

            # 猜测语音文件类型
            file_type = mimetypes.guess_type(file_path)[0] or 'audio/mpeg'
            file_name = file_path.split('/')[-1]

            # 准备上传到微信服务器
            upload_url = f"https://api.weixin.qq.com/cgi-bin/media/upload?type=voice"
            files = {'media': (file_name, voice_content, file_type)}
            upload_response = requests.post(upload_url, files=files, verify=False)
            upload_response.raise_for_status()  # 如果上传失败，抛出异常
            result = upload_response.json()
            media_id = result.get('media_id')

            if media_id:
                return {'media_id': media_id}
            else:
                # 返回一个包含错误信息的字典
                return {'error': 'Media ID not found in response', 'details': result}
        except requests.RequestException as e:
            return {'error': 'Operation failed', 'details': str(e)}

    def upload_voice_file(self, file):
        """
        上传语音文件到微信服务器

        :param file: 文件对象，比如从 request.files['media'] 获取的
        :return: 微信服务器返回的media_id
        """
        allowed_extensions = ['.mp3', '.wav', '.ogg']  # 添加更多允许的声音文件后缀
        file_extension = os.path.splitext(file.filename)[1]

        if file_extension not in allowed_extensions:
            return {'error': '无效的文件类型:' + file_extension}

        url = "https://api.weixin.qq.com/cgi-bin/media/upload?type=voice"
        files = {'media': (file.filename, file, file.mimetype)}

        try:
            response = requests.post(url, files=files, verify=False)
            response.raise_for_status()  # 如果发送失败，抛出异常
            result = response.json()
            media_id = result.get('media_id')

            if media_id:
                return {'media_id': media_id}
            else:
                # 返回一个包含错误信息的字典
                return {'error': '响应中未找到media_id', 'details': result}
        except requests.RequestException as e:
            return {'error': '上传失败', 'details': str(e)}

    def get_image(self, media_id, wechat_id):
        image_url = f"https://api.weixin.qq.com/cgi-bin/media/get?media_id={media_id}"
        response = requests.get(image_url, stream=True, verify=False)
        if response.status_code == 200:
            file_content = response.content
            # 生成一个基于wechat_id的唯一文件名
            file_name = f"wechat_users/{wechat_id}/images/{media_id}.jpg"
            # 上传到阿里云OSS
            oss_restful.upload_to_oss(file_name, file_content)
            return file_name
        else:
            return None
    # def get_image(self, media_id, wechat_id):
    #     voice_url = f"https://api.weixin.qq.com/cgi-bin/media/get?media_id={media_id}"
    #     response = requests.get(voice_url, stream=True, verify=False)
    #     if response.status_code == 200:
    #         file_content = response.content
    #         # 生成一个唯一的文件名
    #         file_name = f"voices/{media_id}.mp3"
    #         # 上传到阿里云OSS
    #         oss_restful.upload_to_oss(file_name, file_name)
    #         return file_name
    #     else:
    #         return None

    def get_voice(self, media_id, wechat_id):
        voice_url = f"https://api.weixin.qq.com/cgi-bin/media/get?media_id={media_id}"
        response = requests.get(voice_url, stream=True, verify=False)
        if response.status_code == 200:
            file_content = response.content
            # 生成一个基于wechat_id的唯一文件名
            file_name = f"wechat_users/{wechat_id}/voices/{media_id}.amr"
            # 上传到阿里云OSS
            oss_restful.upload_to_oss(file_name, file_content)
            return file_name
        else:
            return None

    # def get_voice(self, media_id, wechat_id):
    #     voice_url = f"https://api.weixin.qq.com/cgi-bin/media/get?media_id={media_id}"
    #     response = requests.get(voice_url, stream=True, verify=False)
    #     if response.status_code == 200:
    #         file_content = response.content
    #         # 生成一个唯一的文件名
    #         file_name = f"voices/{media_id}.amr"
    #         # 上传到阿里云OSS
    #         oss_restful.upload_to_oss(file_name, file_content)
    #         return file_name
    #     else:
    #         return None
