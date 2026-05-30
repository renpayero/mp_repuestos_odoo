# -*- coding: utf-8 -*-
import secrets
import string
import re

from odoo import api, fields, models


class DakoPassword(models.Model):
    _name = 'dako.password'
    _description = 'Contraseña gestionada por el equipo'
    _order = 'name'

    name = fields.Char(string='Nombre', required=True)
    username = fields.Char(string='Usuario / Email')
    password = fields.Char(string='Contraseña', required=True)
    url = fields.Char(string='URL')
    note = fields.Text(string='Nota')
    vault_id = fields.Many2one(
        'dako.password.vault', string='Vault', required=True, ondelete='cascade', index=True,
    )

    strength = fields.Selection(
        [('weak', 'Débil'), ('medium', 'Media'), ('strong', 'Fuerte')],
        string='Fortaleza',
        compute='_compute_strength',
        store=True,
    )
    strength_score = fields.Integer(
        string='Puntaje',
        compute='_compute_strength',
        store=True,
    )

    @api.depends('password')
    def _compute_strength(self):
        for rec in self:
            pwd = rec.password or ''
            score = 0
            if len(pwd) >= 8:
                score += 25
            if len(pwd) >= 12:
                score += 15
            if re.search(r'[a-z]', pwd) and re.search(r'[A-Z]', pwd):
                score += 20
            if re.search(r'\d', pwd):
                score += 20
            if re.search(r'[^A-Za-z0-9]', pwd):
                score += 20
            score = min(score, 100)

            rec.strength_score = score
            if score >= 75:
                rec.strength = 'strong'
            elif score >= 45:
                rec.strength = 'medium'
            else:
                rec.strength = 'weak'

    def action_generate_password(self, length=16, use_symbols=True):
        self.ensure_one()
        alphabet = string.ascii_letters + string.digits
        if use_symbols:
            alphabet += '!@#$%^&*()-_=+[]{}'
        new_pwd = ''.join(secrets.choice(alphabet) for _ in range(length))
        self.password = new_pwd
        return new_pwd

    @api.model
    def generate_password_value(self, length=16, use_symbols=True):
        alphabet = string.ascii_letters + string.digits
        if use_symbols:
            alphabet += '!@#$%^&*()-_=+[]{}'
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    def action_export_xlsx(self):
        ids = self.ids or self.search([]).ids
        return {
            'type': 'ir.actions.act_url',
            'url': '/dako_password/export/xlsx?ids=%s' % ','.join(str(i) for i in ids),
            'target': 'self',
        }

    @api.depends('name', 'vault_id', 'vault_id.name')
    def _compute_display_name(self):
        for rec in self:
            if rec.vault_id:
                rec.display_name = '[%s] %s' % (rec.vault_id.name, rec.name)
            else:
                rec.display_name = rec.name
