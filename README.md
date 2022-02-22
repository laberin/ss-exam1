# health checker

본 과제는 Service Health Checker 시스템 및 API 구현을 목표로 합니다.

- 복잡한 요구사항이 특별히 명시되어 있지 않기 때문에 최대한 간단하게 구현했습니다. 실제로 사용할때는 루틴을 분리하여 테스트를 작성하거나 여러 방면에서 호출/실행될 수 있도록 모듈을 구성하는것이 좋을것 같습니다. 따로 어플리케이션의 dockerize등은 하지 않았습니다.

# 명시되어 있지 않은 제약사항

- 언어의 제약은 없는지?
  - (요구사항에 Celery가 적당해보여 Python으로 진행했습니다.)
- MQ의 종류는 정해져 있는지?
  - (Rabbitmq로 구성했습니다. 과제기 때문에 따로 managed service를 이용하지 않고 docker-compose로 구성했습니다.)
- error가 반환될 때 http status code는 어떻게 되는지?
  - (status code로 조건을 잡지 않고 메시지로 잡았습니다.)
- 각종 web ui를 접속하는 규칙
  - (특별히 nginx등의 웹서버 없이 각 port를 개방했습니다.)
- api 명세에서 `/history: 최근 10건의 응답 정보를 MQ에서 가져와 return합니다.` 부분의 10건은 MQ의 10건인지 storage까지 합쳐서의 10건인지 명확하지 않습니다.
  - 저장 상태에 상관없이 무조건 최근 10개가 나오도록 했습니다.

# 환경

- ec2 ubuntu
- rabbitmq
- s3
- python3.8
  - pika (for rabbitmq)
  - boto3 (for aws s3)
- node (for pm2)

# 구현

- 두개의 큐(status, history)를 이용했습니다. API의 `/history`와 `/status`에 응답하기 위해 최근 10개를 유지하는 큐(history)를 따로 유지 했습니다. history큐는 `{max-length: 10}`이 적용 되었습니다.
- bucket에는 `last`로 마지막 메시지들을 저장하고 다음 `last`의 내용이 들어올때 현재 `last`를 timestamp key로 변경합니다.

# 실행

### 프로젝트 클론

```
git clone <project url> <project>
cd <project>
```

## rabbitmq docker container 생성

```
docker-compose up -d
```

## rabbitmq virtualhost 생성, 권한 및 policy 설정

```bash
docker-compose exec rabbitmq /bin/bash
(in docker shell)
rabbitmqctl add_user test test
rabbitmqctl add_vhost celery
rabbitmqctl add_vhost logs
rabbitmqctl set_permissions -p "celery" "test" ".*" ".*" ".*"
rabbitmqctl set_permissions -p "logs" "test" ".*" ".*" ".*"
rabbitmqctl set_policy limit10 "^history$" '{"max-length":10}' --apply-to queues
```

### 파이썬 환경 셋업

```bash
python3 -m venv .ve
. .ve/bin/activate
pip install invoke
inv init
```

### 서버 실행 (개별 실행방법은 이렇습니다만, 여기 예제에서는 이렇게 실행하지 않습니다.)

```bash
# Celery
RMQ_HOST=localhost RMQ_USER=test RMQ_PASSWORD=test \
  AWS_ACCESS_KEY=<AWS_KEY> AWS_SECRET_KEY=<AWS_SECRET> \
  CHECK_INTERVAL=60.0 PUT_INTERVAL=600.0 \
  inv scheduler

# Status API
RMQ_HOST=localhost RMQ_USER=test RMQ_PASSWORD=test \
  AWS_ACCESS_KEY=<AWS_KEY> AWS_SECRET_KEY=<AWS_SECRET> \
  CHECK_INTERVAL=60.0 PUT_INTERVAL=600.0 \
  inv api
```

### Process Manager

```bash
npm i -g pm2
cd <project dir>
cat > ecosystem.config.js <<EOF
const env = {
  RMQ_HOST: "localhost",
  RMQ_USER: "test",
  RMQ_PASSWORD: "test",
  AWS_ACCESS_KEY: <AWS_KEY>,
  AWS_SECRET_KEY: <AWS_SECRET>,
  CHECK_INTERVAL: 60.0,
  PUT_INTERVAL: 600.0
};

module.exports = {
  apps: [
    {
      name: "api",
      cmd: "inv api",
      env,
    },
    {
      name: "scheduler",
      cmd: "inv scheduler",
      env,
    },
  ],
};

EOF
pm2 start ecosystem.config.js
pm2 ps
```
