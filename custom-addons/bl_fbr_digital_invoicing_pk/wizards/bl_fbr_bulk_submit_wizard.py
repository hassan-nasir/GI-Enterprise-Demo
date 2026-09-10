from odoo import fields, models
from odoo.exceptions import UserError


class BlFbrBulkSubmitWizard(models.TransientModel):
    _name = "bl.fbr.bulk.submit.wizard"
    _description = "FBR Bulk Submit Wizard"

    move_ids = fields.Many2many("account.move", string="Invoices")
    action_type = fields.Selection(
        [
            ("validate", "Validate Only"),
            ("submit", "Submit Now"),
            ("queue", "Queue for Retry"),
        ],
        default="validate",
        required=True,
    )
    skip_errors = fields.Boolean(default=True)
    stop_on_first_error = fields.Boolean(default=False)
    result_html = fields.Html(readonly=True)

    def action_run(self):
        self.ensure_one()
        messages = []
        for move in self.move_ids:
            errors = move._bl_fbr_validation_errors()
            if errors:
                message = "%s: %s" % (move.name, "; ".join(errors))
                messages.append(message)
                move.action_bl_fbr_validate()
                if self.stop_on_first_error:
                    raise UserError(message)
                if not self.skip_errors:
                    continue
                continue
            if self.action_type == "validate":
                move.action_bl_fbr_validate()
                messages.append("%s: ready" % move.name)
            elif self.action_type == "submit":
                move.action_bl_fbr_submit()
                messages.append("%s: submitted" % move.name)
            elif self.action_type == "queue":
                move.action_bl_fbr_queue()
                messages.append("%s: queued" % move.name)
        self.result_html = "<ul>%s</ul>" % "".join("<li>%s</li>" % msg for msg in messages)
        return True
