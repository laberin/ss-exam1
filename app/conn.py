import pika


class LogMQ:
    def __init__(self, host, user, password, virtual_host, queue):
        self.host = host
        self.user = user
        self.password = password
        self.virtual_host = virtual_host
        self.queue = queue
        
    def __enter__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                self.host,
                virtual_host=self.virtual_host,
                credentials=pika.PlainCredentials(self.user, self.password),
            )
        )
        channel = self.connection.channel()
        channel.queue_declare(queue=self.queue)
        return channel

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.connection.close()
