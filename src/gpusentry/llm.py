"""Module for interacting with LLMs to generate intelligent summaries."""

import os
from typing import Dict, Any
from openai import OpenAI
from dotenv import load_dotenv
from .utils.logger import app_logger
from .utils.configs import Config


class LLMAnalyzer:
    """Analyzer that uses LLM to generate intelligent summaries."""

    def __init__(self, config: Config):
        """Initialize the LLM analyzer.

        Args:
            config: Configuration object
        """
        self.config = config
        self.logger = app_logger

        # Load environment variables
        load_dotenv()

        # Get API key and base URL from config or environment variables
        self.api_key = config.get("LLM.OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.base_url = config.get("LLM.BASE_URL") or os.getenv("BASE_URL")
        self.model_name = config.get("LLM.model_name")

        # Initialize OpenAI client if API key is available
        self.client = None
        if self.api_key:
            try:
                if self.base_url:
                    self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
                else:
                    self.client = OpenAI(api_key=self.api_key)
            except Exception as e:
                self.logger.error(f"Failed to initialize OpenAI client: {e}")
        else:
            self.logger.warning(
                "OpenAI API key not found. LLM features will be disabled."
            )

    def generate_intelligent_summary(
        self, usage_summary: Dict[str, Any], period: str = "daily"
    ) -> str:
        """Generate an intelligent summary using LLM.

        Args:
            usage_summary: Dictionary containing usage statistics
            period: Time period for the summary (daily, weekly, monthly)

        Returns:
            Generated summary text
        """
        if not self.client:
            return "LLM features are disabled due to missing API key."

        # Create a prompt for the LLM
        prompt = self._create_summary_prompt(usage_summary, period)

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that analyzes GPU usage data and provides insightful summaries.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=300,
                temperature=0.7,
            )

            summary = response.choices[0].message.content
            self.logger.info("Successfully generated intelligent summary using LLM")
            return summary

        except Exception as e:
            self.logger.error(f"Failed to generate intelligent summary: {e}")
            return f"Failed to generate intelligent summary: {e}"

    def _create_summary_prompt(self, usage_summary: Dict[str, Any], period: str) -> str:
        """Create a prompt for the LLM based on usage summary.

        Args:
            usage_summary: Dictionary containing usage statistics
            period: Time period for the summary

        Returns:
            Formatted prompt string
        """
        prompt = (
            "Please analyze the following {period} GPU usage data and provide an insightful summary:\n\n"
            "Total records: {total_records}\n"
            "Time range: {time_range}\n"
            "Unique GPUs: {unique_gpus}\n"
            "Average memory used: {average_memory_used} MB\n"
            "Average utilization: {average_utilization}%\n"
            "Peak memory used: {peak_memory_used} MB\n"
            "Peak utilization: {peak_utilization}%\n\n"
            "The Output Formtat should be: 1. 请你保证输出语言是中文！并且尽可能简洁 2. 你的输出只能包含两个部分：总结分析使用量，分析变化趋势 3. 你不允许使用任何的 markdown 标记"
            "如果 GPU 使用量很低或者基本为 0，请你只输出一句话：该干活了！！！"
        ).format(
            period=usage_summary.get("period", "period"),
            total_records=usage_summary["total_records"],
            time_range=usage_summary["time_range"],
            unique_gpus=usage_summary["unique_gpus"],
            average_memory_used=usage_summary["average_memory_used"],
            average_utilization=usage_summary["average_utilization"],
            peak_memory_used=usage_summary["peak_memory_used"],
            peak_utilization=usage_summary["peak_utilization"],
        )

        return prompt
