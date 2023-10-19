import time
from datetime import datetime
from flask import render_template, request, jsonify
from run import app
from wxcloudrun.dao import delete_counterbyid, query_counterbyid, insert_counter, update_counterbyid
from wxcloudrun.model import Counters
from wxcloudrun.response import make_succ_empty_response, make_succ_response, make_err_response


@app.route('/wechat', methods=['GET', 'POST'])
def wechat():
    if request.method == 'GET':
        # 这里处理 GET 请求
        # 如果微信公众号有发送验证请求，可以在这里处理
        # 否则，您可以根据需要自定义处理
        return "success"  # 对微信服务器返回 "success" 或其他必要的响应

    elif request.method == 'POST':
        # 处理微信服务器的消息推送请求
        # 获取JSON数据
        json_data = request.get_json()

        # 提取所需字段
        to_user_name = json_data.get('ToUserName')
        from_user_name = json_data.get('FromUserName')

        # 构建响应消息
        response_data = {
            "ToUserName": from_user_name,  # 注意这里交换了ToUserName和FromUserName的值
            "FromUserName": to_user_name,
            "CreateTime": int(time.time()),
            "MsgType": "text",
            "Content": "ok"
        }

        return jsonify(response_data)

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
