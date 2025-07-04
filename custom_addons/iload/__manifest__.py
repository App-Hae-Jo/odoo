# iload/__manifest__.py
{
    'name': 'iLoad',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'iLoad HeackerThon Module',
    'description': 'iLoad HeackerThon Module',
    'depends': [
        'base',
        'web',
        'sale',
        'stock',
        'account',
        'product',
        'contacts',
        'mail',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/component/breadcrumb_template.xml',
        'views/iload_layout_template.xml',
        'views/iload_home_template.xml',
        # --- 여기에 누락된 뷰 파일들을 추가해야 합니다 ---

        # 'views/ocr_test_template.xml',
        # 'views/upload_result_template.xml',
        # 'views/history_template.xml',
        # 'views/record_detail_template.xml',
        # 'views/error_template.xml',
        # 'views/Iload_dashboard_template.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'iload/static/src/css/iload_style.css',
            'iload/static/src/img/iload_logo.svg',
            'iload/static/src/img/odoo_logo.png',
        ],
    }
}