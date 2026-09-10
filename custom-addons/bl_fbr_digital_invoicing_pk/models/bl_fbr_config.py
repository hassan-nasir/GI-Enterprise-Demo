from odoo import api, fields, models


class BlFbrConfig(models.Model):
    _name = "bl.fbr.config"
    _description = "Bashalog FBR Configuration"
    _rec_name = "name"

    name = fields.Char(default="Default FBR Configuration", required=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        required=True,
    )
    enabled = fields.Boolean(string="Enable FBR Integration", default=True)
    connection_mode = fields.Selection(
        [
            ("mock_success", "Mock Success"),
            ("mock_failure", "Mock Failure"),
            ("sandbox", "Sandbox"),
            ("production", "Production"),
        ],
        default="mock_success",
        required=True,
    )
    auto_submit_on_post = fields.Boolean(default=False)
    enable_retry_queue = fields.Boolean(default=True)
    max_retry_attempts = fields.Integer(default=3)
    retry_delay_minutes = fields.Integer(default=15)
    timeout_seconds = fields.Integer(default=30)
    show_raw_payload_to_users = fields.Boolean(default=False)
    lock_invoice_after_submission = fields.Boolean(default=True)
    seller_ntn = fields.Char(string="Company Seller NTN")
    seller_strn = fields.Char(string="Company Seller STRN")
    seller_registration_no = fields.Char(string="Company Seller Registration No")
    seller_province = fields.Char(default="Sindh")
    seller_business_name_override = fields.Char()
    sandbox_url = fields.Char(string="Sandbox Base URL")
    production_url = fields.Char(string="Production Base URL")
    api_token = fields.Char(string="API Token", groups="base.group_system")
    notes = fields.Text()

    @api.model
    def get_config(self):
        config = self.search([("company_id", "=", self.env.company.id)], limit=1)
        if config:
            return config
        company = self.env.company
        return self.create(
            {
                "company_id": company.id,
                "seller_registration_no": company.bl_fbr_seller_registration_no,
                "seller_ntn": company.bl_fbr_ntn or company.vat,
                "seller_strn": company.bl_fbr_strn or company.company_registry,
                "seller_province": company.bl_fbr_seller_province or "Sindh",
                "seller_business_name_override": company.bl_fbr_business_name_override or company.name,
                "sandbox_url": company.bl_fbr_sandbox_base_url,
                "production_url": company.bl_fbr_production_base_url,
                "api_token": company.bl_fbr_api_token,
                "notes": "Demo mock mode only. No real FBR API credentials are required.",
            }
        )

    def sync_company_fields(self):
        for config in self:
            company = config.company_id
            config.write(
                {
                    "seller_registration_no": config.seller_registration_no or company.bl_fbr_seller_registration_no,
                    "seller_ntn": config.seller_ntn or company.bl_fbr_ntn or company.vat,
                    "seller_strn": config.seller_strn or company.bl_fbr_strn or company.company_registry,
                    "seller_province": config.seller_province or company.bl_fbr_seller_province,
                    "seller_business_name_override": config.seller_business_name_override or company.bl_fbr_business_name_override or company.name,
                    "sandbox_url": config.sandbox_url or company.bl_fbr_sandbox_base_url,
                    "production_url": config.production_url or company.bl_fbr_production_base_url,
                    "api_token": config.api_token or company.bl_fbr_api_token,
                }
            )
