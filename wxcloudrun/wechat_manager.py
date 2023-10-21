import requests


class WeChatManager:
    def send_text_message(self, open_id, message):
        access_token = self.get_access_token()  # 确保您有一个有效的token
        url = f"http://api.weixin.qq.com/cgi-bin/message/custom/send"
        message_data = {
            "touser": open_id,
            "msgtype": "text",
            "text": {
                "content": message
            }
        }
        response = requests.post(url, json=message_data)
        return response.json()  # 这个调用将返回微信API的响应，您可能想要检查这个来确保消息已发送