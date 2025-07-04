# -*- coding: utf-8 -*-

from odoo import api, models
from odoo.exceptions import UserError

class LLMProcessorFactory(models.AbstractModel):
    _name = 'iload.llm_processor_factory'
    _description = 'LLM Processor Factory'

    @api.model
    def get_processor(self, processor_type):
        """
        주어진 유형에 따라 적절한 LLM 프로세서 인스턴스를 반환합니다.
        :param processor_type: 'openai', 'anthropic' 등 LLM 프로세서의 유형.
        :return: 해당 LLM 프로세서의 레코드셋 인스턴스.
        """
        if processor_type == 'openai':
            processor = self.env['iload.openai_processor'].search([], limit=1)
            if not processor:
                raise UserError("OpenAI processor not configured. Please create one.")
            return processor
        elif processor_type == 'anthropic':
            processor = self.env['iload.anthropic_processor'].search([], limit=1)
            if not processor:
                raise UserError("Anthropic processor not configured. Please create one.")
            return processor
        else:
            raise UserError(f"Unknown LLM processor type: {processor_type}")