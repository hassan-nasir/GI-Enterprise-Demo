from odoo import fields, models


class BlFbrLog(models.Model):
    _name = "bl.fbr.log"
    _description = "Bashalog FBR Log"
    _order = "create_date desc, id desc"

    name = fields.Char(required=True)
    move_id = fields.Many2one("account.move", index=True, ondelete="cascade")
    move_name = fields.Char()
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    partner_id = fields.Many2one(related="move_id.partner_id", store=True)
    event_type = fields.Selection(
        [
            ("validation", "Validation"),
            ("submission", "Submission"),
            ("retry", "Retry"),
        ],
        required=True,
    )
    status = fields.Selection(
        [
            ("success", "Success"),
            ("failure", "Failure"),
            ("failed", "Failed"),
            ("warning", "Warning"),
            ("queued", "Queued"),
            ("skipped", "Skipped"),
        ],
        required=True,
    )
    http_status = fields.Integer()
    error_code = fields.Char()
    request_payload = fields.Text()
    response_payload = fields.Text()
    error_message = fields.Text()
    friendly_message = fields.Text()
    submitted_at = fields.Datetime()
    environment = fields.Selection(
        [
            ("mock", "Mock"),
            ("sandbox", "Sandbox"),
            ("production", "Production"),
        ],
        default="mock",
    )
    connection_mode = fields.Char()
    retry_no = fields.Integer(default=0)
    user_id = fields.Many2one("res.users", default=lambda self: self.env.user)
    duration_ms = fields.Integer()
    endpoint = fields.Char()
    is_mock = fields.Boolean()
