from .methods import send_notification
from huey.contrib.djhuey import task

@task()
def task_send_notification(message):
    send_notification(message)