# -*- coding: utf-8 -*-
from random import randint

from odoo import api, fields, models


class DakoPasswordVault(models.Model):
    _name = 'dako.password.vault'
    _description = 'Vault de contraseñas'
    _order = 'name'

    name = fields.Char(string='Nombre', required=True)
    description = fields.Text(string='Descripción')
    color = fields.Integer(string='Color', default=lambda self: randint(1, 11))
    active = fields.Boolean(default=True)

    user_ids = fields.Many2many(
        'res.users',
        'dako_password_vault_user_rel',
        'vault_id', 'user_id',
        string='Usuarios autorizados',
        default=lambda self: [(6, 0, [self.env.user.id])],
        help='Solo estos usuarios podrán ver y editar las contraseñas de este vault.',
    )

    password_ids = fields.One2many(
        'dako.password', 'vault_id', string='Contraseñas',
    )
    password_count = fields.Integer(
        string='Cantidad', compute='_compute_password_count',
    )

    @api.depends('password_ids')
    def _compute_password_count(self):
        for vault in self:
            vault.password_count = len(vault.password_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'user_ids' not in vals or not vals.get('user_ids'):
                vals['user_ids'] = [(6, 0, [self.env.user.id])]
            else:
                # Asegurarse de que el creador siempre quede incluido
                vals['user_ids'] = vals['user_ids'] + [(4, self.env.user.id)]
        return super().create(vals_list)

    def action_open_passwords(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Contraseñas - %s' % self.name,
            'res_model': 'dako.password',
            'view_mode': 'list,form',
            'domain': [('vault_id', '=', self.id)],
            'context': {'default_vault_id': self.id},
        }
