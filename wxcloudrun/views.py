import json
import logging
import os
import time
from datetime import datetime

import requests
from flask import render_template, request, jsonify, abort
# from mns.account import Account
# from mns.queue import Message

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


@app.route('/send_text', methods=['POST'])
def send_text():
    if request.content_type == 'application/json':
        feedback_data = request.get_json()
        open_id = feedback_data.get("touser")
        msg_type = feedback_data.get("msgtype")
        message = feedback_data.get("text", {}).get("content")
        wechat_response = wechat_manager.send_text_message(open_id, message)
        return jsonify({"success": True}), 200


@app.route('/send_image', methods=['POST'])
def send_image():
    if request.content_type == 'application/json':
        feedback_data = request.get_json()
        if not feedback_data:
            return jsonify({"error": "Invalid JSON data"}), 400

        open_id = feedback_data.get("touser")
        msg_type = feedback_data.get("msgtype")
        media_id = feedback_data.get("media_id")

        if not all([open_id, msg_type, media_id]):
            return jsonify({"error": "Missing required fields"}), 400

        try:
            wechat_response = wechat_manager.send_image_message(open_id, media_id)
        except Exception as e:
            return jsonify({"error": str(e), 'wechat_response': wechat_response}), 500

        return jsonify({"success": True}), 200

    abort(415)  # Unsupported Media Type


@app.route('/send_audio', methods=['POST'])
def send_audio():
    if request.content_type == 'application/json':
        # feedback_data = request.get_json()
        # if not feedback_data:
        #     return jsonify({"error": "Invalid JSON data"}), 400
        #
        # open_id = feedback_data.get("touser")
        # msg_type = feedback_data.get("msgtype")
        # media_id = feedback_data.get("media_id")
        #
        # if not all([open_id, msg_type, media_id]):
        #     return jsonify({"error": "Missing required fields"}), 400
        #
        # try:
        #     wechat_response = wechat_manager.send_voice_message(open_id, media_id)
        # except Exception as e:
        #     return jsonify({"error": str(e), 'wechat_response': wechat_response}), 500

        return jsonify({"success": 'True'}), 200

    abort(415)  # Unsupported Media Type


@app.route('/wechat', methods=['GET', 'POST'])
def wechat():
    if request.method == 'GET':
        return "success"

    elif request.method == 'POST':
        json_data = request.get_json()
        message = Message(action='FORWARD_MESSAGE', data=json_data)

        response_from_aliyun = communication_manager.send_request(message)

        return "success"


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
