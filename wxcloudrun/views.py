import json
import time
from datetime import datetime

import requests
from flask import render_template, request, jsonify
from run import app
from wxcloudrun.communication_manager import CommunicationManager
from wxcloudrun.dao import delete_counterbyid, query_counterbyid, insert_counter, update_counterbyid
from wxcloudrun.message import Message
from wxcloudrun.model import Counters
from wxcloudrun.response import make_succ_empty_response, make_succ_response, make_err_response
from wxcloudrun.wechat_manager import WeChatManager

WECHAT_MEDIA_URL = "http://api.weixin.qq.com/cgi-bin/media/get"  # 微信获取媒体文件的接口
communication_manager = CommunicationManager()
wechat_manager = WeChatManager()

@app.route('/wechat', methods=['GET', 'POST'])
def wechat():
    if request.method == 'GET':
        return "success"

    elif request.method == 'POST':
        json_data = request.get_json()
        message = Message(action='FORWARD_MESSAGE', data=json_data)
        return "success"

        response_from_aliyun = communication_manager.send_request(message)
        if response_from_aliyun:
            response_str = json.dumps(response_from_aliyun, ensure_ascii=False)
            wechat_manager.send_text_message("oxi2qjn7b7rtE2rjT6TudqzqEXDs", "ok")
        # msg_type = json_data.get('MsgType')
        #
        # if msg_type in ['image', 'voice']:
        #     media_id = json_data.get('MediaId')  # 获取媒体文件ID
        #     media_url = f"{WECHAT_MEDIA_URL}?media_id={media_id}"
        #
        #     # 获取实际的媒体内容
        #     media_response = requests.get(media_url, stream=True)
        #     if media_response.status_code == 200:
        #         files = {'media': media_response.content}
        #         # 将媒体文件以及原始的JSON数据一起转发到阿里云服务器
        #         response_from_aliyun = requests.post(ALIYUN_SERVER_URL, files=files,
        #                                              data={'json_data': jsonify(json_data).data})
        #
        #         if response_from_aliyun.status_code == 200:
        #             return response_from_aliyun.content, 200, {'ContentType': 'application/json'}
        #         else:
        #             # 错误处理
        #             return "Error", 500
        #     else:
        #         return "Error", 500  # 媒体文件获取失败处理
        # else:
        #
        #     headers = {
        #         'Content-Type': 'application/json; charset=UTF-8'
        #     }
        #     response_from_aliyun = requests.post(ALIYUN_SERVER_URL, json=json_data, headers=headers)
        #
        #     if response_from_aliyun.status_code == 200:
        #         response_data = response_from_aliyun.json()
        #         response_str = json.dumps(response_data, ensure_ascii=False)
        #         return response_str, 200, {'ContentType': 'application/json'}
        #     else:
        #         return "Error", 500

@app.route('/')
def index():
    """
    :return: 返回index页面
    """
    return render_template('index.html')


@app.route('/api/count', methods=['POST'])
def count():
    """
    :return:计数结果/清除结果
    """

    # 获取请求体参数
    params = request.get_json()

    # 检查action参数
    if 'action' not in params:
        return make_err_response('缺少action参数')

    # 按照不同的action的值，进行不同的操作
    action = params['action']

    # 执行自增操作
    if action == 'inc':
        counter = query_counterbyid(1)
        if counter is None:
            counter = Counters()
            counter.id = 1
            counter.count = 1
            counter.created_at = datetime.now()
            counter.updated_at = datetime.now()
            insert_counter(counter)
        else:
            counter.id = 1
            counter.count += 1
            counter.updated_at = datetime.now()
            update_counterbyid(counter)
        return make_succ_response(counter.count)

    # 执行清0操作
    elif action == 'clear':
        delete_counterbyid(1)
        return make_succ_empty_response()

    # action参数错误
    else:
        return make_err_response('action参数错误')


@app.route('/api/count', methods=['GET'])
def get_count():
    """
    :return: 计数的值
    """
    counter = Counters.query.filter(Counters.id == 1).first()
    return make_succ_response(0) if counter is None else make_succ_response(counter.count)
