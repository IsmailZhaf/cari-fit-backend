from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging

logger = logging.getLogger(__name__)

def send_notification(data: dict):
    try:
        channel = get_channel_layer()
        async_to_sync(channel.group_send)('notification', {
            "type": 'send_notification',
            "data": data,
        })
    except Exception as e:
        logger.warning(f"Failed to send notification: {e}")
        # Continue without failing the main process
        pass