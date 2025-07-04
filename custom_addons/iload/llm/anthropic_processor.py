# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import UserError
import anthropic
from .base_llm import BaseLLM

class AnthropicProcessor(BaseLLM):
    """
    Anthropic API를 사용하여 텍스트를 처리하는 LLM 프로세서입니다.
    """

    _name = 'iload.anthropic_processor'
    _description = 'Anthropic LLM Processor'

    name = fields.Char(string="Name", default="Anthropic Processor")
    api_key = fields.Char(string="API Key", required=True, groups="base.group_system", help="Your Anthropic API Key")
    model_name = fields.Char(string="Model Name", default="claude-3-opus-20240229", help="e.g., claude-3-opus-20240229, claude-3-sonnet-20240229")
    max_tokens = fields.Integer(string="Max Tokens", default=1000, help="Maximum number of tokens to generate.")
    temperature = fields.Float(string="Temperature", default=0.7, help="Controls randomness: lower is less random.")

    @api.model
    def _get_llm_processor_name(self):
        return "anthropic"

    def _process_text_internal(self, prompt, **kwargs):
        """
        BaseLLM의 추상 메서드를 구현하여 Anthropic API 호출을 수행합니다.
        """
        if not self.api_key:
            raise UserError("Anthropic API Key is not configured.")

        try:
            client = anthropic.Anthropic(api_key=self.api_key)
            response = client.messages.create(
                model=self.model_name,
                max_tokens=self.max_tokens,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                **kwargs
            )
            return response.content[0].text
        except anthropic.APIError as e:
            raise UserError(f"Anthropic API Error: {e}")
        except Exception as e:
            raise UserError(f"An unexpected error occurred with Anthropic: {e}")

    def generate_response(self, prompt, **kwargs):
        return self._process_text_internal(prompt, **kwargs)

    def extract_info(self, text, extraction_pattern, **kwargs):
        full_prompt = f"{text}\n\nExtract the following information: {extraction_pattern}"
        return self._process_text_internal(full_prompt, **kwargs)

    def summarize_text(self, text, **kwargs):
        full_prompt = f"Summarize the following text:\n\n{text}"
        return self._process_text_internal(full_prompt, **kwargs)

    def classify_text(self, text, categories, **kwargs):
        category_list = ", ".join(categories)
        full_prompt = f"Classify the following text into one of these categories: {category_list}\n\nText: {text}"
        return self._process_text_internal(full_prompt, **kwargs)