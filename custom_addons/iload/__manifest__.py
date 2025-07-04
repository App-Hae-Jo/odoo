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
        'views/iload_dashboard_template.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'iload/static/src/css/iload_style.css',
            'iload/static/src/js/iload.js',
            'iload/static/src/img/iload_logo.svg',
            'iload/static/src/img/odoo_logo.png',
        ],
    },
    'installable': True,
    'application': True,
}
