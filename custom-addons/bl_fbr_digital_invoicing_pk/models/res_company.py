from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    bl_fbr_seller_registration_no = fields.Char(string="FBR Seller Registration No")
    bl_fbr_ntn = fields.Char(string="FBR NTN")
    bl_fbr_strn = fields.Char(string="FBR STRN")
    bl_fbr_seller_province = fields.Char(string="FBR Seller Province")
    bl_fbr_business_name_override = fields.Char(string="FBR Business Name Override")
    bl_fbr_default_sale_type = fields.Char(default="Standard taxable sale")
    bl_fbr_default_scenario_id = fields.Many2one("bl.fbr.scenario", string="Default FBR Scenario")
    bl_fbr_api_token = fields.Char(string="FBR API Token", groups="base.group_system")
    bl_fbr_sandbox_base_url = fields.Char(string="FBR Sandbox Base URL")
    bl_fbr_production_base_url = fields.Char(string="FBR Production Base URL")
