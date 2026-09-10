{
    "name": "Bashalog Pakistan FBR Digital Invoicing Connector",
    "version": "19.0.1.0.0",
    "category": "Accounting/Localization",
    "summary": "Pakistan FBR Digital Invoicing integration, validation, mock testing, QR invoices, and submission logs for Odoo",
    "description": """
Bashalog Pakistan FBR Digital Invoicing Connector
=================================================

Validates customer invoices and credit notes for Pakistan FBR Digital
Invoicing readiness, generates normalized payloads, supports mock success and
mock failure flows without real credentials, and provides a clean service layer
for sandbox/production API submission when credentials are available.
""",
    "author": "Bashalog",
    "website": "https://www.bashalog.com",
    "license": "LGPL-3",
    "depends": ["account", "product", "mail", "web"],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/sequence.xml",
        "data/fbr_error_codes.xml",
        "data/fbr_scenarios.xml",
        "data/ir_cron.xml",
        "views/bl_fbr_config_views.xml",
        "views/fbr_error_code_views.xml",
        "views/fbr_scenario_views.xml",
        "views/bl_fbr_log_views.xml",
        "views/bl_fbr_queue_views.xml",
        "views/account_move_views.xml",
        "views/product_template_views.xml",
        "views/res_partner_views.xml",
        "views/res_company_views.xml",
        "views/res_config_settings_views.xml",
        "wizards/bl_fbr_readiness_wizard_views.xml",
        "wizards/bl_fbr_bulk_submit_wizard_views.xml",
        "reports/account_move_report.xml",
        "views/menu_views.xml",
    ],
    "demo": ["demo/demo_data.xml"],
    "application": False,
    "auto_install": False,
    "installable": True,
}
