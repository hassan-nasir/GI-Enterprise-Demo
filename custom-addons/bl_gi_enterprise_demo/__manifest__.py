{
    "name": "GI Enterprises (Pvt) Ltd — Auto Parts Manufacturing Demo",
    "version": "19.0.1.0.0",
    "category": "Manufacturing/Automotive",
    "summary": "Turnkey Tier-1 Automotive OEM Parts Manufacturing Demo with Multi-Unit Warehouses, MRP, Quality, Maintenance, and Pakistan FBR e-Invoicing",
    "description": """
GI Enterprises (Pvt) Ltd Demo
==============================
End-to-End Tier-1 Automotive OEM parts manufacturing operations demo for GI Enterprises (Pvt) Ltd (Karachi & Lahore).
Includes:
- Multi-facility setup (Head Office + Units I–V + Karachi Central Hub)
- Multi-level BOMs (Toyota Corolla Side Mirrors, Chrome Emblems, Decals, Plastics)
- Work Centers (Injection presses 150T/250T, Cleanroom Paint Shop, Chrome Plating, Press Stamping, Assembly)
- Quality Control Points (Incoming MFI, Coating Cross-Hatch DFT, Final Optical/Actuator tests)
- Corrective Maintenance workflow (Injection Press breakdown & repair)
- Pakistan Accounting (PKR, 18% Sales Tax, WHT)
- FBR Digital Invoicing Integration with Pakistan Customs HS Codes (e.g. 7009.10.00, 8708.29.31)
""",
    "author": "Bashalog",
    "website": "https://www.bashalog.com",
    "license": "LGPL-3",
    "depends": [
        "web_enterprise",
        "contacts",
        "sale_management",
        "purchase_stock",
        "mrp",
        "mrp_workorder",
        "mrp_accountant",
        "stock",
        "stock_barcode",
        "quality_control",
        "quality_mrp",
        "maintenance",
        "mrp_maintenance",
        "account",
        "account_reports",
        "l10n_pk",
        "bl_fbr_digital_invoicing_pk",
    ],
    "data": [
        "views/workcenter_views.xml",
        "views/equipment_views.xml",
        "views/demo_banner_views.xml",
    ],
    "application": False,
    "auto_install": False,
    "installable": True,
    "post_init_hook": "post_init_hook",
}

