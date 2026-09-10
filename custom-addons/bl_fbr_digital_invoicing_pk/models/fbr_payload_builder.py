from odoo import _, models


class BlFbrPayloadBuilder(models.AbstractModel):
    _name = "bl.fbr.payload.builder"
    _description = "FBR Payload Builder"

    def _config_for_move(self, move):
        return self.env["bl.fbr.config"].with_company(move.company_id).get_config()

    def _invoice_lines(self, move):
        return move.invoice_line_ids.filtered(lambda line: line.display_type in (False, "product") and line.product_id)

    def _get_invoice_type(self, move):
        return {
            "out_invoice": "sale_invoice",
            "out_refund": "credit_note",
        }.get(move.move_type, "unsupported")

    def _format_address(self, partner):
        parts = [partner.street, partner.street2, partner.city, partner.state_id.name]
        address = ", ".join(part.strip() for part in parts if part)
        if not address:
            address = (partner.contact_address or "").replace("\n", ", ").strip(" ,")
        return address

    def _digits_only(self, value):
        return "".join(char for char in (value or "") if char.isdigit())

    def _first_direct_identifier(self, *values):
        for value in values:
            digits = self._digits_only(value)
            if digits:
                return digits
        return False

    def _live_invoice_type(self, move):
        return {
            "out_invoice": "Sale Invoice",
            # PRAL v1.12 sales error codes still reference credit notes even though
            # the sample field description only lists Debit Note for adjustments.
            "out_refund": "Credit Note",
        }.get(move.move_type, "Unsupported")

    def _live_buyer_registration_type(self, buyer):
        return "Registered" if buyer.get("registration_type") == "registered" else "Unregistered"

    def _live_rate(self, tax_rate):
        return f"{tax_rate:g}%"

    def _live_invoice_ref_no(self, move):
        if move.move_type != "out_refund":
            return ""
        return move.reversed_entry_id.bl_fbr_invoice_number or ""

    def _get_seller_data(self, move):
        config = self._config_for_move(move)
        company = move.company_id
        return {
            "business_name": config.seller_business_name_override or company.bl_fbr_business_name_override or company.name,
            "registration_no": config.seller_registration_no or company.bl_fbr_seller_registration_no,
            "ntn": config.seller_ntn or company.bl_fbr_ntn or company.vat,
            "strn": config.seller_strn or company.bl_fbr_strn or company.company_registry,
            "province": config.seller_province or company.bl_fbr_seller_province,
            "address": self._format_address(company.partner_id),
        }

    def _get_buyer_data(self, move):
        partner = move.partner_id.commercial_partner_id
        return {
            "name": partner.name,
            "registration_type": partner.bl_fbr_registration_type,
            "registration_no": partner.bl_fbr_registration_no,
            "buyer_type": partner.bl_fbr_buyer_type,
            "ntn": partner.bl_fbr_ntn or partner.vat,
            "cnic": partner.bl_fbr_cnic,
            "strn": partner.bl_fbr_strn or partner.company_registry,
            "province": partner.bl_fbr_province,
            "exempt": partner.bl_fbr_exempt_from_validation,
            "address": self._format_address(partner),
        }

    def _get_line_tax_data(self, line):
        tax_rate = 0.0
        tax_amount = line.price_total - line.price_subtotal
        taxes = line.tax_ids.filtered(lambda tax: tax.amount_type == "percent")
        if taxes:
            tax_rate = sum(taxes.mapped("amount"))
        return {
            "tax_rate": tax_rate,
            "value_excluding_tax": line.price_subtotal,
            "sales_tax_amount": tax_amount,
            "total_amount": line.price_total,
            "discount": line.discount,
        }

    def _get_invoice_lines(self, move):
        lines = []
        for line in self._invoice_lines(move):
            template = line.product_id.product_tmpl_id
            scenario = template.bl_fbr_scenario_id or move.company_id.bl_fbr_default_scenario_id
            lines.append(
                {
                    "product_name": line.product_id.display_name,
                    "item_code": template.bl_fbr_item_code or line.product_id.default_code,
                    "hs_code": template.bl_fbr_hs_code,
                    "fbr_uom": template.bl_fbr_uom,
                    "quantity": line.quantity,
                    "price_unit": line.price_unit,
                    "sale_type": template.bl_fbr_sale_type or scenario.default_sale_type or move.company_id.bl_fbr_default_sale_type,
                    "scenario_code": scenario.code if scenario else template.bl_fbr_scenario,
                    **self._get_line_tax_data(line),
                }
            )
        return lines

    def _validate_seller_data(self, move, issues):
        seller = self._get_seller_data(move)
        if not seller["registration_no"] and not seller["ntn"]:
            issues.append(_("Company seller registration number or NTN is missing."))
        if not seller["province"]:
            issues.append(_("Company seller province is missing."))

    def _validate_buyer_data(self, move, issues):
        partner = move.partner_id.commercial_partner_id
        if partner.bl_fbr_exempt_from_validation:
            return
        buyer = self._get_buyer_data(move)
        if not buyer["name"]:
            issues.append(_("Buyer name is missing."))
        if not buyer["registration_type"]:
            issues.append(_("Buyer registration type is missing for %s.") % partner.display_name)
        if buyer["registration_type"] == "registered":
            if not any([buyer["registration_no"], buyer["ntn"], buyer["cnic"]]):
                issues.append(_("Buyer registration number / NTN / CNIC is missing for registered buyer %s.") % partner.display_name)
        if not buyer["province"]:
            issues.append(_("Buyer province is missing for %s.") % partner.display_name)

    def _validate_live_identifier(self, value, label, issues):
        digits = self._digits_only(value)
        if len(digits) not in (7, 13):
            issues.append(_("%s must be a 7-digit NTN or 13-digit CNIC for direct FBR API mode.") % label)

    def _validate_live_payload(self, move, issues):
        payload = self.build_live_payload(move)
        partner = move.partner_id.commercial_partner_id
        self._validate_live_identifier(payload.get("sellerNTNCNIC"), _("Seller NTN/CNIC"), issues)
        if not payload.get("sellerAddress"):
            issues.append(_("Company seller address is required for direct FBR API mode."))
        if not payload.get("buyerAddress"):
            issues.append(_("Buyer address is required for %s in direct FBR API mode.") % partner.display_name)
        if payload.get("buyerRegistrationType") == "Registered":
            self._validate_live_identifier(payload.get("buyerNTNCNIC"), _("Buyer NTN/CNIC"), issues)
        else:
            buyer_id = payload.get("buyerNTNCNIC")
            if buyer_id and len(self._digits_only(buyer_id)) not in (7, 13):
                issues.append(
                    _("Buyer NTN/CNIC, when provided, must be a 7-digit NTN or 13-digit CNIC for %s.")
                    % partner.display_name
                )
        if move.move_type == "out_refund" and not payload.get("invoiceRefNo"):
            issues.append(_("Reference FBR invoice number is required for credit notes in direct FBR API mode."))
        if self._config_for_move(move).connection_mode == "sandbox" and not payload.get("scenarioId"):
            issues.append(_("Scenario ID is required for sandbox mode. Configure it on the product or company defaults."))

    def _validate_product_data(self, move, issues):
        for line in self._invoice_lines(move):
            template = line.product_id.product_tmpl_id
            if template.bl_fbr_exempt_from_validation:
                continue
            label = line.product_id.display_name
            if not template.bl_fbr_hs_code:
                issues.append(_("Product %s is missing HS Code.") % label)
            if not template.bl_fbr_uom:
                issues.append(_("Product %s is missing FBR UOM.") % label)
            if not (template.bl_fbr_sale_type or template.bl_fbr_scenario_id or move.company_id.bl_fbr_default_sale_type):
                issues.append(_("Product %s is missing FBR sale type.") % label)

    def _validate_invoice_lines(self, move, issues):
        if not self._invoice_lines(move):
            issues.append(_("Invoice has no invoice lines."))

    def validate_payload(self, move):
        config = self._config_for_move(move)
        issues = []
        if move.move_type not in ("out_invoice", "out_refund"):
            issues.append(_("Only customer invoices and credit notes can be submitted to FBR."))
        if move.state != "posted":
            issues.append(_("Invoice must be posted before FBR submission."))
        if move.bl_fbr_invoice_number and move.bl_fbr_status == "submitted":
            issues.append(_("Invoice is already submitted to FBR."))
        if not config.enabled:
            issues.append(_("FBR integration is not enabled."))
        if config.connection_mode in ("sandbox", "production"):
            base_url = config.sandbox_url if config.connection_mode == "sandbox" else config.production_url
            if not config.api_token:
                issues.append(_("API token is missing for sandbox/production mode."))
            if not base_url:
                issues.append(_("Base URL is missing for sandbox/production mode."))
        self._validate_seller_data(move, issues)
        self._validate_buyer_data(move, issues)
        self._validate_invoice_lines(move, issues)
        self._validate_product_data(move, issues)
        if config.connection_mode in ("sandbox", "production"):
            self._validate_live_payload(move, issues)
        return issues

    def build_payload(self, move):
        return {
            "invoice_type": self._get_invoice_type(move),
            "invoice_date": move.invoice_date,
            "seller": self._get_seller_data(move),
            "buyer": self._get_buyer_data(move),
            "invoice": {
                "odoo_id": move.id,
                "odoo_number": move.name,
                "origin": move.invoice_origin,
                "currency": move.currency_id.name,
                "amount_untaxed": move.amount_untaxed,
                "amount_tax": move.amount_tax,
                "amount_total": move.amount_total,
                "is_refund": move.move_type == "out_refund",
            },
            "lines": self._get_invoice_lines(move),
        }

    def build_live_payload(self, move):
        payload = self.build_payload(move)
        lines = payload["lines"]
        live_payload = {
            "invoiceType": self._live_invoice_type(move),
            "invoiceDate": str(move.invoice_date),
            "sellerNTNCNIC": self._first_direct_identifier(payload["seller"].get("registration_no"), payload["seller"].get("ntn")),
            "sellerBusinessName": payload["seller"].get("business_name"),
            "sellerProvince": payload["seller"].get("province"),
            "sellerAddress": payload["seller"].get("address"),
            "buyerNTNCNIC": self._first_direct_identifier(
                payload["buyer"].get("registration_no"),
                payload["buyer"].get("ntn"),
                payload["buyer"].get("cnic"),
            ),
            "buyerBusinessName": payload["buyer"].get("name"),
            "buyerProvince": payload["buyer"].get("province"),
            "buyerAddress": payload["buyer"].get("address"),
            "buyerRegistrationType": self._live_buyer_registration_type(payload["buyer"]),
            "invoiceRefNo": self._live_invoice_ref_no(move),
            "items": [
                {
                    "hsCode": line.get("hs_code"),
                    "productDescription": line.get("product_name"),
                    "rate": self._live_rate(line.get("tax_rate") or 0.0),
                    "uoM": line.get("fbr_uom"),
                    "quantity": line.get("quantity"),
                    "totalValues": line.get("total_amount"),
                    "valueSalesExcludingST": line.get("value_excluding_tax"),
                    "fixedNotifiedValueOrRetailPrice": 0.0,
                    "salesTaxApplicable": line.get("sales_tax_amount"),
                    "salesTaxWithheldAtSource": 0.0,
                    "extraTax": 0.0,
                    "furtherTax": 0.0,
                    "sroScheduleNo": "",
                    "fedPayable": 0.0,
                    "discount": line.get("discount"),
                    "saleType": line.get("sale_type"),
                    "sroItemSerialNo": "",
                }
                for line in lines
            ],
        }
        if self._config_for_move(move).connection_mode == "sandbox":
            live_payload["scenarioId"] = next((line.get("scenario_code") for line in lines if line.get("scenario_code")), "")
        return live_payload

    def build_submission_payload(self, move):
        config = self._config_for_move(move)
        if config.connection_mode in ("sandbox", "production"):
            return self.build_live_payload(move)
        return self.build_payload(move)
