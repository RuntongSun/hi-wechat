
class Message:
    def __init__(self, action, data):
        self.action = action
        self.data = data

    def construct_payload(self):
        """
        构建请求的数据负载。

        :return: 用于请求的数据字典。
        """
        return {
            "action": self.action,
            "data": self.data
        }

class NewMessage(Message):
    def __init__(self, message_json):
        super().__init__("NEW_MESSAGE", message_json)
    # 如果需要，你可以为特定的消息类型添加更多定制的方法和属性
