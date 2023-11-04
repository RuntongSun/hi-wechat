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
        response = requests.post(url, headers=headers, data=json.dumps(message_data, ensure_ascii=False).encode('utf-8'))
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
        response = requests.post(url, json=message_data)
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
