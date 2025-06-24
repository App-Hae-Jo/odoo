{
    'name': 'Hello World',
    'version': '1.0',
    'category': 'Tools',
    'summary': 'Simple Hello World module',
    'description': 'This module displays a Hello World message.',
    'depends': ['base', 'web'],
    'data': [
        'views/hello_template.xml',
    ],
    'installable': True,
    'application': True,
}