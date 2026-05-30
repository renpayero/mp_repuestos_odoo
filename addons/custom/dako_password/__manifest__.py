# -*- coding: utf-8 -*-
{
    'name': 'Dako Password Manager',
    'version': '19.0.1.0.0',
    'summary': 'Vaults de contraseñas con control de acceso por usuario',
    'author': 'DakoDev',
    'category': 'Tools',
    'depends': ['mail'],
    'data': [
        'security/ir.model.access.csv',
        'security/dako_password_security.xml',
        'views/dako_password_vault_views.xml',
        'views/dako_password_views.xml',
        'views/dako_password_menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'dako_password/static/src/components/**/*',
            'dako_password/static/src/scss/*.scss',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
