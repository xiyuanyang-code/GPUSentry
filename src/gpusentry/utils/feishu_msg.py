import requests
import logging
import base64
import tempfile
import os
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
            logger.info("Feishu auto initing...")
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


def send_feishu_post_message(title: str, content: str, images: list = None, auto_init: bool = True) -> bool:
    """
    Sends a post (rich text) message with optional images to the Feishu bot.

    Args:
        title: Title of the post message
        content: Text content to send
        images: List of base64 encoded image data to send
        auto_init: Whether to auto initialize config

    Returns:
        bool: True if the message was sent successfully, False otherwise.
    """
    # Check if config is initialized
    if _config is None:
        if not auto_init:
            logger.error("Feishu configuration not initialized")
            return False
        else:
            logger.info("Feishu auto initing...")
            config = Config()
            initialize_feishu_config(config=config)

    # Get configuration values
    keyword = _config.feishu_keyword
    webhook_url = _config.feishu_webhook_url

    # Check if webhook URL is configured
    if not webhook_url:
        logger.warning("Feishu webhook URL not configured")
        return False

    # Prepare content blocks
    content_blocks = []
    
    # Add the main text content
    content_blocks.append([{
        "tag": "text",
        "text": content
    }])
    
    # Add images if provided
    if images:
        for img_data in images:
            # Save image data to temporary file
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                image_path = temp_file.name
                with open(image_path, 'wb') as f:
                    f.write(base64.b64decode(img_data))
            
            try:
                # For webhook-based bots, we need to upload the image first
                # But for now we'll just note that this requires a more complex implementation
                logger.info(f"Image data received for sending, but webhook bots may not support direct image upload")
                # Add a placeholder for the image
                content_blocks.append([{
                    "tag": "text",
                    "text": "[Image attachment - requires direct upload to Feishu server]"
                }])
            finally:
                # Clean up temporary file
                try:
                    os.remove(image_path)
                except OSError:
                    pass  # Ignore cleanup errors
    
    # Create the post message payload
    headers = {"Content-Type": "application/json"}
    payload = {
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": f"【{keyword}】{title}",
                    "content": content_blocks
                }
            }
        }
    }

    logger.info(f"Sending post message to Feishu with {len(images) if images else 0} images")
    try:
        response = requests.post(webhook_url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()

        response_data = response.json()
        if response_data.get("code") == 0 or response_data.get("StatusCode") == 0:
            logger.info("Post message sent to Feishu successfully.")
            return True
        else:
            logger.error(f"Failed to send post message to Feishu. Response: {response_data}")
            return False

    except requests.exceptions.RequestException as e:
        logger.error(f"An error occurred while sending post message to Feishu: {e}")
        return False


def send_feishu_message_with_images(text_message: str, image_list: list = None, auto_init: bool = True) -> bool:
    """
    Sends a text message with optional images to the Feishu bot.

    Args:
        text_message: Text message to send
        image_list: List of base64 encoded image data to send
        auto_init: Whether to auto initialize config

    Returns:
        bool: True if the message was sent successfully, False otherwise.
    """
    if not image_list:
        # If no images, send as regular text message
        return send_feishu_message(text_message, auto_init=True)
    
    title = "GPU Usage Report"
    return send_feishu_post_message(title, text_message, image_list, auto_init)

if __name__ == "__main__":
    config = Config()
    initialize_feishu_config(config=config)
    send_feishu_message("Hello World")