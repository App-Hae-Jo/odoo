# custom_addons/iload_back_office/__manifest__.py

{
    'name': '아이로드',
    'version': '1.0',
    'category': '운송 / 물류',
    'summary': 'iLoad 운송 주문 및 차량 매입 관리', # 요약 변경
    'description': """
        iLoad 백오피스 모듈로, 운송 주문 관리, 차량 매입 및 관련 문서 처리 기능을 제공합니다.
    """,
    'author': 'Ai dot',
    'depends': [
        'base',        # Odoo의 핵심 기능 (필수)
        'mail',        # mail.thread, mail.activity.mixin 사용 시 필수
        'contacts',    # res.partner (고객/거래처) 사용 시 필수
        # 'web'는 'base'가 간접적으로 포함하므로 명시적으로 추가할 필요는 없습니다.
    ],
    'data': [
        # 보안 규칙
        # 'security/iload_security.xml', # 특정 그룹별 권한이 필요할 경우 만듭니다. 현재는 ir.model.access.csv로 충분
        'security/ir.model.access.csv',

        # 리포트
        'report/iload_customs_request_report.xml',

        # 시퀀스 (주문 및 매입 번호 자동 생성을 위해)
        'data/iload_sequence.xml',  
        # ocr 관련 wizard가 먼저되야되나 ?         
        'views/ocr_upload_vehicle_wizard_views.xml',
        'wizard/iload_vehicle_deregistration_wizard_views.xml',
        # 뷰 파일들
        'views/res_partner_views.xml', # 파트너 모델 확장 뷰
        'views/iload_vehicle_views.xml', # 차량 모델 마스터 뷰
        'views/iload_order_views.xml',       # 운송 주문 뷰
        'views/iload_export_declaration_upload_wizard_views.xml',
        'views/iload_order_detail_views.xml', # 운송 주문 상세 뷰
        'views/iload_vehicle_acquisition_views.xml', # 차량 매입 뷰
        'views/iload_vehicle_acquisition_document_views.xml',
        'views/iload_export_document_views.xml',
        'views/iload_customs_print_wizard_views.xml',
        'views/iload_shipping_mark_templates.xml',
        'views/iload_shipping_views.xml',
        'views/iload_shipping_document_views.xml',

        # 메뉴 아이템 (모든 뷰 로드 후 메뉴 연결)
        'views/iload_menus.xml',             
    ],
    'assets': {
        'web.assets_backend': ['iload/static/src/css/iload_back_office.css',],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    # 'license': 'LGPL-3',      # 모듈의 라이선스 (권장)
    'web_icon': 'iload_back,iload/static/src/img/iload_logo.svg', # 앱스 및 메뉴에 표시될 아이콘 경로 (선택 사항)
}