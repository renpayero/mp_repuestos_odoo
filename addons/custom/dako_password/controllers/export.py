# -*- coding: utf-8 -*-
import io
from datetime import datetime

from odoo import http
from odoo.http import request, content_disposition

try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None


class DakoPasswordExport(http.Controller):

    @http.route('/dako_password/export/xlsx', type='http', auth='user')
    def export_xlsx(self, ids=None, **kwargs):
        if xlsxwriter is None:
            return request.make_response(
                'xlsxwriter no está instalado en el servidor.',
                headers=[('Content-Type', 'text/plain; charset=utf-8')],
            )

        record_ids = []
        if ids:
            record_ids = [int(i) for i in ids.split(',') if i.strip().isdigit()]

        Password = request.env['dako.password']
        records = Password.browse(record_ids) if record_ids else Password.search([])
        records = records.filtered(lambda r: r.id)

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Contraseñas')

        header_fmt = workbook.add_format({
            'bold': True, 'bg_color': '#1f2937', 'font_color': '#ffffff',
            'border': 1, 'align': 'center', 'valign': 'vcenter',
        })
        cell_fmt = workbook.add_format({'border': 1, 'valign': 'vcenter'})
        date_fmt = workbook.add_format({'border': 1, 'num_format': 'yyyy-mm-dd hh:mm'})

        headers = ['Nombre', 'Usuario', 'Contraseña', 'URL', 'Fortaleza', 'Creado por', 'Fecha creación']
        widths = [28, 24, 28, 36, 12, 22, 20]
        for col, (title, width) in enumerate(zip(headers, widths)):
            sheet.set_column(col, col, width)
            sheet.write(0, col, title, header_fmt)

        strength_label = {'weak': 'Débil', 'medium': 'Media', 'strong': 'Fuerte'}
        for row_idx, rec in enumerate(records, start=1):
            sheet.write(row_idx, 0, rec.name or '', cell_fmt)
            sheet.write(row_idx, 1, rec.username or '', cell_fmt)
            sheet.write(row_idx, 2, rec.password or '', cell_fmt)
            sheet.write(row_idx, 3, rec.url or '', cell_fmt)
            sheet.write(row_idx, 4, strength_label.get(rec.strength, ''), cell_fmt)
            sheet.write(row_idx, 5, rec.create_uid.name or '', cell_fmt)
            if rec.create_date:
                sheet.write_datetime(row_idx, 6, rec.create_date, date_fmt)
            else:
                sheet.write(row_idx, 6, '', cell_fmt)

        sheet.freeze_panes(1, 0)
        workbook.close()
        output.seek(0)
        data = output.read()

        filename = 'dako_passwords_%s.xlsx' % datetime.now().strftime('%Y%m%d_%H%M%S')
        return request.make_response(
            data,
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', content_disposition(filename)),
                ('Content-Length', len(data)),
            ],
        )
