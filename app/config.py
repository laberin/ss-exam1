import os

RMQ_HOST = os.environ.get("RMQ_HOST")
RMQ_USER = os.environ.get("RMQ_USER")
RMQ_PASSWORD = os.environ.get("RMQ_PASSWORD")

BUCKET = "ss-exam-status-logs"
AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY')
AWS_SECRET_KEY = os.environ.get('AWS_SECRET_KEY')

CHECK_INTERVAL = os.environ.get('CHECK_INTERVAL')
PUT_INTERVAL = os.environ.get('PUT_INTERVAL')