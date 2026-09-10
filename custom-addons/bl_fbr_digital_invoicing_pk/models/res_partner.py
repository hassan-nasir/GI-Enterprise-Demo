from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    bl_fbr_registration_type = fields.Selection(
        [
            ("registered", "Registered"),
            ("unregistered", "Unregistered"),
            ("consumer", "Consumer"),
        ],
        string="FBR Registration Type",
    )
    bl_fbr_registration_no = fields.Char(string="FBR Registration No")
    bl_fbr_ntn = fields.Char(string="FBR NTN")
    bl_fbr_cnic = fields.Char(string="FBR CNIC")
    bl_fbr_strn = fields.Char(string="FBR STRN")
    bl_fbr_province = fields.Char(string="FBR Province")
    bl_fbr_buyer_type = fields.Char(string="FBR Buyer Type")
    bl_fbr_exempt_from_validation = fields.Boolean(string="Exempt from FBR Validation")
