from datetime import timedelta

from odoo import api, fields, models


class BlFbrQueue(models.Model):
    _name = "bl.fbr.queue"
    _description = "Bashalog FBR Retry Queue"
    _order = "next_attempt_at asc, id desc"
    _rec_name = "name"

    name = fields.Char(default="New", required=True)
    move_id = fields.Many2one("account.move", required=True, index=True, ondelete="cascade")
    invoice_id = fields.Many2one("account.move", string="Invoice", related="move_id", store=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    status = fields.Selection(
        [
            ("queued", "Queued"),
            ("processing", "Processing"),
            ("failed", "Failed"),
            ("done", "Done"),
            ("cancelled", "Cancelled"),
        ],
        default="queued",
        required=True,
    )
    state = fields.Selection(string="State", related="status", store=True)
    attempt_count = fields.Integer(default=0)
    retry_count = fields.Integer(string="Retry Count", related="attempt_count", store=True)
    max_retry_attempts = fields.Integer(default=3)
    next_attempt_at = fields.Datetime()
    next_retry_at = fields.Datetime(string="Next Retry At", related="next_attempt_at", store=True)
    last_error = fields.Text()
    last_error_code = fields.Char()
    last_log_id = fields.Many2one("bl.fbr.log")
    connection_mode = fields.Char()
    created_by = fields.Many2one("res.users", default=lambda self: self.env.user)
    processed_at = fields.Datetime()

    @api.model_create_multi
    def create(self, vals_list):
        sequence = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = sequence.next_by_code("bl.fbr.queue") or "New"
        return super().create(vals_list)

    @api.model
    def create_or_update_for_move(self, move, error_message):
        config = self.env["bl.fbr.config"].get_config()
        queue = self.search([("move_id", "=", move.id), ("status", "!=", "done")], limit=1)
        vals = {
            "move_id": move.id,
            "company_id": move.company_id.id,
            "status": "queued",
            "last_error": error_message,
            "last_error_code": "MOCK_VALIDATION_ERROR",
            "max_retry_attempts": config.max_retry_attempts or 3,
            "connection_mode": config.connection_mode,
            "next_attempt_at": fields.Datetime.now() + timedelta(minutes=config.retry_delay_minutes or 15),
        }
        if queue:
            vals["attempt_count"] = queue.attempt_count + 1
            queue.write(vals)
            return queue
        vals["attempt_count"] = 1
        return self.create(vals)

    def action_retry(self):
        return self.action_process()

    def action_process(self):
        for queue in self:
            if queue.status in ("done", "cancelled"):
                continue
            queue.status = "processing"
            queue.move_id.action_bl_fbr_retry()
            if queue.move_id.bl_fbr_status == "submitted":
                queue.write({"status": "done", "processed_at": fields.Datetime.now()})
        return True

    def action_cancel(self):
        self.write({"status": "cancelled"})
        return True

    def action_requeue(self):
        config = self.env["bl.fbr.config"].get_config()
        self.write(
            {
                "status": "queued",
                "next_attempt_at": fields.Datetime.now() + timedelta(minutes=config.retry_delay_minutes or 15),
            }
        )
        return True

    @api.model
    def cron_process_fbr_queue(self):
        config = self.env["bl.fbr.config"].get_config()
        if not config.enable_retry_queue:
            return True
        now = fields.Datetime.now()
        queues = self.search(
            [
                ("status", "=", "queued"),
                "|",
                ("next_attempt_at", "=", False),
                ("next_attempt_at", "<=", now),
            ],
            limit=20,
        )
        for queue in queues:
            if queue.attempt_count >= (queue.max_retry_attempts or config.max_retry_attempts or 3):
                queue.status = "failed"
                continue
            queue.action_process()
        return True
