import requests
import logging
import yaml
from typing import Dict, Any


# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """加载配置文件"""
    with open(config_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)


# 从配置文件加载
try:
    app_config = load_config()
    FEISHU_BOT_KEYWORD = app_config.get('feishu', {}).get('keyword', 'GPUSentry')
    FEISHU_BOT_WEBHOOK_URL = app_config.get('feishu', {}).get('webhook_url', '')
except FileNotFoundError:
    # 如果配置文件不存在，使用默认值
    FEISHU_BOT_KEYWORD = 'GPUSentry'
    FEISHU_BOT_WEBHOOK_URL = ''


def send_feishu_message(message: str):
    """
    Sends a text message directly to the Feishu bot's Webhook.

    Args:
        message (str): The text message to send.

    Returns:
        bool: True if the message was sent successfully, False otherwise.
    """
    if FEISHU_BOT_KEYWORD not in message:
        message = f"【{FEISHU_BOT_KEYWORD}】{message}"

    headers = {"Content-Type": "application/json"}
    payload = {"msg_type": "text", "content": {"text": message}}

    logger.info(f"Sending message to Feishu: '{message}'")
    try:
        response = requests.post(
            FEISHU_BOT_WEBHOOK_URL, json=payload, headers=headers, timeout=10
        )
        response.raise_for_status()

        response_data = response.json()
        if response_data.get("code") == 0 or response_data.get("StatusCode") == 0:
            logger.info("Message sent to Feishu successfully.")
            return True
        else:
            logger.error(f"Failed to send message to Feishu. Response: {response_data}")
            return False

    except requests.exceptions.RequestException as e:
        logger.error(f"An error occurred while sending request to Feishu: {e}")
        return False