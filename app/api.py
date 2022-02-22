import json

from flask import Flask, jsonify

from app import config, storage
from app.conn import LogMQ

app = Flask(__name__)


def get_messages(queue_name):
    messages = []
    with LogMQ(
        config.RMQ_HOST, config.RMQ_USER, config.RMQ_PASSWORD, "logs", queue_name
    ) as channel:
        while True:
            method_frame, header_frame, body = channel.basic_get(
                queue_name, auto_ack=False
            )
            if method_frame:
                messages.append(json.loads(body.decode("utf-8")))
            else:
                break
    return messages


@app.get("/history")
def history():
    # 현재 history에 들어있는 데이터 가져오기
    return jsonify(get_messages("history"))


@app.get("/status")
def status():
    # 현재 history에 들어있는 데이터 가져오기
    t = get_messages("history")

    # 마지막 요소 리턴
    return jsonify(t.pop())


@app.get("/recent")
def recent():
    # 마지막 저장분 + 현재 status에 들어있는 데이터 가져오기
    messages = storage.get_latest() + get_messages("status")

    # 합쳐서 리턴
    return jsonify(messages)
