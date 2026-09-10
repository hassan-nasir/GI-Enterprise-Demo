from odoo import fields, models


class BlFbrScenario(models.Model):
    _name = "bl.fbr.scenario"
    _description = "FBR Scenario"
    _order = "code"

    name = fields.Char(required=True)
    code = fields.Char(required=True, index=True)
    description = fields.Text()
    active = fields.Boolean(default=True)
    default_sale_type = fields.Char(default="Standard taxable sale")
    notes = fields.Text()

    _code_unique = models.Constraint(
        "UNIQUE(code)",
        "The FBR scenario code must be unique.",
    )
