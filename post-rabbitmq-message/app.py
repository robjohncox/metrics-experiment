import pika


USERNAME = 'admin'
PASSWORD = 'password'
RABBITMQ_HOST = 'localhost'
DEFAULT_EXCHANGE = ''
QUEUE_NAME = 'test'
MESSAGE = 'message'


def application(env, start_response):
    credentials = pika.PlainCredentials(
        username=USERNAME,
        password=PASSWORD)
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        credentials=credentials))
    channel = connection.channel()
    try:
        queue = channel.queue_declare(
            queue=QUEUE_NAME,
            exclusive=False,
            durable=True,
            auto_delete=False,
            arguments={})
        channel.confirm_delivery()
        channel.basic_publish(
            exchange=DEFAULT_EXCHANGE,
            routing_key=QUEUE_NAME,
            body=MESSAGE,
            properties=pika.BasicProperties(delivery_mode=2),
            mandatory=True)
        start_response('200 OK', [('Content-Type', 'text/html')])
        return ''
    except Exception as ex:
        start_response('500 INTERNAL SERVER ERROR', [('Content-Type', 'text/html')])
        return ex.message
    finally:
        connection.close()
