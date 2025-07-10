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
        'website', # 웹 컨트롤러를 사용하고 웹사이트 템플릿을 렌더링하므로 'website' 의존성 추가 권장
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/component/breadcrumb_template.xml',
        'views/iload_layout_template.xml',
        'views/iload_home_template.xml',

        # --- 여기에 누락된 뷰 파일들을 추가해야 합니다 ---
        'views/ocr_test_template.xml',
        'views/upload_result_template.xml',
        'views/history_template.xml',
        'views/record_detail_template.xml',
        'views/error_template.xml',
        'views/Iload_dashboard_template.xml', # 파일명 대소문자 주의: 'Iload' 그대로 사용
        # 만약 models 디렉토리에 정의된 뷰(예: action, menuitem)가 있다면 추가
        # 'views/document_record_views.xml', # 예시
    ],
    'assets': {
        'web.assets_frontend': [
            'iload/static/src/css/iload_style.css',
            # 정적 이미지 파일은 assets에 넣을 필요는 없지만, CSS에서 참조하거나 JS에서 동적으로 로드하는 경우 필요할 수 있습니다.
            # 이들은 직접적으로 웹사이트의 <head> 태그에 포함되는 항목들입니다.
            # 'iload/static/src/img/iload_logo.svg', # 일반적으로 필요 없음 (CSS에서 url()로 참조하는 경우 제외)
            # 'iload/static/src/img/odoo_logo.png', # 일반적으로 필요 없음
        ],
    },
    'installable': True,
    'application': True,
    # 'auto_install': False, # 필요에 따라 추가
    # 'license': 'LGPL-3', # 라이선스 명시 권장
}