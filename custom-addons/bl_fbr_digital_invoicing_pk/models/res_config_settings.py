from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    bl_fbr_enable_integration = fields.Boolean("Enable FBR Integration", related="bl_fbr_config_id.enabled", readonly=False)
    bl_fbr_connection_mode = fields.Selection(string="Connection Mode", related="bl_fbr_config_id.connection_mode", readonly=False)
    bl_fbr_auto_submit_on_post = fields.Boolean("Auto Submit on Post", related="bl_fbr_config_id.auto_submit_on_post", readonly=False)
    bl_fbr_enable_retry_queue = fields.Boolean("Enable Retry Queue", related="bl_fbr_config_id.enable_retry_queue", readonly=False)
    bl_fbr_max_retry_attempts = fields.Integer("Max Retry Attempts", related="bl_fbr_config_id.max_retry_attempts", readonly=False)
    bl_fbr_retry_delay_minutes = fields.Integer("Retry Delay (Minutes)", related="bl_fbr_config_id.retry_delay_minutes", readonly=False)
    bl_fbr_timeout_seconds = fields.Integer("Timeout (Seconds)", related="bl_fbr_config_id.timeout_seconds", readonly=False)
    bl_fbr_show_raw_payload_to_users = fields.Boolean("Show Raw Payload to Users", related="bl_fbr_config_id.show_raw_payload_to_users", readonly=False)
    bl_fbr_lock_invoice_after_submission = fields.Boolean("Lock Submitted Invoices", related="bl_fbr_config_id.lock_invoice_after_submission", readonly=False)
    bl_fbr_config_id = fields.Many2one("bl.fbr.config", default=lambda self: self.env["bl.fbr.config"].get_config())

    bl_fbr_sandbox_base_url = fields.Char("Sandbox Base URL", related="company_id.bl_fbr_sandbox_base_url", readonly=False)
    bl_fbr_production_base_url = fields.Char("Production Base URL", related="company_id.bl_fbr_production_base_url", readonly=False)
    bl_fbr_api_token = fields.Char("API Token", related="company_id.bl_fbr_api_token", readonly=False)
    bl_fbr_company_seller_registration_no = fields.Char("Seller Registration No.", related="company_id.bl_fbr_seller_registration_no", readonly=False)
    bl_fbr_company_ntn = fields.Char("Seller NTN", related="company_id.bl_fbr_ntn", readonly=False)
    bl_fbr_company_strn = fields.Char("Seller STRN", related="company_id.bl_fbr_strn", readonly=False)
    bl_fbr_seller_province = fields.Char("Seller Province", related="company_id.bl_fbr_seller_province", readonly=False)
    bl_fbr_seller_business_name_override = fields.Char("Business Name Override", related="company_id.bl_fbr_business_name_override", readonly=False)
