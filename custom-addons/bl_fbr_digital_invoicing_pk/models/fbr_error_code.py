from odoo import fields, models


class BlFbrErrorCode(models.Model):
    _name = "bl.fbr.error.code"
    _description = "FBR Error Code"
    _order = "code"

    code = fields.Char(required=True, index=True)
    name = fields.Char(required=True)
    description = fields.Text()
    friendly_message = fields.Text()
    suggested_fix = fields.Text()
    active = fields.Boolean(default=True)

    _code_unique = models.Constraint(
        "UNIQUE(code)",
        "The FBR error code must be unique.",
    )
