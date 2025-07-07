# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class IloadVehicleDeregistrationWizard(models.TransientModel):
    _name = 'iload.vehicle.deregistration.wizard'
    _description = '차량 말소 등록 마법사'

    deregistration_certificate = fields.Binary(string="말소 확인증", required=True)
    file_name = fields.Char(string="파일 이름")

    # HAJINTODO
    # 여기에 말소확인증으로 ocr 해서 차대번호같은걸로 구매한 목록에서 찾아서 알아서 말소상태로 바꿔 줄수있을듯
    # self.env(iload.vehicle.acquisition) 에서 찾으면 될듯합니다요 !
    def ocr(self):
        return{}


    def action_confirm(self):
        """
        말소 확인증을 업로드하고, 선택된 차량의 말소 상태를 업데이트합니다.
        """
        self.ensure_one()
        active_ids = self.env.context.get('active_ids', [])

        if not active_ids or len(active_ids) > 1:
            raise UserError("말소 등록은 단일 차량에 대해서만 가능합니다.")

        acquisition_record = self.env['iload.vehicle.acquisition'].browse(active_ids)

        if acquisition_record.deregistration_status:
            raise UserError("선택된 차량은 이미 말소 처리되었습니다.")

        # 1. 매입 관련 문서에 추가 (첨부파일 포함)
        # 'attachment=True' 필드이므로 ir.attachment는 자동 생성됩니다.
        self.env['iload.vehicle.acquisition.document'].create({
            'acquisition_id': acquisition_record.id,
            'attachment': self.deregistration_certificate,
            'name': self.file_name or '말소 확인증',
            'document_type': 'deregistration_confirmation',
        })

        # 2. 차량 매입 정보 업데이트
        acquisition_record.write({
            'deregistration_status': True,
            'deregistration_date': fields.Date.today(),
        })

        return {'type': 'ir.actions.act_window_close'}
