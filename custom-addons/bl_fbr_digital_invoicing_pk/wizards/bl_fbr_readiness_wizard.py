from odoo import Command, fields, models


class BlFbrReadinessWizard(models.TransientModel):
    _name = "bl.fbr.readiness.wizard"
    _description = "FBR Readiness Wizard"

    move_ids = fields.Many2many("account.move", string="Invoices")
    line_ids = fields.One2many("bl.fbr.readiness.wizard.line", "wizard_id")
    result_html = fields.Html(readonly=True)

    def action_validate(self):
        self.ensure_one()
        self.line_ids.unlink()
        commands = []
        ready_count = 0
        for move in self.move_ids:
            errors = move._bl_fbr_validation_errors()
            if not errors:
                ready_count += 1
            commands.append(
                Command.create(
                    {
                        "move_id": move.id,
                        "partner_id": move.partner_id.id,
                        "invoice_date": move.invoice_date,
                        "fbr_status": "ready" if not errors else "blocked",
                        "blocking_issues": "\n".join(errors),
                    }
                )
            )
        self.line_ids = commands
        self.result_html = "<p><strong>%s of %s invoices ready.</strong></p>" % (ready_count, len(self.move_ids))
        return True

    def action_submit_ready(self):
        for line in self.line_ids.filtered(lambda item: item.fbr_status == "ready"):
            line.move_id.action_bl_fbr_submit()
        return True

    def action_queue_ready(self):
        for line in self.line_ids.filtered(lambda item: item.fbr_status == "ready"):
            line.move_id.action_bl_fbr_queue()
        return True


class BlFbrReadinessWizardLine(models.TransientModel):
    _name = "bl.fbr.readiness.wizard.line"
    _description = "FBR Readiness Wizard Line"

    wizard_id = fields.Many2one("bl.fbr.readiness.wizard", required=True, ondelete="cascade")
    move_id = fields.Many2one("account.move", required=True)
    partner_id = fields.Many2one("res.partner")
    invoice_date = fields.Date()
    fbr_status = fields.Selection([("ready", "Ready"), ("blocked", "Blocked")])
    blocking_issues = fields.Text()

    def action_open_invoice(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.move_id.display_name,
            "res_model": "account.move",
            "view_mode": "form",
            "res_id": self.move_id.id,
        }
