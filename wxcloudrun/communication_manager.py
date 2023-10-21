import requests

from wxcloudrun.message import Message


class CommunicationManager:
    # SERVER_URL = 'https://g362909r31.goho.co/from-wechat'
    SERVER_URL = 'http://hi-talk-to-tony-ufmxxxhouy.cn-hongkong.fcapp.run/'

    def send_request(self, message: Message):
        """
        发送请求到服务器。

        :param message: Message对象，包含请求的目的和数据。
        :return: 服务器的响应。
        """
        # 使用message对象的数据构建请求体
        request_body = message.construct_payload()

        # 发送请求
        try:
            response = requests.post(self.SERVER_URL, json=request_body)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"请求发送失败: {e}")
            return None

        return response.json()