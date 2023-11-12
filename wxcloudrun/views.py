import json
import logging
import os
import time
from datetime import datetime

import requests
from flask import render_template, request, jsonify
from mns.account import Account
from mns.queue import Message

from run import app
from wxcloudrun.communication_manager import CommunicationManager
from wxcloudrun.dao import delete_counterbyid, query_counterbyid, insert_counter, update_counterbyid

from wxcloudrun.model import Counters
from wxcloudrun.response import make_succ_empty_response, make_succ_response, make_err_response
from wxcloudrun.wechat_manager import WeChatManager



WECHAT_MEDIA_URL = "http://api.weixin.qq.com/cgi-bin/media/get"  # 微信获取媒体文件的接口
communication_manager = CommunicationManager()
wechat_manager = WeChatManager()

# 阿里云MNS的凭据和端点信息
end_point = "http://1647939067643291.mns.cn-shanghai.aliyuncs.com"
queue_name = "wechat-msg"  # 你的MNS队列名称
# 初始化MNS账户和队列
mns_account = Account("http://1647939067643291.mns.cn-shanghai.aliyuncs.com", os.environ.get("ALI_KEY_ID"), os.environ.get("ALI_ACCESS_KEY_SECRET"))
mns_queue = mns_account.get_queue(queue_name)

@app.route('/from-aliyun', methods=['POST'])
def receive_feedback():
    open_id = None
    msg_type = None
    message = None
    media_id = None
    error_details = None  # Ensure this variable is in scope
    file_upload_success = False
    file_retrieved = False
    file = None

    if request.content_type == 'application/json':
        feedback_data = request.get_json()
        if not feedback_data:
            return jsonify({"error": "No data received"}), 400
        open_id = feedback_data.get("touser")
        msg_type = feedback_data.get("msgtype")
        if msg_type == "text":
            message = feedback_data.get("text", {}).get("content")
        elif msg_type == "image":
            media_id = feedback_data.get("image", {}).get("media_id")
        elif msg_type == "voice":
            media_id = feedback_data.get("voice", {}).get("media_id")
    else:  # handle form data or file uploads
        open_id = request.form.get("touser")
        msg_type = request.form.get("msgtype")
        if 'media' in request.files:
            file_retrieved = True
            file = request.files['media']
            if msg_type == "image":
                upload_result = wechat_manager.upload_image_file(file)
            elif msg_type == "voice":
                upload_result = wechat_manager.upload_voice_file(file)
            else:
                return jsonify({"error": "Unsupported message type"}), 400

            if 'error' in upload_result:
                error_details = upload_result.get('details', 'No details provided')
            else:
                media_id = upload_result.get('media_id')
                file_upload_success = True

    # Verify if necessary data is received
    if not open_id or (msg_type in ["text", "voice", "image"] and not media_id):
        response_data = {
            "error": "Invalid data received",
            "file_retrieved": file_retrieved,
            "file_upload_success": file_upload_success,
            "media_id": media_id,
            "error_details": error_details
        }

        if file and not media_id:
            response_data["error"] += " - File was retrieved but upload failed"
        return jsonify(response_data), 400

    # Send message
    try:
        if msg_type == "text":
            wechat_response = wechat_manager.send_text_message(open_id, message)
        elif msg_type == "image":
            wechat_response = wechat_manager.send_image_message(open_id, media_id)
        elif msg_type == "voice":
            wechat_response = wechat_manager.send_voice_message(open_id, media_id)
        else:
            return jsonify({"error": "Unsupported message type"}), 400

        if wechat_response.get("errcode") != 0:
            return jsonify({"error": "Failed to send WeChat message", "details": wechat_response}), 500

    except Exception as e:
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500

    return jsonify({"success": True, "media_id": media_id}), 200


@app.route('/wechat', methods=['GET', 'POST'])
def wechat():
    if request.method == 'GET':
        return "success"

    elif request.method == 'POST':
        json_data = request.get_json()
        # message = Message(action='FORWARD_MESSAGE', data=json_data)
        #
        # response_from_aliyun = communication_manager.send_request(message)
        try:
            # message_body = json_data  # 获取原始消息内容，这已经是一个字符串了
            send_to_logger(json_data)
            message = Message(message_body=json_data)  # 直接使用字符串，不需要编码为字节
            re_msg = mns_queue.send_message(message)
            print("Message sent to MNS. Message ID: ", re_msg.message_id)
            send_to_logger(re_msg)
        except Exception as e:
            print("Failed to send message to MNS:", e)
            send_to_logger(e)

        return "success"
        # if response_from_aliyun:
        # response_str = json.dumps(response_from_aliyun, ensure_ascii=False)
        # wechat_response = wechat_manager.send_text_message("oxi2qjn7b7rtE2rjT6TudqzqEXDs", "ok")
        # message = Message(action='WECHAT_BACK', data=wechat_response)
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

def send_to_logger(json_data):
    headers = {
            'Content-Type': 'application/json; charset=UTF-8'
        }
    response = requests.post("https://g362909r31.goho.co/logger", json=json_data, headers=headers)

    if response.status_code == 200:
        print('ok')
    else:
        print('no')

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
