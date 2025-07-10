# custom_addons/iload/__manifest__.py

{
    'name': '아이로드',
    'version': '1.0',
    'category': '운송 / 물류',
    'summary': 'iLoad 운송 주문 및 차량 매입 관리',
    'description': """
        iLoad 백오피스 모듈로, 운송 주문 관리, 차량 매입 및 관련 문서 처리 기능을 제공합니다.
    """,
    'author': 'Ai dot',
    'depends': [
        'base',
        'board',
        'mail',
        'contacts',
    ],
    'data': [
        'security/ir.model.access.csv',
        'report/iload_customs_request_report.xml',
        'data/iload_sequence.xml',
        'views/ocr_upload_vehicle_wizard_views.xml',
        'wizard/iload_vehicle_deregistration_wizard_views.xml',
        'views/res_partner_views.xml',
        'views/iload_vehicle_views.xml',
        'views/iload_order_views.xml',
        'views/iload_export_declaration_upload_wizard_views.xml',
        'views/iload_order_detail_views.xml',
        'views/iload_vehicle_acquisition_views.xml',
        'views/iload_vehicle_acquisition_document_views.xml',
        'views/iload_export_document_views.xml',
        'views/iload_customs_print_wizard_views.xml',
        'views/iload_shipping_mark_templates.xml',
        'views/iload_shipping_views.xml',
        'views/iload_shipping_document_views.xml',
        'views/iload_menus.xml',
        'views/dashboard_views.xml',
    ],
    'assets': {
        'web.assets_backend': ['iload/static/src/css/iload.css',],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'web_icon': 'iload_back,iload/static/src/img/iload_logo.svg',
}
