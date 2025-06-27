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
        'views/iload_layout_template.xml',
        'views/iload_home_template.xml',
    ],
    'installable': True,
    'application': True,
}