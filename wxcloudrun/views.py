import json
import logging
import os
import time
from datetime import datetime

import requests
from flask import render_template, request, jsonify, abort
from mns.account import Account
from mns.mns_exception import MNSExceptionBase
from mns.queue import Message

# from mns.account import Account
# from mns.queue import Message

from run import app
from wxcloudrun.communication_manager import CommunicationManager
from wxcloudrun.dao import delete_counterbyid, query_counterbyid, insert_counter, update_counterbyid


from wxcloudrun.model import Counters
from wxcloudrun.response import make_succ_empty_response, make_succ_response, make_err_response
from wxcloudrun.wechat_manager import WeChatManager

WECHAT_MEDIA_URL = "http://api.weixin.qq.com/cgi-bin/media/get"  # 微信获取媒体文件的接口
communication_manager = CommunicationManager()
wechat_manager = WeChatManager()
my_account = Account(os.environ.get('MNS_ENDPOINT_PUBLIC'), os.environ.get('ALI_KEY_ID'), os.environ.get('ALI_ACCESS_KEY_SECRET'))


@app.route('/upload_voice', methods=['POST'])
def upload_voice():
    if 'media' not in request.files:
        return 'No media file part in the request', 400
    file = request.files['media']
    open_id = request.form.get("touser")
    if file and open_id:
        upload_result = wechat_manager.upload_voice_file(file)
        if 'error' in upload_result:
            return upload_result, 500
        else:
            media_id = upload_result['media_id']
            # 根据需求进行逻辑处理，将 media_id 和 open_id 一起处理
            response_data = {
                "upload_status": "File uploaded successfully",
                "media_id": media_id
            }
            return jsonify(response_data), 200
    else:
        return 'No valid media file or touser in the request', 400


@app.route('/upload_image', methods=['POST'])
def upload_image():
    if 'media' not in request.files:
        return 'No media file part in the request', 400
    file = request.files['media']
    open_id = request.form.get("touser")
    if file and open_id:
        upload_result = wechat_manager.upload_image_file(file)
        if 'error' in upload_result:
            return upload_result['error'], 500
        else:
            media_id = upload_result['media_id']
            # 根据需求进行逻辑处理，将 media_id 和 open_id 一起处理
            response_data = {
                "upload_status": "File uploaded successfully",
                "media_id": media_id
            }
            return jsonify(response_data), 200
    else:
        return 'No valid media file or touser in the request', 400


@app.route('/send_msg', methods=['POST'])
def send_msg():
    if request.content_type != 'application/json':
        return jsonify({"error": "Invalid content type. Expected application/json"}), 400

    feedback_data = request.get_json()
    if not feedback_data:
        return jsonify({"error": "Invalid JSON data"}), 400

    open_id = feedback_data.get("touser")
    msg_type = feedback_data.get("msgtype")

    if msg_type == "text":
        message = feedback_data.get("text")
        if not all([open_id, message]):
            return jsonify({"error": "Missing required fields"}), 400
        wechat_response = wechat_manager.send_text_message(open_id, message)

    elif msg_type in ["image", "voice"]:
        media_id = feedback_data.get("media_id")
        if not all([open_id, msg_type, media_id]):
            return jsonify({"error": "Missing required fields"}), 400

        try:
            if msg_type == "image":
                wechat_response = wechat_manager.send_image_message(open_id, media_id)
            elif msg_type == "voice":
                wechat_response = wechat_manager.send_voice_message(open_id, media_id)
        except Exception as e:
            return jsonify({"error": str(e), 'wechat_response': wechat_response}), 500

    else:
        return jsonify({"error": f"Unsupported msgtype: {msg_type}. Only 'text', 'image', or 'audio' are supported."}), 400

    return jsonify({"success": True}), 200


@app.route('/wechat', methods=['GET', 'POST'])
def wechat():
    if request.method == 'GET':
        return "success"

    elif request.method == 'POST':
        json_data = request.get_json()
        msg_type = json_data.get('MsgType')
        media_id = json_data.get('MediaId')
        user_id = json_data.get('FromUserName')  # 假设用户的微信ID在 'FromUserName' 字段中

        if msg_type in ['image', 'voice'] and media_id:
            # 用于处理图片和语音消息
            file_name = None
            if msg_type == 'image':
                file_name = wechat_manager.get_image(media_id)
            elif msg_type == 'voice':
                file_name = wechat_manager.get_voice(media_id)

            if file_name:
                json_data['OSSUrl'] = file_name

        # 将处理后的消息发送给阿里云
        # message = Message(action='FORWARD_MESSAGE', data=json_data)
        # response_from_aliyun = communication_manager.send_request(message)
        if msg_type == 'voice':
            send_to_queue("voice-recognition", json_data)

        return "success"

def send_to_queue(queue_name, message_body):
    my_queue = my_account.get_queue(queue_name)
    message = Message(message_body)
    try:
        send_msg = my_queue.send_message(message)
        print("Send message success. MessageBody:%s MessageID:%s" % (message_body, send_msg.message_id))
    except MNSExceptionBase as e:
        print("Send message fail! Exception:%s\n" % e)

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
