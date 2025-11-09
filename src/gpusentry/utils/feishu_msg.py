import requests
import logging
from typing import Optional
from .configs import Config
from .logger import app_logger

# Global config instance
_config: Optional[Config] = None
logger = app_logger


def initialize_feishu_config(config: Config):
    """
    Initialize the Feishu configuration.

    Args:
        config: Configuration object
    """
    global _config
    _config = config


def send_feishu_message(message: str, auto_init: bool = True) -> bool:
    """
    Sends a text message directly to the Feishu bot's Webhook.

    Args:
        message (str): The text message to send.

    Returns:
        bool: True if the message was sent successfully, False otherwise.
    """
    # Check if config is initialized
    if _config is None:
        if not auto_init:
            logger.error("Feishu configuration not initialized")
            return False
        else:
            logger.warning("Feishu auto initing...")
            config = Config()
            initialize_feishu_config(config=config)

    # Get configuration values
    keyword = _config.feishu_keyword
    webhook_url = _config.feishu_webhook_url

    # Check if webhook URL is configured
    if not webhook_url:
        logger.warning("Feishu webhook URL not configured")
        return False

    if keyword not in message:
        message = f"【{keyword}】{message}"

    headers = {"Content-Type": "application/json"}
    payload = {"msg_type": "text", "content": {"text": message}}

    logger.info(f"Sending message to Feishu: '{message}'")
    try:
        response = requests.post(webhook_url, json=payload, headers=headers, timeout=10)
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


if __name__ == "__main__":
    config = Config()
    initialize_feishu_config(config=config)
    send_feishu_message("Hello World")