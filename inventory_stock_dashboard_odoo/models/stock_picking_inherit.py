# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import api, models


class StockPickingInherit(models.Model):
    _inherit = "stock.picking"

    @api.model
    def get_operation_types(self):
        """rpc method of operation type tiles,operation type graph
            Returns operation type details.
            no_transfer - each operation type transfer count,
            late - each operation type late count
            waiting - each operation type waiting count
            operation_type_name - have all the operation type name
            backorder - each operation type backorders count
                """
        no_transfer = {}
        stock_picking_type = self.env['stock.picking.type'].search([])
        stock_picking = self.env['stock.picking'].search([])
        stock = []
        length = []
        names = []
        late = {}
        query = '''select stock_picking.picking_type_id, count(stock_picking.picking_type_id) from stock_picking
            inner join stock_picking_type on stock_picking.picking_type_id = stock_picking_type.id
            where stock_picking.company_id = %s and
            stock_picking.state in ('assigned', 'waiting', 'confirmed') and (has_deadline_issue = true or 
            date_deadline <= now() or scheduled_date <= now())
            group by stock_picking.picking_type_id''' % self.env.company.id

        self._cr.execute(query)
        lates = self._cr.dictfetchall()
        for rec in lates:
            late.update({rec.get('picking_type_id'): rec.get('count')})
        waiting = {}
        backorder = {}
        operation_type_name = {}
        for i in stock_picking_type:
            names.append(i.name)
            orders = stock_picking.filtered(lambda r: r.picking_type_id.id == i.id)
            stock.append(len(orders))
            length_stock_picking = len(orders)
            length.append(len(stock_picking.filtered(lambda r: r.picking_type_id.id == i.id)))
            no_transfer.update({i.id: length_stock_picking})
            operation_type_name.update({i.id: i.name})
            if len(orders) > 0:
                if len(orders.filtered(lambda r: r.state == 'confirmed')) > 0:
                    waiting.update({i.id: len(orders.filtered(lambda r: r.state == 'confirmed'))})
                if len(orders.mapped('backorder_id')) > 0:
                    backorder.update({i.id: len(orders.mapped('backorder_id'))})
        return no_transfer, late, waiting, operation_type_name, backorder

    @api.model
    def get_product_category(self):
        """rpc method of product category graph
        Returns product categories and category having on hand product quantity"""
        category_ids = self.env['product.category'].search([])
        category_name = []
        product_count = []
        for rec in category_ids:
            name = rec.name
            category_name.append(name)
            count = rec.product_count
            product_count.append(count)
        value = {'name': category_name, 'count': product_count}
        return value

    @api.model
    def get_locations(self):
        """rpc method of product location table
               Returns locations and location having on hand product quantity"""
        stock_quant_ids = self.env['stock.quant'].search([])
        locations = stock_quant_ids.mapped('location_id')
        value = {}
        for rec in locations:
            loc_stock_quant = stock_quant_ids.filtered(lambda x: x.location_id == rec)
            on_hand_quantity = sum(loc_stock_quant.mapped('inventory_quantity_auto_apply'))
            value[rec.name] = on_hand_quantity
        return value