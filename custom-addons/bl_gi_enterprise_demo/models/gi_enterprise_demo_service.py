# -*- coding: utf-8 -*-
import base64
import json
import logging
from pathlib import Path
from datetime import date, timedelta
from markupsafe import Markup
from odoo import Command, fields, models

_logger = logging.getLogger(__name__)

MODULE = "bl_gi_enterprise_demo"

CUSTOMERS = [
    {
        "key": "customer_atlas_honda",
        "name": "Atlas Honda Limited",
        "street": "26-27 KM, Lahore-Sheikhupura Road, Sheikhupura",
        "city": "Sheikhupura",
        "zip": "39350",
        "province": "Punjab",
        "registration_type": "registered",
        "registration_no": "0710111-3",
        "strn": "03-01-8714-001-28",
        "buyer_type": "Registered",
        "term": "30",
        "logo": "partner_atlas_honda.png",
    },
    {
        "key": "customer_yamaha_motor",
        "name": "Yamaha Motor Pakistan (Pvt) Ltd",
        "street": "Sector 38-A, Deh Landhi, Bin Qasim Industrial Park",
        "city": "Karachi",
        "zip": "75120",
        "province": "Sindh",
        "registration_type": "registered",
        "registration_no": "4125890-2",
        "strn": "17-00-8711-001-55",
        "buyer_type": "Registered",
        "term": "30",
        "logo": "partner_yamaha.png",
    },
    {
        "key": "customer_pak_suzuki",
        "name": "Pak Suzuki Motor Company Ltd (Motorcycle Division)",
        "street": "DSU-13, Pakistan Steel Industrial Estate, Bin Qasim",
        "city": "Karachi",
        "zip": "75000",
        "province": "Sindh",
        "registration_type": "registered",
        "registration_no": "0710166-0",
        "strn": "02-01-8708-002-11",
        "buyer_type": "Registered",
        "term": "30",
        "logo": "partner_kia.png",
    },
    {
        "key": "customer_master_changan",
        "name": "Master Changan Motors Ltd",
        "street": "Sector 8-A, Korangi Industrial Area",
        "city": "Karachi",
        "zip": "74900",
        "province": "Sindh",
        "registration_type": "registered",
        "registration_no": "7936521-8",
        "strn": "32-77-8708-003-45",
        "buyer_type": "Registered",
        "term": "30",
        "logo": "partner_changan.png",
    },
]

VENDORS = [
    {
        "key": "vendor_sabic_polymer",
        "name": "SABIC Polymer & Optical Acrylics Pakistan",
        "street": "Executive Tower, Main Clifton Road",
        "city": "Karachi",
        "province": "Sindh",
        "ntn": "3100293-1",
        "term": "30",
        "logo": "raw_abs_pellets.jpg",
    },
    {
        "key": "vendor_atotech_chemicals",
        "name": "Atotech Surface Finishing & Vacuum Coating Chemicals",
        "street": "Plot 42, Sector 15, Korangi Industrial Area",
        "city": "Karachi",
        "province": "Sindh",
        "ntn": "2847192-5",
        "term": "30",
        "logo": "plant_metal_plating.jpg",
    },
    {
        "key": "vendor_aisha_steel",
        "name": "Aisha Steel Mills Ltd",
        "street": "Downstream Industrial Estate, Bin Qasim",
        "city": "Karachi",
        "province": "Sindh",
        "ntn": "2255104-9",
        "term": "45",
        "logo": "raw_steel_coil.jpg",
    },
    {
        "key": "vendor_osram_lighting",
        "name": "Osram / Lumileds Automotive Bulbs & Sockets",
        "street": "Plot 18, Commercial Zone, Gulberg III",
        "city": "Lahore",
        "province": "Punjab",
        "ntn": "4189302-7",
        "term": "30",
        "logo": "part_bulb_12v.png",
    },
]


class GiEnterpriseDemoService(models.AbstractModel):
    _name = "bl.gi.enterprise.demo.service"
    _description = "GI Enterprises Auto Parts Demo Automation Service"

    def _image(self, filename):
        if not filename:
            return False
        path = Path(__file__).resolve().parent.parent / "static" / "src" / "img" / filename
        if path.exists():
            return base64.b64encode(path.read_bytes())
        return False

    def _upsert(self, xmlid, model_name, values):
        full_xmlid = f"{MODULE}.{xmlid}"
        record = self.env.ref(full_xmlid, raise_if_not_found=False)
        if record and record.exists():
            record.write(values)
            return record

        imd = self.env["ir.model.data"].search([("module", "=", MODULE), ("name", "=", xmlid)], limit=1)
        record = self.env[model_name].create(values)
        if imd:
            imd.write({"res_id": record.id, "model": model_name})
        else:
            self.env["ir.model.data"].create(
                {
                    "module": MODULE,
                    "name": xmlid,
                    "model": model_name,
                    "res_id": record.id,
                    "noupdate": True,
                }
            )
        return record

    def _company(self):
        company = self.env.ref("base.main_company")
        pk_currency = self.env.ref("base.PKR")
        country = self.env.ref("base.pk")
        sindh = self.env["res.country.state"].search([("country_id", "=", country.id), ("name", "ilike", "Sindh")], limit=1)

        logo_b64 = self._image("gi_logo.png")
        vals = {
            "name": "GI Enterprises (Pvt) Ltd",
            "street": "Plot No. 43/1, Sector 12-C, S.I.T.E. II Industrial Area",
            "city": "Karachi",
            "zip": "75850",
            "state_id": sindh.id if sindh else False,
            "country_id": country.id,
            "phone": "+92 21 36625770",
            "email": "info@gienterprises.com.pk",
            "website": "https://www.gienterprises.com.pk",
            "currency_id": pk_currency.id,
            "vat": "0658921-4",
        }
        if logo_b64:
            vals["logo"] = logo_b64

        company.write(vals)

        # Setup FBR credentials on company
        if "bl_fbr_ntn" in company._fields:
            company.write(
                {
                    "bl_fbr_ntn": "0658921-4",
                    "bl_fbr_strn": "11-00-8708-002-19",
                    "bl_fbr_seller_registration_no": "0658921-4",
                    "bl_fbr_seller_province": "Sindh",
                    "bl_fbr_business_name_override": "GI Enterprises (Pvt) Ltd",
                }
            )
        # Setup bl.fbr.config
        if "bl.fbr.config" in self.env:
            fbr_cfg = self.env["bl.fbr.config"].search([("company_id", "=", company.id)], limit=1)
            cfg_vals = {
                "name": "GI Enterprises FBR Configuration",
                "company_id": company.id,
                "enabled": True,
                "connection_mode": "mock_success",
                "seller_ntn": "0658921-4",
                "seller_strn": "11-00-8708-002-19",
                "seller_registration_no": "0658921-4",
                "seller_province": "Sindh",
                "seller_business_name_override": "GI Enterprises (Pvt) Ltd",
                "lock_invoice_after_submission": True,
            }
            if not fbr_cfg:
                self.env["bl.fbr.config"].create(cfg_vals)
            else:
                fbr_cfg.write(cfg_vals)

        # Enable Work Orders & Work Centers across Odoo menus
        settings = self.env["res.config.settings"].create({
            "group_mrp_routings": True,
            "group_mrp_workorder_dependencies": True,
        })
        settings.execute()

        # Link Administrator to MRP, Work Center, and Full Accounting groups
        admin_user = self.env.ref("base.user_admin", raise_if_not_found=False)
        group_routings = self.env.ref("mrp.group_mrp_routings", raise_if_not_found=False)
        group_mgr = self.env.ref("mrp.group_mrp_manager", raise_if_not_found=False)
        acc_groups = [
            self.env.ref("account.group_account_readonly", raise_if_not_found=False),
            self.env.ref("account.group_account_invoice", raise_if_not_found=False),
            self.env.ref("account.group_account_user", raise_if_not_found=False),
            self.env.ref("account.group_account_manager", raise_if_not_found=False),
        ]
        for grp in [group_routings, group_mgr] + acc_groups:
            if grp and admin_user and admin_user not in grp.user_ids:
                grp.write({"user_ids": [Command.link(admin_user.id)]})

        # Ensure Root Accounting Menu is visible and named 'Accounting'
        invoicing_menu = self.env.ref("account.menu_finance", raise_if_not_found=False)
        if invoicing_menu:
            invoicing_menu.write({"name": "Accounting"})

        # Create Demo Shop Floor Operator Employees
        self._upsert("emp_tariq", "hr.employee", {
            "name": "Muhammad Tariq — Senior Assembly Operator",
            "company_id": company.id,
            "pin": "1234",
            "barcode": "EMPTARIQ01",
        })
        self._upsert("emp_zubair", "hr.employee", {
            "name": "Zubair Ahmed — IATF 16949 QC Inspector",
            "company_id": company.id,
            "pin": "5678",
            "barcode": "EMPZUBAIR02",
        })

        return company

    def _taxes(self, company, accounts=None):
        account_tax = self.env["account.tax"]
        tax_group_obj = self.env["account.tax.group"]

        # Rename any legacy 'Tax 15%' group to 'GST 18%'
        for tg in tax_group_obj.search([("name", "ilike", "15%")]):
            tg.write({"name": "GST 18%"})

        tax_group_18 = tax_group_obj.search([("name", "=", "GST 18%"), ("company_id", "=", company.id)], limit=1)
        if not tax_group_18:
            tax_group_18 = tax_group_obj.search([("name", "=", "GST 18%")], limit=1)
        if not tax_group_18:
            tax_group_18 = self._upsert("tax_group_gst_18", "account.tax.group", {"name": "GST 18%", "company_id": company.id})

        # Archive any legacy 15% taxes from standard chart of accounts
        for legacy in account_tax.search([("company_id", "=", company.id), ("amount", "=", 15.0)]):
            legacy.write({"active": False})

        # 1. Output GST 18% (Sales)
        sale_tax = account_tax.search(
            [("company_id", "=", company.id), ("type_tax_use", "=", "sale"), ("amount", "=", 18.0)],
            limit=1,
        )
        if not sale_tax:
            sale_tax = self._upsert(
                "tax_gst_sale_18",
                "account.tax",
                {
                    "name": "Output GST 18% (Automotive Parts)",
                    "amount_type": "percent",
                    "amount": 18.0,
                    "type_tax_use": "sale",
                    "tax_group_id": tax_group_18.id,
                    "company_id": company.id,
                    "description": "GST 18%",
                },
            )
        else:
            sale_tax.write({"tax_group_id": tax_group_18.id, "active": True})

        # 2. Input GST 18% (Purchases)
        purchase_tax = account_tax.search(
            [("company_id", "=", company.id), ("type_tax_use", "=", "purchase"), ("amount", "=", 18.0)],
            limit=1,
        )
        if not purchase_tax:
            purchase_tax = self._upsert(
                "tax_gst_purchase_18",
                "account.tax",
                {
                    "name": "Input GST 18% (Raw Materials & Supplies)",
                    "amount_type": "percent",
                    "amount": 18.0,
                    "type_tax_use": "purchase",
                    "tax_group_id": tax_group_18.id,
                    "company_id": company.id,
                    "description": "Input GST 18%",
                },
            )
        else:
            purchase_tax.write({"tax_group_id": tax_group_18.id, "active": True})

        # Configure tax repartition accounts to route 18% GST to account 251000
        if accounts and "acc_tax" in accounts:
            for tax_rec in [sale_tax, purchase_tax]:
                for rep in tax_rec.invoice_repartition_line_ids:
                    if rep.repartition_type == "tax":
                        rep.write({"account_id": accounts["acc_tax"].id})
                for rep in tax_rec.refund_repartition_line_ids:
                    if rep.repartition_type == "tax":
                        rep.write({"account_id": accounts["acc_tax"].id})

        # Configure Pakistan Domestic Fiscal Position
        pk_country = self.env.ref("base.pk", raise_if_not_found=False)
        fp_domestic = self.env["account.fiscal.position"].search([("company_id", "=", company.id), ("name", "ilike", "Domestic")], limit=1)
        if fp_domestic and pk_country:
            fp_domestic.write({
                "name": "Domestic (Pakistan Taxable)",
                "country_id": pk_country.id,
                "auto_apply": True,
                "sequence": 10,
            })
        fp_foreign = self.env["account.fiscal.position"].search([("company_id", "=", company.id), ("name", "ilike", "Foreign")], limit=1)
        if fp_foreign:
            fp_foreign.write({
                "name": "Export / Foreign Trade (0% Tax)",
                "sequence": 20,
            })

        # Set company default taxes to 18% GST so new invoices automatically use 18%
        company.write({
            "account_sale_tax_id": sale_tax.id,
            "account_purchase_tax_id": purchase_tax.id,
        })

        return sale_tax, purchase_tax

    def _warehouses(self, company):
        main_wh = self.env["stock.warehouse"].search([("company_id", "=", company.id)], limit=1)
        if main_wh:
            main_wh.write({"name": "GI Enterprises — S.I.T.E. II Plant"})
        else:
            main_wh = self._upsert("wh_site2", "stock.warehouse", {"name": "GI Enterprises — S.I.T.E. II Plant", "code": "SITE2", "company_id": company.id})

        return {"site2": main_wh, "main": main_wh}

    def _workcenters(self, company):
        wc_specs = [
            ("wc_mold_150t", "WC-MOLD-01 — Precision Plastic Injection Molding Press (150T)", "MOLD-01", 3120.0, 0.0, 0.0, "machine_inj_press.jpg", "Heavy-duty 150-ton hydraulic injection molding machine for high-clarity optical PMMA lenses and precision clear components."),
            ("wc_mold_250t", "WC-MOLD-02 — Heavy-Duty Plastic Injection Molding Press (250T)", "MOLD-02", 3300.0, 0.0, 0.0, "machine_inj_press.jpg", "Heavy-duty 250-ton toggle injection molding press for structural ABS rear housings, side covers, and high-impact structural shells."),
            ("wc_asm_mirror", "WC-ASM-01 — Final Assembly & Quality Inspection Line", "ASM-01", 1800.0, 0.0, 0.0, "plant_assembly_line.jpg", "Conveyorized lighting assembly bench with 12V dual-filament photometric testing, bulb socket wiring, and ultrasonic hermetic sealing."),
        ]
        workcenters = {}
        for key, name, code, costs_hour, t_start, t_stop, img_file, note in wc_specs:
            vals = {
                "name": name,
                "code": code,
                "costs_hour": costs_hour,
                "time_start": t_start,
                "time_stop": t_stop,
                "company_id": company.id,
                "note": f"<p>{note}</p>",
            }
            img_b64 = self._image(img_file)
            if img_b64:
                vals["image_1920"] = img_b64

            wc = self._upsert(key, "mrp.workcenter", vals)
            workcenters[key] = wc

        # Remove any other unused workcenters from database so dashboard is ultra clean
        allowed_ids = [wc.id for wc in workcenters.values()]
        for old_wc in self.env["mrp.workcenter"].search([("company_id", "=", company.id), ("id", "not in", allowed_ids)]):
            try:
                old_wc.unlink()
            except Exception:
                old_wc.write({"active": False})

        return workcenters

    def _chart_of_accounts(self, company):
        acc_specs = [
            ("acc_bank", "101400", "Bank Account (MCB Bank)", "asset_cash", False),
            ("acc_recv", "121000", "Accounts Receivable (Trade Debtors)", "asset_receivable", True),
            ("acc_stock", "110100", "Inventory / Stock", "asset_current", False),
            ("acc_payable", "211000", "Accounts Payable (Trade Creditors)", "liability_payable", True),
            ("acc_tax", "251000", "Sales Tax (18% FBR GST)", "liability_current", False),
            ("acc_sales", "400000", "Product Sales Revenue", "income", False),
            ("acc_cogs", "500000", "Cost of Goods Sold (COGS)", "expense_direct_cost", False),
            ("acc_expenses", "600000", "Factory & Operating Expenses", "expense", False),
        ]
        accounts = {}
        for key, code, name, acc_type, reconcile in acc_specs:
            acc = self.env["account.account"].search([("code", "=", code), ("company_ids", "in", company.id)], limit=1)
            vals = {
                "name": name,
                "code": code,
                "account_type": acc_type,
                "company_ids": [Command.set([company.id])],
            }
            if reconcile:
                vals["reconcile"] = True
            if acc:
                acc.write(vals)
            else:
                acc = self._upsert(key, "account.account", vals)
            accounts[key] = acc
        return accounts

    def _categories(self, company, accounts):
        cat_specs = [
            ("cat_fg", "Finished Goods (Motorcycle Parts)", accounts["acc_sales"], accounts["acc_cogs"], accounts["acc_stock"]),
            ("cat_sa", "Sub-Assemblies (In-House Parts)", accounts["acc_sales"], accounts["acc_cogs"], accounts["acc_stock"]),
            ("cat_rm", "Raw Materials & Components", accounts["acc_sales"], accounts["acc_cogs"], accounts["acc_stock"]),
            ("cat_sp", "Maintenance & Factory Spares", accounts["acc_sales"], accounts["acc_expenses"], accounts["acc_stock"]),
        ]
        categories = {}
        for key, name, income_acc, expense_acc, stock_acc in cat_specs:
            vals = {
                "name": name,
                "property_cost_method": "standard",
                "property_valuation": "real_time",
                "property_account_income_categ_id": income_acc.id,
                "property_account_expense_categ_id": expense_acc.id,
                "property_stock_valuation_account_id": stock_acc.id,
                "account_stock_variation_id": expense_acc.id,
            }
            cat = self._upsert(key, "product.category", vals)
            categories[key] = cat
        return categories

    def _partners(self, company, accounts=None):
        country = self.env.ref("base.pk")
        term_30 = self.env.ref("account.account_payment_term_30days")
        term_45 = self.env.ref("account.account_payment_term_45days")
        terms = {"30": term_30, "45": term_45}
        fp_domestic = self.env["account.fiscal.position"].search([("company_id", "=", company.id), ("name", "ilike", "Domestic")], limit=1)

        customers = {}
        for item in CUSTOMERS:
            vals = {
                "name": item["name"],
                "company_type": "company",
                "customer_rank": 1,
                "supplier_rank": 0,
                "street": item["street"],
                "city": item["city"],
                "zip": item["zip"],
                "country_id": country.id,
                "email": f"{item['key']}@gi-oem-demo.invalid",
                "property_payment_term_id": terms.get(item["term"], term_30).id,
                "bl_fbr_registration_type": item["registration_type"],
                "bl_fbr_registration_no": item["registration_no"],
                "bl_fbr_ntn": item["registration_no"],
                "bl_fbr_strn": item.get("strn", False),
                "bl_fbr_province": item["province"],
                "bl_fbr_buyer_type": item["buyer_type"],
            }
            if fp_domestic:
                vals["property_account_position_id"] = fp_domestic.id
            if accounts and "acc_recv" in accounts:
                vals["property_account_receivable_id"] = accounts["acc_recv"].id
            if item.get("logo"):
                img_b64 = self._image(item["logo"])
                if img_b64:
                    vals["image_1920"] = img_b64

            customers[item["key"]] = self._upsert(item["key"], "res.partner", vals)

        vendors = {}
        for item in VENDORS:
            vals = {
                "name": item["name"],
                "company_type": "company",
                "customer_rank": 0,
                "supplier_rank": 1,
                "street": item["street"],
                "city": item["city"],
                "country_id": country.id,
                "email": f"{item['key']}@gi-vendor-demo.invalid",
                "property_supplier_payment_term_id": terms.get(item["term"], term_30).id,
                "bl_fbr_registration_type": "registered",
                "bl_fbr_registration_no": item["ntn"],
                "bl_fbr_ntn": item["ntn"],
                "bl_fbr_province": item["province"],
            }
            if fp_domestic:
                vals["property_account_position_id"] = fp_domestic.id
            if accounts and "acc_payable" in accounts:
                vals["property_account_payable_id"] = accounts["acc_payable"].id
            if item.get("logo"):
                img_b64 = self._image(item["logo"])
                if img_b64:
                    vals["image_1920"] = img_b64

            vendors[item["key"]] = self._upsert(item["key"], "res.partner", vals)
        return customers, vendors

    def _products(self, company, taxes, vendors=None, categories=None):
        sale_tax, purchase_tax = taxes
        unit = self.env.ref("uom.product_uom_unit")
        kg = self.env.ref("uom.product_uom_kgm")
        scenario = self.env.ref("bl_fbr_digital_invoicing_pk.scenario_standard_taxable_sale", raise_if_not_found=False)

        # Product definitions: (key, name, default_code, uom, cost, list_price, hs_code, is_fg, is_sa, img_file, vendor_key, vendor_price)
        items = [
            # 1. Flagship Showcase Finished Good
            ("prod_taillight_cd70", "Honda CD70 Motorcycle Tail Light Complete Assembly", "GI-TL-CD70-01", unit, 775.0, 1450.0, "85122000", True, False, "prod_taillight_cd70.png", None, 0),

            # 2. In-House Molded Sub-Assemblies (Manufactured by GI Enterprises on Injection Presses)
            ("prod_sa_tl_lens", "Red Optical PMMA Tail Light Lens Cover", "GI-TL-LENS01", unit, 180.0, 0, "85129000", False, True, "prod_lens_red.png", None, 0),
            ("prod_sa_tl_base", "Black High-Impact ABS Housing Base Shell", "GI-TL-BASE01", unit, 240.0, 0, "85129000", False, True, "part_tl_base.png", None, 0),

            # 3. Direct Raw Materials & Purchased Components
            ("prod_rm_pmma", "Optical Grade Red PMMA Acrylic Polymer Granules", "RM-PMMA-01", kg, 850.0, 0, "39061000", False, False, "raw_pmma_red.jpg", "vendor_sabic_polymer", 850.0),
            ("prod_rm_abs", "High-Impact Automotive Grade ABS Polymer Pellets", "RM-ABS-01", kg, 650.0, 0, "39033000", False, False, "raw_abs_pellets.jpg", "vendor_sabic_polymer", 650.0),
            ("prod_rm_bulb_12v", "12V 21/5W Dual-Filament Bulb & Socket Harness", "RM-BLB-12V", unit, 210.0, 0, "85392990", False, False, "part_bulb_12v.png", "vendor_osram_lighting", 210.0),
            ("prod_rm_fasteners", "Mounting Hardware Screws & EPDM Seal Kit", "RM-FAS-01", unit, 70.0, 0, "73181590", False, False, "part_fasteners_screws.png", "vendor_aisha_steel", 70.0),

            # 4. Additional Catalog OEM Products (For Catalog Richness)
            ("prod_decal_cd70", "Honda CD70 Fuel Tank Decal Graphics Set", "GI-DC-CD70-01", unit, 270.0, 650.0, "87141020", True, False, "decal_cd70.png", None, 0),
            ("prod_sidecover_cd70", "Honda CD70 Side Cover Plastic (Black)", "GI-PL-CD70-SC01", unit, 485.0, 1150.0, "87141020", True, False, "sidecover_cd70.png", None, 0),
            ("prod_emblem_cd70", "Chrome Plated 'CD70' 3D Fuel Tank Emblem Badge", "GI-EM-CD70-01", unit, 160.0, 420.0, "87141020", True, False, "emblem_cd70.png", None, 0),
        ]

        products = {}
        for key, name, code, uom, cost, price, hs_code, is_fg, is_sa, img_file, vkey, vprice in items:
            tmpl_vals = {
                "name": name,
                "default_code": code,
                "type": "consu",
                "is_storable": True,
                "sale_ok": is_fg,
                "purchase_ok": not is_fg and not is_sa,
                "tracking": "lot" if is_fg else "none",
                "uom_id": uom.id,
                "standard_price": cost,
                "list_price": price,
                "taxes_id": [Command.set([sale_tax.id])] if is_fg else [],
                "supplier_taxes_id": [Command.set([purchase_tax.id])] if not is_fg and not is_sa else [],
                "invoice_policy": "order",
                "bl_fbr_item_code": code,
                "bl_fbr_hs_code": hs_code,
                "bl_fbr_uom": "Numbers, pieces, units",
                "bl_fbr_sale_type": "Standard taxable sale",
            }
            if categories:
                if is_fg:
                    tmpl_vals["categ_id"] = categories["cat_fg"].id
                elif is_sa:
                    tmpl_vals["categ_id"] = categories["cat_sa"].id
                else:
                    tmpl_vals["categ_id"] = categories["cat_rm"].id

            if img_file:
                b64_img = self._image(img_file)
                if b64_img:
                    tmpl_vals["image_1920"] = b64_img

            if scenario:
                tmpl_vals["bl_fbr_scenario_id"] = scenario.id
                tmpl_vals["bl_fbr_scenario"] = scenario.code

            prod_tmpl = self._upsert(key, "product.template", tmpl_vals)
            products[key] = prod_tmpl.product_variant_id

            if vkey and vendors and vendors.get(vkey):
                supp_vals = {
                    "partner_id": vendors[vkey].id,
                    "product_tmpl_id": prod_tmpl.id,
                    "price": vprice,
                    "min_qty": 1.0,
                    "company_id": company.id,
                }
                self._upsert(f"supp_{key}", "product.supplierinfo", supp_vals)

        return products

    def _boms(self, company, products, workcenters):
        # Remove any legacy BOMs
        for old_bom in self.env["mrp.bom"].search([("company_id", "=", company.id)]):
            try:
                old_bom.bom_line_ids.unlink()
                old_bom.operation_ids.unlink()
                old_bom.unlink()
            except Exception:
                old_bom.write({"active": False})

        def set_bom(xmlid, vals):
            bom = self.env.ref(f"{MODULE}.{xmlid}", raise_if_not_found=False)
            if bom and bom.exists():
                bom.bom_line_ids.unlink()
                bom.operation_ids.unlink()
                bom.write(vals)
                return bom
            return self._upsert(xmlid, "mrp.bom", vals)

        # 1. Sub-Assembly BOM: Red PMMA Lens Cover (Molded in-house on 150T Press)
        # Material: 0.12 kg PMMA Granules (PKR 102.00) + Molding Operation (PKR 78.00) = Cost PKR 180.00
        bom_lens = set_bom(
            "bom_tl_lens",
            {
                "product_tmpl_id": products["prod_sa_tl_lens"].product_tmpl_id.id,
                "product_qty": 1.0,
                "type": "normal",
                "company_id": company.id,
                "bom_line_ids": [
                    Command.create({"product_id": products["prod_rm_pmma"].id, "product_qty": 0.12}),
                ],
                "operation_ids": [
                    Command.create({
                        "name": "OP-MOLD-01: Precision Optical Lens Injection Molding & Gate Trimming",
                        "workcenter_id": workcenters["wc_mold_150t"].id,
                        "time_mode": "manual",
                        "time_cycle_manual": 1.5,
                        "company_id": company.id,
                    }),
                ],
            },
        )

        # 2. Sub-Assembly BOM: Black ABS Base Housing (Molded in-house on 250T Press)
        # Material: 0.20 kg ABS Pellets (PKR 130.00) + Molding Operation (PKR 110.00) = Cost PKR 240.00
        bom_base = set_bom(
            "bom_tl_base",
            {
                "product_tmpl_id": products["prod_sa_tl_base"].product_tmpl_id.id,
                "product_qty": 1.0,
                "type": "normal",
                "company_id": company.id,
                "bom_line_ids": [
                    Command.create({"product_id": products["prod_rm_abs"].id, "product_qty": 0.20}),
                ],
                "operation_ids": [
                    Command.create({
                        "name": "OP-MOLD-02: Heavy-Duty Base Housing Injection Molding & Degating",
                        "workcenter_id": workcenters["wc_mold_250t"].id,
                        "time_mode": "manual",
                        "time_cycle_manual": 2.0,
                        "company_id": company.id,
                    }),
                ],
            },
        )

        # 3. Final Assembly BOM: Honda CD70 Tail Light Complete Assembly
        # 4 Components (PKR 700.00) + 1 Assembly Operation (PKR 75.00) = Total COGS PKR 775.00
        bom_tl_cd70_final = set_bom(
            "bom_tl_cd70_final",
            {
                "product_tmpl_id": products["prod_taillight_cd70"].product_tmpl_id.id,
                "product_qty": 1.0,
                "type": "normal",
                "company_id": company.id,
                "bom_line_ids": [
                    Command.create({"product_id": products["prod_sa_tl_lens"].id, "product_qty": 1.0}),
                    Command.create({"product_id": products["prod_sa_tl_base"].id, "product_qty": 1.0}),
                    Command.create({"product_id": products["prod_rm_bulb_12v"].id, "product_qty": 1.0}),
                    Command.create({"product_id": products["prod_rm_fasteners"].id, "product_qty": 1.0}),
                ],
                "operation_ids": [
                    Command.create({
                        "name": "OP-ASM: Final Electrical Lighting Assembly & Photometric Inspection",
                        "workcenter_id": workcenters["wc_asm_mirror"].id,
                        "time_mode": "manual",
                        "time_cycle_manual": 2.5,
                        "company_id": company.id,
                    }),
                ],
            },
        )

        return {
            "lens": bom_lens,
            "base": bom_base,
            "tl_final": bom_tl_cd70_final,
        }

    def _quality_points(self, company, products, warehouses, boms):
        # Remove any legacy quality points
        for old_qp in self.env["quality.point"].search([("company_id", "=", company.id)]):
            old_qp.unlink()

        site2_wh = warehouses["site2"]
        site2_mo = site2_wh.manu_type_id

        tt_passfail = self.env["quality.point.test_type"].search([("technical_name", "=", "passfail")], limit=1)

        # 1. In-Line Quality Check on Final Assembly
        op_asm = boms["tl_final"].operation_ids[:1]
        if site2_mo:
            qp_fin_vals = {
                "title": "QC-1: Final 12V Dual-Filament (Tail 5W / Brake 21W) Photometric & Continuity Test",
                "product_ids": [Command.set([products["prod_taillight_cd70"].id])],
                "picking_type_ids": [Command.set([site2_mo.id])],
                "company_id": company.id,
                "measure_on": "product",
                "is_workorder_step": True,
                "note": "<p>Apply 12.0V DC power. Verify Tail Light circuit draw (0.42A ± 0.05A) and Brake Light circuit draw (1.75A ± 0.10A). Inspect red optical beam dispersion and hermetic EPDM gasket seal.</p>",
            }
            if op_asm:
                qp_fin_vals["operation_id"] = op_asm.id
            if tt_passfail:
                qp_fin_vals["test_type_id"] = tt_passfail.id
            self._upsert("qp_final_taillight", "quality.point", qp_fin_vals)

        # 2. In-Line Quality Check on Plastic Injection Molding (Lens)
        op_mold_lens = boms["lens"].operation_ids[:1]
        if site2_mo:
            qp_mold_lens_vals = {
                "title": "QC-MOLD-01: Red Optical PMMA Lens Clarity, Surface Finish & Gate Flash Inspection",
                "product_ids": [Command.set([products["prod_sa_tl_lens"].id])],
                "picking_type_ids": [Command.set([site2_mo.id])],
                "company_id": company.id,
                "measure_on": "product",
                "is_workorder_step": True,
                "note": "<p>Inspect molded PMMA lens for optical clarity, uniform red pigment dispersion (SAE/ECE standard), no sink marks or bubbles, and clean sprue gate cut.</p>",
            }
            if op_mold_lens:
                qp_mold_lens_vals["operation_id"] = op_mold_lens.id
            if tt_passfail:
                qp_mold_lens_vals["test_type_id"] = tt_passfail.id
            self._upsert("qp_mold_lens", "quality.point", qp_mold_lens_vals)

        # 3. In-Line Quality Check on Plastic Injection Molding (Base Housing)
        op_mold_base = boms["base"].operation_ids[:1]
        if site2_mo:
            qp_mold_base_vals = {
                "title": "QC-MOLD-02: Black ABS Base Housing Structural Boss & Screw Fit Inspection",
                "product_ids": [Command.set([products["prod_sa_tl_base"].id])],
                "picking_type_ids": [Command.set([site2_mo.id])],
                "company_id": company.id,
                "measure_on": "product",
                "is_workorder_step": True,
                "note": "<p>Inspect molded ABS housing base for high-impact structural wall thickness, clean wire harness aperture, and brass insert screw thread boss alignment.</p>",
            }
            if op_mold_base:
                qp_mold_base_vals["operation_id"] = op_mold_base.id
            if tt_passfail:
                qp_mold_base_vals["test_type_id"] = tt_passfail.id
            self._upsert("qp_mold_base", "quality.point", qp_mold_base_vals)

    def _reordering_rules(self, company, warehouses, products, vendors=None, taxes=None):
        # Remove legacy orderpoints
        for old_op in self.env["stock.warehouse.orderpoint"].search([("company_id", "=", company.id)]):
            old_op.unlink()

        # Clean all old purchase orders and associated pickings
        for old_po in self.env["purchase.order"].search([("company_id", "=", company.id)]):
            try:
                for p in old_po.picking_ids:
                    for m in p.move_ids:
                        self.env.cr.execute("DELETE FROM stock_move_line WHERE move_id = %s", (m.id,))
                        self.env.cr.execute("DELETE FROM stock_move WHERE id = %s", (m.id,))
                    self.env.cr.execute("DELETE FROM stock_picking WHERE id = %s", (p.id,))
                self.env.cr.execute("DELETE FROM purchase_order_line WHERE order_id = %s", (old_po.id,))
                self.env.cr.execute("DELETE FROM purchase_order WHERE id = %s", (old_po.id,))
            except Exception:
                pass

        if not vendors or not taxes:
            return

        wh = warehouses["site2"]
        _, purchase_tax = taxes

        # 1. SABIC RFQ (P00001): 60 kg Red PMMA Granules + 100 kg Black ABS Pellets
        sabic = vendors.get("vendor_sabic_polymer")
        if sabic:
            self._upsert(
                "po_sabic_plastics",
                "purchase.order",
                {
                    "name": "P00001",
                    "partner_id": sabic.id,
                    "company_id": company.id,
                    "order_line": [
                        Command.create({
                            "product_id": products["prod_rm_pmma"].id,
                            "product_qty": 60.0,
                            "price_unit": 850.0,
                            "tax_ids": [Command.set([purchase_tax.id])],
                        }),
                        Command.create({
                            "product_id": products["prod_rm_abs"].id,
                            "product_qty": 100.0,
                            "price_unit": 650.0,
                            "tax_ids": [Command.set([purchase_tax.id])],
                        }),
                    ],
                },
            )

        # 2. Aisha Steel RFQ (P00002): 500 Mounting Fasteners & Seal Kits
        aisha = vendors.get("vendor_aisha_steel")
        if aisha:
            self._upsert(
                "po_aisha_fasteners",
                "purchase.order",
                {
                    "name": "P00002",
                    "partner_id": aisha.id,
                    "company_id": company.id,
                    "order_line": [
                        Command.create({
                            "product_id": products["prod_rm_fasteners"].id,
                            "product_qty": 500.0,
                            "price_unit": 70.0,
                            "tax_ids": [Command.set([purchase_tax.id])],
                        }),
                    ],
                },
            )

        # 3. Osram RFQ (P00003): 500 12V Bulbs & Socket Harnesses
        osram = vendors.get("vendor_osram_lighting")
        if osram:
            self._upsert(
                "po_osram_lighting",
                "purchase.order",
                {
                    "name": "P00003",
                    "partner_id": osram.id,
                    "company_id": company.id,
                    "order_line": [
                        Command.create({
                            "product_id": products["prod_rm_bulb_12v"].id,
                            "product_qty": 500.0,
                            "price_unit": 210.0,
                            "tax_ids": [Command.set([purchase_tax.id])],
                        }),
                    ],
                },
            )

    def _maintenance(self, company, workcenters, products):
        team = self._upsert(
            "maint_team_die",
            "maintenance.team",
            {
                "name": "Plant Reliability & Testing Calibration Cell",
                "company_id": company.id,
            },
        )
        eq = self._upsert(
            "maint_eq_asm01",
            "maintenance.equipment",
            {
                "name": "Automated 12V Photometric Testing Rig & Ultrasonic Welder",
                "workcenter_id": workcenters["wc_asm_mirror"].id,
                "maintenance_team_id": team.id,
                "company_id": company.id,
            },
        )
        stage_done = self.env["maintenance.stage"].search([("done", "=", True)], limit=1)
        if not stage_done:
            stage_done = self.env["maintenance.stage"].search([], order="sequence desc", limit=1)

        req_corr = self._upsert(
            "maint_req_tester_cal",
            "maintenance.request",
            {
                "name": "Quarterly Calibration: 12V Regulated DC Photometric Sensor Rig",
                "equipment_id": eq.id,
                "maintenance_team_id": team.id,
                "maintenance_type": "preventive",
                "priority": "2",
                "description": "<p>Calibrated 12.0V DC regulated power supply and lux light sensor probes. Verified dual-filament current sensitivity (Tail 0.42A, Brake 1.75A). Certified for OEM production.</p>",
                "stage_id": stage_done.id if stage_done else False,
                "company_id": company.id,
            },
        )
        return req_corr

    def _seed_stock_and_lots(self, company, warehouses, products):
        # Baseline stock is 0.00 so procurement and manufacturing workflows are demonstrated live
        self.env.cr.execute("DELETE FROM stock_quant WHERE company_id = %s OR company_id IS NULL", (company.id,))

    def _stage_demo_transactions(self, company, customers, products, taxes, warehouses, boms):
        sale_tax, _ = taxes
        wh = warehouses["site2"]
        honda = customers["customer_atlas_honda"]
        taillight = products["prod_taillight_cd70"]

        # Clean up any past invoices so demo can be repeated freshly
        fbr_cfg = self.env["bl.fbr.config"].search([("company_id", "=", company.id)], limit=1)
        if fbr_cfg:
            fbr_cfg.write({"lock_invoice_after_submission": False})
        for inv in self.env["account.move"].search([("company_id", "=", company.id)]):
            try:
                inv.button_draft()
                inv.unlink()
            except Exception:
                pass

        # 1. Clean Single OEM Sales Order: SO-HONDA-2026-001 (Atlas Honda Ltd) for 200 Tail Lights
        so1 = self.env["sale.order"].search([("partner_id", "=", honda.id), ("company_id", "=", company.id)], limit=1)
        if not so1:
            so1 = self._upsert(
                "so_atlas_honda_001",
                "sale.order",
                {
                    "name": "SO-HONDA-2026-001",
                    "partner_id": honda.id,
                    "company_id": company.id,
                    "warehouse_id": wh.id,
                    "client_order_ref": "AHL-OEM-PO-2026-001",
                    "order_line": [
                        Command.create({
                            "product_id": taillight.id,
                            "product_uom_qty": 200.0,
                            "price_unit": 1450.0,
                            "tax_ids": [Command.set([sale_tax.id])],
                        }),
                    ],
                },
            )
        if so1.state == "draft":
            so1.action_confirm()

        # Validate delivery WH/OUT/00001 as Done (200 Units Delivered to Atlas Honda)
        for p in so1.picking_ids:
            if p.state not in ["done", "cancel"]:
                for m in p.move_ids:
                    m.quantity = m.product_uom_qty
                    m.picked = True
                p.button_validate()

        # Create and post official customer invoice INV/2026/00001
        inv1 = self.env["account.move"].search([("partner_id", "=", honda.id), ("company_id", "=", company.id), ("move_type", "=", "out_invoice")], limit=1)
        if not inv1:
            inv1 = so1._create_invoices()
        if inv1.state == "draft":
            inv1.action_post()

        # Ensure baseline physical warehouse inventory is exactly 0.00
        self.env.cr.execute("DELETE FROM stock_quant WHERE company_id = %s OR company_id IS NULL", (company.id,))

        # Remove any legacy sub-assembly MOs so only WH/MO/00001 exists
        for old_mo in self.env["mrp.production"].search([("company_id", "=", company.id), ("name", "!=", "WH/MO/00001"), ("state", "!=", "done")]):
            try:
                old_mo.action_cancel()
                old_mo.unlink()
            except Exception:
                pass

        # 2. Stage a Clean Primary Live Manufacturing Order: WH/MO/00001 for 200 Units of Honda CD70 Tail Light
        mo = self.env["mrp.production"].search([("product_id", "=", taillight.id), ("company_id", "=", company.id)], order="id desc", limit=1)
        if not mo:
            mo = self._upsert(
                "mo_honda_taillight_001",
                "mrp.production",
                {
                    "name": "WH/MO/00001",
                    "product_id": taillight.id,
                    "product_qty": 200.0,
                    "bom_id": boms["tl_final"].id,
                    "warehouse_id": wh.id,
                    "company_id": company.id,
                    "date_start": fields.Datetime.now(),
                },
            )
            mo.action_confirm()
            try:
                mo.button_plan()
            except Exception as e:
                _logger.warning("Planning MO note: %s", e)
            now = fields.Datetime.now()
            mo.write({"date_start": now})
            for wo in mo.workorder_ids:
                wo.write({"date_start": now})

        # 3. Clean Chatter Messages: Remove OdooBot field tracking logs and post professional notes
        admin_partner = self.env.ref("base.partner_admin", raise_if_not_found=False) or self.env.user.partner_id
        for model, res_ids in [("sale.order", [so1.id]), ("mrp.production", [mo.id])]:
            self.env["mail.message"].search([("model", "=", model), ("res_id", "in", res_ids)]).unlink()

        so1.message_post(
            body=Markup("<p><strong>OEM Purchase Release Logged</strong>: Confirmed schedule for 200 units of Honda CD70 Tail Light Complete Assembly at PKR 1,450.00 / unit (+18% GST) for Atlas Honda Limited (Sheikhupura Assembly Plant).</p>"),
            subtype_xmlid="mail.mt_note",
            author_id=admin_partner.id,
        )

        mo.message_post(
            body=Markup("<p><strong>Final Assembly Order Scheduled</strong>: S.I.T.E. II Plant production active for 200 units on Assembly Bench (WC-ASM-MIRROR). In-line photometric inspection (QC-1) ready for operator.</p>"),
            subtype_xmlid="mail.mt_note",
            author_id=admin_partner.id,
        )

        return {"so1": so1, "mo": mo, "inv": False}

    def seed(self):
        company = self._company()
        accounts = self._chart_of_accounts(company)
        taxes = self._taxes(company, accounts)
        categories = self._categories(company, accounts)
        warehouses = self._warehouses(company)
        workcenters = self._workcenters(company)
        customers, vendors = self._partners(company, accounts)
        products = self._products(company, taxes, vendors, categories)
        boms = self._boms(company, products, workcenters)
        self._quality_points(company, products, warehouses, boms)
        self._reordering_rules(company, warehouses, products, vendors, taxes)
        maint_req = self._maintenance(company, workcenters, products)
        self._seed_stock_and_lots(company, warehouses, products)
        tx = self._stage_demo_transactions(company, customers, products, taxes, warehouses, boms)

        return {
            "status": "success",
            "company": company.name,
            "currency": company.currency_id.name,
            "fbr_ntn": company.vat,
            "warehouse": warehouses["site2"].name,
            "accounts_count": len(accounts),
            "categories_count": len(categories),
            "workcenters_count": len(workcenters),
            "products_count": len(products),
            "boms_count": len(boms),
            "customers_count": len(customers),
            "vendors_count": len(vendors),
            "showcase_product": products["prod_taillight_cd70"].name,
            "maintenance_request": maint_req.name,
            "sales_order_honda": tx["so1"].name if tx.get("so1") else False,
            "manufacturing_order": tx["mo"].name if tx.get("mo") else False,
        }

    def verify(self):
        company = self.env.ref("base.main_company")
        assert company.name == "GI Enterprises (Pvt) Ltd", f"Expected GI Enterprises, got {company.name}"
        assert company.vat == "0658921-4", f"Expected NTN 0658921-4, got {company.vat}"

        wh = self.env["stock.warehouse"].search([("company_id", "=", company.id), ("active", "=", True)], limit=1)
        assert wh, "Expected at least 1 active warehouse (S.I.T.E. II Plant)"

        acc_count = self.env["account.account"].search_count([("company_ids", "in", company.id)])
        assert acc_count >= 50, f"Expected at least 50 accounts in chart of accounts, found {acc_count}"

        wc_count = self.env["mrp.workcenter"].search_count([("company_id", "=", company.id)])
        assert wc_count >= 1, f"Expected at least 1 workcenter, found {wc_count}"

        bom_count = self.env["mrp.bom"].search_count([("company_id", "=", company.id)])
        assert bom_count >= 1, f"Expected at least 1 BOM, found {bom_count}"

        qp_count = self.env["quality.point"].search_count([("company_id", "=", company.id)])
        assert qp_count >= 1, f"Expected at least 1 quality point, found {qp_count}"

        mo_count = self.env["mrp.production"].search_count([("company_id", "=", company.id)])
        assert mo_count >= 1, f"Expected at least 1 manufacturing order, found {mo_count}"

        so_count = self.env["sale.order"].search_count([("company_id", "=", company.id)])
        assert so_count >= 1, f"Expected at least 1 sales order, found {so_count}"

        return {
            "status": "verified",
            "company": company.name,
            "warehouse": wh.name,
            "chart_of_accounts": acc_count,
            "workcenters": wc_count,
            "boms": bom_count,
            "quality_points": qp_count,
            "manufacturing_orders": mo_count,
            "sales_orders": so_count,
            "stock_baseline": "ZERO",
        }
