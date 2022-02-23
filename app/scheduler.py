import json
import time

import requests
from celery import Celery

from app import config, storage
from app.conn import LogMQ

broker_url = f"amqp://{config.RMQ_USER}:{config.RMQ_PASSWORD}@{config.RMQ_HOST}/celery"

# sample url
target_url = "https://ic8s2cma39.execute-api.ap-northeast-2.amazonaws.com/default/BackendAssignment"


def save_to_mq(data):
    """
    데이터를 MQ에 집어 넣습니다.
    """
    # status큐에 넣음 (s3로 보내기 전의 큐)
    with LogMQ(
        config.RMQ_HOST, config.RMQ_USER, config.RMQ_PASSWORD, "logs", "status"
    ) as channel:
        print(f"[*] save data to mq`logs`: {data}")
        channel.basic_publish(exchange="", routing_key="status", body=data)

    # history큐에 넣음 (api 응답용 큐)
    with LogMQ(
        config.RMQ_HOST, config.RMQ_USER, config.RMQ_PASSWORD, "logs", "history"
    ) as channel:
        print(f"[*] save data to mq `history`: {data}")
        channel.basic_publish(exchange="", routing_key="history", body=data)


def consume_once():
    """
    쌓인 메시지큐의 로그들을 로드하고 S3에 보낸 후 삭제합니다.
    """
    with LogMQ(
        config.RMQ_HOST, config.RMQ_USER, config.RMQ_PASSWORD, "logs", "status"
    ) as channel:
        messages = []

        while True:
            # 1초동안 추가 메시지가 없으면 loop를 종료 합니다.
            method_frame, header_frame, body = channel.basic_get(queue="status")
            if not method_frame:
                break
            # s3에 업로드 할 메시지 추가
            messages.append(json.loads(body.decode("utf-8")))
            # 메시지 acknowledge
            channel.basic_ack(method_frame.delivery_tag)

        print(f"[*] upload logs: {messages}")

        # s3
        put_storage.delay(messages)


def request(url):
    """
    HTTP 요청을 처리 하는 루틴입니다.
    """
    # default data
    data = dict(status="unknownError")
    # try
    try:
        rv = requests.get(url, timeout=3)
    except requests.exceptions.ConnectionError:
        print("error: cannot connect to the server.", url)
        data["timestamp"] = int(time.time())
        return data
    # parse the fetched data
    try:
        fetched_data = rv.json()
    except Exception:
        pass
    # expect
    if fetched_data.get("status") in ["running", "stopped", "paused"]:
        data = fetched_data
    # timestamp
    data["timestamp"] = int(time.time())
    return data


# CELERY APP
app = Celery("checkerapp", broker=broker_url)
app.conf.timezone = "UTC"


@app.task
def put_storage(messages):
    """
    s3로 전송합니다.
    """
    storage.put(json.dumps(messages))


@app.task
def queue(data):
    """
    로그를 메시지 큐에 쌓습니다.
    """
    save_to_mq(json.dumps(data))


@app.task
def checker():
    """
    주어진 url에 대해 GET요청을 하여 응답을 확인합니다.
    """
    queue.delay(request(target_url))


@app.task
def consumer():
    """
    메시지 큐에 쌓인 메시지를 로드해 S3등으로 보내는 루틴을 호출합니다.
    """
    consume_once()


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """
    cron을 등록합니다.
     - 1분에 한번씩 checker를 호출
     - 10분에 한번씩 consumer를 호출
    """
    sender.add_periodic_task(float(config.CHECK_INTERVAL), checker.s(), name="check apis every 1 minute")
    sender.add_periodic_task(float(config.PUT_INTERVAL), consumer.s(), name="load response data to s3")


if __name__ == "__main__":
    app.start()
