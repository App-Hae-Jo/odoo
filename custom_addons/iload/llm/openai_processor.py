# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import UserError
import openai
from .base_llm import BaseLLM

class OpenAIProcessor(BaseLLM):
    """
    OpenAI API를 사용하여 텍스트를 처리하는 LLM 프로세서입니다.
    """

    _name = 'iload.openai_processor'
    _description = 'OpenAI LLM Processor'

    name = fields.Char(string="Name", default="OpenAI Processor")
    api_key = fields.Char(string="API Key", required=True, groups="base.group_system", help="Your OpenAI API Key")
    model_name = fields.Char(string="Model Name", default="gpt-3.5-turbo", help="e.g., gpt-3.5-turbo, gpt-4")
    temperature = fields.Float(string="Temperature", default=0.7, help="Controls randomness: lower is less random.")
    max_tokens = fields.Integer(string="Max Tokens", default=150, help="Maximum number of tokens to generate.")

    @api.model
    def _get_llm_processor_name(self):
        return "openai"

    def _process_text_internal(self, prompt, **kwargs):
        """
        BaseLLM의 추상 메서드를 구현하여 OpenAI API 호출을 수행합니다.
        """
        if not self.api_key:
            raise UserError("OpenAI API Key is not configured.")

        try:
            openai.api_key = self.api_key
            messages = [{"role": "user", "content": prompt}]

            response = openai.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                **kwargs
            )
            return response.choices[0].message.content.strip()
        except openai.APIStatusError as e: # openai.error.OpenAIError 대신 최신 예외 처리
            raise UserError(f"OpenAI API Error: {e.status_code} - {e.response}")
        except Exception as e:
            raise UserError(f"An unexpected error occurred with OpenAI: {e}")

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