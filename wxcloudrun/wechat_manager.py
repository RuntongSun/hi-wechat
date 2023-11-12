import json

import requests


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
        response = requests.post(url, headers=headers, data=json.dumps(message_data, ensure_ascii=False).encode('utf-8'), verify=False)
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

    def upload_image_data(self, image_data):
        """
        上传图片数据到微信服务器

        :param image_data: 二进制图片数据
        :return: 微信服务器返回的media_id
        """
        url = f"https://api.weixin.qq.com/cgi-bin/media/upload?type=image"
        files = {'media': image_data}
        try:
            response = requests.post(url, files=files)
            response.raise_for_status()  # 如果发送失败，抛出异常
            result = response.json()
            return result.get('media_id')  # 返回media_id
        except requests.RequestException as e:
            print(f"上传图片失败: {e}")
            return None

    def upload_image_file(self, file):
        """
        上传文件到微信服务器

        :param file: 文件对象，比如从 request.files['media'] 获取的
        :return: 微信服务器返回的media_id
        """
        url = f"https://api.weixin.qq.com/cgi-bin/media/upload?type=image"
        files = {'media': (file.filename, file, 'image/jpeg')}
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

    def upload_voice_file(self, file):
        """
        上传语音文件到微信服务器

        :param file: 文件对象，比如从 request.files['media'] 获取的
        :return: 微信服务器返回的media_id
        """
        url = "https://api.weixin.qq.com/cgi-bin/media/upload?type=voice"
        files = {'media': (file.filename, file, 'audio/mpeg')}  # 假设语音文件为 mp3 格式
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

