from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    bl_fbr_hs_code = fields.Char(string="FBR HS Code")
    bl_fbr_item_code = fields.Char(string="FBR Item Code")
    bl_fbr_uom = fields.Char(string="FBR UOM")
    bl_fbr_sale_type = fields.Char(string="FBR Sale Type")
    bl_fbr_scenario = fields.Char(string="FBR Scenario")
    bl_fbr_scenario_id = fields.Many2one("bl.fbr.scenario", string="FBR Scenario Record")
    bl_fbr_exempt_from_validation = fields.Boolean(string="Exempt from FBR Validation")
