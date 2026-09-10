import base64
import json
from io import BytesIO

import qrcode

from odoo import _, Command, fields, models
from odoo.exceptions import UserError
from odoo.tools import file_open

from ..services.fbr_api_service import FbrApiService


class AccountMove(models.Model):
    _inherit = "account.move"

    bl_fbr_status = fields.Selection(
        [
            ("not_required", "Not Required"),
            ("draft", "Draft"),
            ("pending", "Pending"),
            ("ready", "Ready"),
            ("queued", "Queued"),
            ("validation_error", "Validation Error"),
            ("submitted", "Submitted"),
            ("failed", "Failed"),
            ("cancelled", "Cancelled"),
        ],
        string="FBR Status",
        default="pending",
        copy=False,
        tracking=True,
    )
    bl_fbr_connection_mode_used = fields.Char(copy=False, readonly=True)
    bl_fbr_invoice_number = fields.Char(string="Digital Invoice Reference", copy=False, readonly=True)
    bl_fbr_qr_data = fields.Text(string="QR Data", copy=False, readonly=True)
    bl_fbr_qr_code_image = fields.Binary(string="QR Code", copy=False, readonly=True)
    bl_fbr_error = fields.Text(copy=False, readonly=True)
    bl_fbr_last_error_code = fields.Char(string="Error Code", copy=False, readonly=True)
    bl_fbr_last_submission = fields.Datetime(string="Submission Time", copy=False, readonly=True)
    bl_fbr_payload_json = fields.Text(copy=False, readonly=True)
    bl_fbr_response_json = fields.Text(copy=False, readonly=True)
    bl_fbr_validation_summary = fields.Text(copy=False, readonly=True)
    bl_fbr_log_ids = fields.One2many("bl.fbr.log", "move_id")
    bl_fbr_queue_ids = fields.One2many("bl.fbr.queue", "move_id")
    bl_fbr_log_count = fields.Integer(compute="_compute_bl_fbr_counts")
    bl_fbr_queue_count = fields.Integer(compute="_compute_bl_fbr_counts")
    bl_fbr_retry_count = fields.Integer(compute="_compute_bl_fbr_counts")
    bl_fbr_is_submitted = fields.Boolean(compute="_compute_bl_fbr_is_submitted", store=True)
    bl_fbr_can_submit = fields.Boolean(compute="_compute_bl_fbr_can_submit")

    def _bl_fbr_report_logo_uri(self):
        """Return the bundled FBR Digital Invoicing mark for PDF reports."""
        self.ensure_one()
        with file_open(
            "bl_fbr_digital_invoicing_pk/static/src/img/fbr-digital-invoicing-system.png",
            "rb",
        ) as logo_file:
            encoded_logo = base64.b64encode(logo_file.read()).decode("ascii")
        return f"data:image/png;base64,{encoded_logo}"

    def _compute_bl_fbr_counts(self):
        for move in self:
            move.bl_fbr_log_count = len(move.bl_fbr_log_ids)
            active_queues = move.bl_fbr_queue_ids.filtered(lambda queue: queue.status != "done")
            move.bl_fbr_queue_count = len(active_queues)
            move.bl_fbr_retry_count = sum(move.bl_fbr_queue_ids.mapped("attempt_count"))

    def _compute_bl_fbr_is_submitted(self):
        for move in self:
            move.bl_fbr_is_submitted = bool(move.bl_fbr_invoice_number and move.bl_fbr_status == "submitted")

    def _compute_bl_fbr_can_submit(self):
        for move in self:
            move.bl_fbr_can_submit = (
                move.move_type in ("out_invoice", "out_refund")
                and move.state == "posted"
                and not move.bl_fbr_is_submitted
            )

    def _bl_fbr_config(self):
        self.ensure_one()
        return self.env["bl.fbr.config"].with_company(self.company_id).get_config()

    def _bl_fbr_builder(self):
        return self.env["bl.fbr.payload.builder"]

    def _bl_fbr_json(self, data):
        return json.dumps(data, indent=2, default=str, ensure_ascii=False)

    def _bl_fbr_payload(self):
        self.ensure_one()
        return self._bl_fbr_builder().build_submission_payload(self)

    def _bl_fbr_validation_errors(self):
        self.ensure_one()
        return self._bl_fbr_builder().validate_payload(self)

    def _bl_fbr_qr_image(self, qr_data):
        if not qr_data:
            return False
        img = qrcode.make(qr_data if isinstance(qr_data, str) else self._bl_fbr_json(qr_data))
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue())

    def _bl_fbr_environment(self, connection_mode):
        if connection_mode in ("sandbox", "production"):
            return connection_mode
        return "mock"

    def _bl_fbr_log(
        self,
        event_type,
        status,
        request_payload=None,
        response_payload=None,
        error_message=None,
        error_code=None,
        api_response=None,
        retry_no=0,
    ):
        self.ensure_one()
        config = self._bl_fbr_config()
        return self.env["bl.fbr.log"].create(
            {
                "name": f"{self.name or 'Draft Invoice'} - {event_type.title()} - {status.title()}",
                "move_id": self.id,
                "move_name": self.name,
                "company_id": self.company_id.id,
                "event_type": event_type,
                "status": status,
                "request_payload": self._bl_fbr_json(request_payload) if isinstance(request_payload, dict) else request_payload,
                "response_payload": self._bl_fbr_json(response_payload) if isinstance(response_payload, dict) else response_payload,
                "error_message": error_message,
                "friendly_message": error_message,
                "error_code": error_code,
                "http_status": api_response.get("http_status") if api_response else False,
                "submitted_at": fields.Datetime.now(),
                "environment": self._bl_fbr_environment(config.connection_mode),
                "connection_mode": config.connection_mode,
                "retry_no": retry_no,
                "duration_ms": api_response.get("duration_ms") if api_response else 0,
                "endpoint": api_response.get("endpoint") if api_response else False,
                "is_mock": api_response.get("is_mock") if api_response else config.connection_mode.startswith("mock_"),
            }
        )

    def _bl_fbr_set_validation_result(self, errors, payload):
        self.ensure_one()
        if errors:
            message = "\n".join(errors)
            self.write(
                {
                    "bl_fbr_status": "validation_error",
                    "bl_fbr_error": message,
                    "bl_fbr_validation_summary": message,
                    "bl_fbr_payload_json": self._bl_fbr_json(payload),
                }
            )
            self._bl_fbr_log("validation", "failure", request_payload=payload, error_message=message)
            self.message_post(body=_("FBR validation failed:<br/>%s") % "<br/>".join(errors))
            return False
        self.write(
            {
                "bl_fbr_status": "ready",
                "bl_fbr_error": False,
                "bl_fbr_last_error_code": False,
                "bl_fbr_validation_summary": _("Ready for FBR submission."),
                "bl_fbr_payload_json": self._bl_fbr_json(payload),
            }
        )
        self._bl_fbr_log("validation", "success", request_payload=payload, response_payload={"ready": True})
        self.message_post(body=_("FBR validation passed."))
        return True

    def action_bl_fbr_validate(self):
        validation_messages = []
        has_failures = False
        for move in self:
            payload = move._bl_fbr_payload()
            errors = move._bl_fbr_validation_errors()
            if errors:
                move._bl_fbr_set_validation_result(errors, payload)
                validation_messages.extend(errors)
                has_failures = True
                continue
            config = move._bl_fbr_config()
            if config.connection_mode not in ("sandbox", "production"):
                move._bl_fbr_set_validation_result(errors, payload)
                continue

            response = FbrApiService(move.env).validate(move, payload, config)
            request_payload = response.get("sent_payload") or payload
            move.write(
                {
                    "bl_fbr_connection_mode_used": config.connection_mode,
                    "bl_fbr_payload_json": move._bl_fbr_json(request_payload),
                    "bl_fbr_response_json": move._bl_fbr_json(response.get("raw_response")),
                    "bl_fbr_last_submission": fields.Datetime.now(),
                }
            )
            if response["success"]:
                message = _("FBR validation passed.")
                move.write(
                    {
                        "bl_fbr_status": "ready",
                        "bl_fbr_error": False,
                        "bl_fbr_last_error_code": False,
                        "bl_fbr_validation_summary": message,
                    }
                )
                move._bl_fbr_log(
                    "validation",
                    "success",
                    request_payload=request_payload,
                    response_payload=response.get("raw_response"),
                    api_response=response,
                )
                move.message_post(body=message)
                continue

            has_failures = True
            message = response.get("error_message") or _("FBR validation failed.")
            validation_messages.append(message)
            move.write(
                {
                    "bl_fbr_status": "validation_error",
                    "bl_fbr_error": message,
                    "bl_fbr_last_error_code": response.get("error_code"),
                    "bl_fbr_validation_summary": message,
                }
            )
            move._bl_fbr_log(
                "validation",
                "failure",
                request_payload=request_payload,
                response_payload=response.get("raw_response"),
                error_message=message,
                error_code=response.get("error_code"),
                api_response=response,
            )
            move.message_post(body=_("FBR validation failed:<br/>%s") % message.replace("\n", "<br/>"))
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("FBR Readiness Check"),
                "message": "\n".join(validation_messages) if has_failures else _("Validation completed. Check the FBR tab for details."),
                "type": "warning" if has_failures else "success",
                "sticky": has_failures,
            },
        }

    def action_bl_fbr_submit(self):
        validation_messages = []
        for move in self:
            if move.bl_fbr_invoice_number and move.bl_fbr_status == "submitted":
                raise UserError(_("This invoice has already been submitted to FBR."))
            payload = move._bl_fbr_payload()
            errors = move._bl_fbr_validation_errors()
            if errors:
                move._bl_fbr_set_validation_result(errors, payload)
                validation_messages.extend(errors)
                continue

            config = move._bl_fbr_config()
            response = FbrApiService(move.env).submit(move, payload, config)
            request_payload = response.get("sent_payload") or payload
            move.write(
                {
                    "bl_fbr_connection_mode_used": config.connection_mode,
                    "bl_fbr_payload_json": move._bl_fbr_json(request_payload),
                    "bl_fbr_response_json": move._bl_fbr_json(response.get("raw_response")),
                    "bl_fbr_last_submission": fields.Datetime.now(),
                }
            )
            if not response["success"]:
                error_message = response.get("error_message") or _("FBR submission failed.")
                move.write(
                    {
                        "bl_fbr_status": "failed",
                        "bl_fbr_error": error_message,
                        "bl_fbr_last_error_code": response.get("error_code"),
                    }
                )
                log = move._bl_fbr_log(
                    "submission",
                    "failure",
                    request_payload=request_payload,
                    response_payload=response.get("raw_response"),
                    error_message=error_message,
                    error_code=response.get("error_code"),
                    api_response=response,
                )
                if config.enable_retry_queue:
                    queue = move.env["bl.fbr.queue"].create_or_update_for_move(move, error_message)
                    queue.last_log_id = log.id
                    move.message_post(body=_("FBR submission failed and was queued for retry: %s") % error_message)
                else:
                    move.message_post(body=_("FBR submission failed: %s") % error_message)
                continue

            qr_data = response.get("qr_code") or {
                "fbr_invoice_number": response.get("fbr_invoice_number"),
                "odoo_invoice": move.name,
            }
            move.write(
                {
                    "bl_fbr_status": "submitted",
                    "bl_fbr_invoice_number": response.get("fbr_invoice_number"),
                    "bl_fbr_qr_data": move._bl_fbr_json(qr_data) if isinstance(qr_data, dict) else qr_data,
                    "bl_fbr_qr_code_image": move._bl_fbr_qr_image(qr_data),
                    "bl_fbr_error": False,
                    "bl_fbr_last_error_code": False,
                }
            )
            move.env["bl.fbr.queue"].search([("move_id", "=", move.id), ("status", "!=", "done")]).write(
                {"status": "done", "processed_at": fields.Datetime.now()}
            )
            move._bl_fbr_log(
                "submission",
                "success",
                request_payload=request_payload,
                response_payload=response.get("raw_response"),
                api_response=response,
            )
            move.message_post(body=_("FBR submission successful. Invoice number: %s") % move.bl_fbr_invoice_number)
        if validation_messages:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("FBR Validation Failed"),
                    "message": "\n".join(validation_messages),
                    "type": "warning",
                    "sticky": True,
                },
            }
        return True

    def action_bl_fbr_queue(self):
        for move in self:
            payload = move._bl_fbr_payload()
            errors = move._bl_fbr_validation_errors()
            if errors:
                move._bl_fbr_set_validation_result(errors, payload)
                continue
            config = move._bl_fbr_config()
            queue = self.env["bl.fbr.queue"].create_or_update_for_move(move, _("Queued by user."))
            queue.write({"last_error": False, "last_error_code": False, "connection_mode": config.connection_mode})
            move.write({"bl_fbr_status": "queued", "bl_fbr_payload_json": move._bl_fbr_json(payload)})
            move._bl_fbr_log("submission", "queued", request_payload=payload)
            move.message_post(body=_("FBR submission queued."))
        return True

    def action_bl_fbr_retry(self):
        for move in self:
            move._bl_fbr_log("retry", "success", request_payload={"invoice": move.name}, retry_no=move.bl_fbr_retry_count + 1)
            move.action_bl_fbr_submit()
        return True

    def action_bl_fbr_reset_status(self):
        for move in self:
            config = move._bl_fbr_config()
            if move.bl_fbr_invoice_number and config.connection_mode == "production":
                raise UserError(_("Production submitted invoices cannot be reset from this demo reset action."))
            move.write(
                {
                    "bl_fbr_status": "pending",
                    "bl_fbr_invoice_number": False,
                    "bl_fbr_qr_data": False,
                    "bl_fbr_qr_code_image": False,
                    "bl_fbr_error": False,
                    "bl_fbr_last_error_code": False,
                    "bl_fbr_payload_json": False,
                    "bl_fbr_response_json": False,
                    "bl_fbr_validation_summary": False,
                }
            )
            move.message_post(body=_("FBR status reset by manager."))
        return True

    def action_bl_fbr_view_logs(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("FBR Logs"),
            "res_model": "bl.fbr.log",
            "view_mode": "list,form",
            "domain": [("move_id", "=", self.id)],
        }

    def action_bl_fbr_view_queue(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("FBR Retry Queue"),
            "res_model": "bl.fbr.queue",
            "view_mode": "list,form",
            "domain": [("move_id", "=", self.id)],
        }

    def action_bl_fbr_open_readiness_wizard(self):
        self.ensure_one()
        wizard = self.env["bl.fbr.readiness.wizard"].create({"move_ids": [Command.set(self.ids)]})
        wizard.action_validate()
        return {
            "type": "ir.actions.act_window",
            "name": _("FBR Readiness"),
            "res_model": "bl.fbr.readiness.wizard",
            "view_mode": "form",
            "res_id": wizard.id,
            "target": "new",
        }

    def action_post(self):
        res = super().action_post()
        for move in self.filtered(lambda m: m.move_type in ("out_invoice", "out_refund")):
            config = move._bl_fbr_config()
            if config.enabled and config.auto_submit_on_post:
                if config.enable_retry_queue:
                    move.action_bl_fbr_queue()
                else:
                    move.action_bl_fbr_submit()
            elif move.bl_fbr_status in (False, "draft", "pending"):
                move.bl_fbr_status = "pending"
        return res

    def button_draft(self):
        for move in self:
            config = move._bl_fbr_config() if move.move_type in ("out_invoice", "out_refund") else False
            if config and config.lock_invoice_after_submission and move.bl_fbr_invoice_number and move.bl_fbr_status == "submitted":
                raise UserError(_("This invoice was submitted to FBR and cannot be reset to draft while FBR locking is enabled."))
        return super().button_draft()
