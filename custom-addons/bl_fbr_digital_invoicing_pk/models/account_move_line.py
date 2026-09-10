from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    bl_fbr_hs_code = fields.Char(related="product_id.product_tmpl_id.bl_fbr_hs_code", store=True)
    bl_fbr_uom = fields.Char(related="product_id.product_tmpl_id.bl_fbr_uom", store=True)
    bl_fbr_sale_type = fields.Char(related="product_id.product_tmpl_id.bl_fbr_sale_type", store=True)
    bl_fbr_scenario_id = fields.Many2one(related="product_id.product_tmpl_id.bl_fbr_scenario_id", store=True)
