# -*- coding: utf-8 -*-
# © <2016> <Jarsa Sistemas, S.A. de C.V.>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, fields, models, _
import requests
from lxml import etree
import base64


class CvaConfig(models.Model):
    _name = 'cva.config.settings'
    _inherit = 'res.config.settings'

    name = fields.Char(
        string='Client number', required=True)
    allowed_groups = fields.Many2many(
        'cva.group', string='Allowed groups')

    @api.multi
    def connect_cva(self, params):
        """
            Connect to CVA web-services
            @param params: dict with parameters to generate xml file
            @return: returns a xml object
        """
        url = (
            'https://www.grupocva.com/catalogo_clientes_xml/lista_precios.xml')
        data = requests.get(str(url), params=params).content
        root = etree.XML(data)
        return root

    @api.multi
    def get_groups(self):
        group = self.env['cva.group']
        group_list = [x.name for x in group.search([])]
        params = {'cliente': self.name}
        root = self.connect_cva(params)
        for item in root:
            if (item.findtext('grupo') not in group_list and
                    item.findtext('grupo') != ''):
                group.create({'name': item.findtext('grupo')})
                group_list.append(item.findtext('grupo'))

    @api.multi
    def create_product(self, item):
        product_obj = self.env['product.template']
        find = item.findtext
        if not find('imagen'):
            image = False
        else:
            image = base64.encodestring(
                requests.get(find('imagen')).content)
        product_obj.create(
            {'name': find('descripcion'),
             'default_code': find('clave'),
             'standard_price': float(find('precio')),
             'description': _('Group\n' + find('grupo') + '\n' +
                              'Subgroup\n' + find('subgrupo') +
                              '\n' + 'Ficha comercial\n' +
                              find('ficha_comercial') +
                              '\n' + 'Ficha tecnica\n' +
                              find('ficha_tecnica')),
             'image_medium': image,
             })

    # def update_product_cron(self, cr, uid):
    #     cva_obj = self.pool.get('cva.config.settings')
    #     cva_id = cva_obj.search(cr, uid, [])
    #     cva = cva_obj.browse(cr, uid, cva_id[0])
    #     product_obj = self.pool.get('product.template')
    #     product_ids = product_obj.search(cr, uid, [])
    #     product_list = product_obj.browse(cr, uid, product_ids)
    #     for product in product_list:
    #         params = {
    #             'cliente': cva.name,
    #             'clave': product.default_code,
    #             'MonedaPesos': '1',
    #         }
    #         root = cva.connect_cva(params=params)
    #         if len(root) == 0:
    #             pass
    #         elif len(root) > 1:
    #             for item in root:
    #                 if item.findtext('clave') == product.default_code:
    #                     product_obj.write(
    #                         cr, uid, product.id, {
    #                             'standard_price':
    #                             float(item.findtext('precio'))
    #                         })
    #         else:
    #             product_obj.write(
    #                 cr, uid, product.id, {
    #                     'standard_price':
    #                     float(root[0].findtext('precio'))
    #                 })

    @api.multi
    def get_products(self):
        product = self.env['product.template']
        group_list = [x.name for x in self.allowed_groups]
        product_list = [x.default_code for x in product.search([])]
        for group in group_list:
            params = {
                'cliente': self.name,
                'grupo': group,
                'depto': '1',
                'dt': '1',
                'dc': '1',
                'subgpo': '1',
                'MonedaPesos': '1',
            }
            root = self.connect_cva(params)
            for item in root:
                find = item.findtext
                if find('clave') not in product_list:
                    self.create_product(item)

            return root
