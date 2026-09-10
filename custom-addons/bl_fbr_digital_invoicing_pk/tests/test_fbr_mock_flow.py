import json
from unittest.mock import patch

from odoo import Command, fields
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from ..services.fbr_api_service import FbrApiService


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload
        self.text = json.dumps(payload)

    def json(self):
        return self._payload


@tagged("post_install", "-at_install")
class TestFbrMockFlow(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.write(
            {
                "bl_fbr_ntn": "DEMO-NTN",
                "bl_fbr_strn": "DEMO-STRN",
                "bl_fbr_seller_registration_no": "DEMO-SELLER",
                "bl_fbr_seller_province": "Sindh",
            }
        )
        cls.company.partner_id.write({"street": "10 Demo Street", "city": "Karachi"})
        cls.config = cls.env["bl.fbr.config"].get_config()
        cls.config.write(
            {
                "enabled": True,
                "connection_mode": "mock_success",
                "seller_ntn": "DEMO-NTN",
                "seller_strn": "DEMO-STRN",
                "seller_registration_no": "DEMO-SELLER",
                "seller_province": "Sindh",
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Registered Buyer",
                "bl_fbr_registration_type": "registered",
                "bl_fbr_registration_no": "BUYER-REG",
                "bl_fbr_ntn": "BUYER-NTN",
                "bl_fbr_province": "Sindh",
                "street": "20 Buyer Avenue",
                "city": "Karachi",
            }
        )
        cls.tax = cls.env["account.tax"].create(
            {
                "name": "FBR Test Tax 18%",
                "amount": 18,
                "amount_type": "percent",
                "type_tax_use": "sale",
                "company_id": cls.company.id,
                "country_id": cls.company.country_id.id,
            }
        )
        template = cls.env["product.template"].create(
            {
                "name": "FBR Test Product",
                "type": "consu",
                "list_price": 100,
                "bl_fbr_hs_code": "DEMO-HS",
                "bl_fbr_uom": "Unit",
                "bl_fbr_sale_type": "Standard taxable sale",
                "bl_fbr_scenario": "SN001",
                "taxes_id": [Command.set([cls.tax.id])],
            }
        )
        cls.product = template.product_variant_id

    def _configure_live_mode(self):
        self.company.write(
            {
                "bl_fbr_ntn": "0786909",
                "bl_fbr_seller_registration_no": "0786909",
                "bl_fbr_seller_province": "Sindh",
            }
        )
        self.company.partner_id.write({"street": "10 Seller Street", "city": "Karachi"})
        self.config.write(
            {
                "enabled": True,
                "connection_mode": "sandbox",
                "seller_ntn": "0786909",
                "seller_registration_no": "0786909",
                "seller_province": "Sindh",
                "sandbox_url": "https://gw.fbr.gov.pk/di_data/v1/di/postinvoicedata_sb",
                "api_token": "demo-token",
            }
        )
        self.partner.write(
            {
                "bl_fbr_registration_type": "registered",
                "bl_fbr_registration_no": "1000000000000",
                "bl_fbr_ntn": False,
                "bl_fbr_cnic": "1000000000000",
                "bl_fbr_province": "Sindh",
                "street": "20 Buyer Avenue",
                "city": "Karachi",
            }
        )

    def _invoice(self):
        move = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "invoice_date": fields.Date.today(),
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": self.product.id,
                            "quantity": 1,
                            "price_unit": 100,
                            "tax_ids": [Command.set([self.tax.id])],
                        }
                    )
                ],
            }
        )
        move.action_post()
        return move

    def test_payload_builder_contains_core_values(self):
        invoice = self._invoice()
        payload = self.env["bl.fbr.payload.builder"].build_payload(invoice)
        self.assertEqual(payload["seller"]["ntn"], "DEMO-NTN")
        self.assertEqual(payload["buyer"]["registration_no"], "BUYER-REG")
        self.assertEqual(payload["lines"][0]["hs_code"], "DEMO-HS")

    def test_live_submission_payload_uses_direct_fbr_schema(self):
        self._configure_live_mode()
        invoice = self._invoice()
        payload = invoice._bl_fbr_payload()
        self.assertEqual(payload["invoiceType"], "Sale Invoice")
        self.assertEqual(payload["sellerNTNCNIC"], "0786909")
        self.assertEqual(payload["buyerNTNCNIC"], "1000000000000")
        self.assertEqual(payload["scenarioId"], "SN001")
        self.assertEqual(payload["items"][0]["rate"], "18%")

    def test_live_validation_rejects_non_numeric_seller_id(self):
        self._configure_live_mode()
        self.config.write({"seller_registration_no": "H424906", "seller_ntn": "H424906"})
        invoice = self._invoice()
        errors = invoice._bl_fbr_validation_errors()
        self.assertTrue(any("7-digit NTN or 13-digit CNIC" in error for error in errors))

    def test_missing_hs_code_blocks_submission(self):
        self.product.product_tmpl_id.bl_fbr_hs_code = False
        invoice = self._invoice()
        invoice.action_bl_fbr_submit()
        self.assertEqual(invoice.bl_fbr_status, "validation_error")

    def test_mock_success_and_duplicate_prevention(self):
        invoice = self._invoice()
        invoice.action_bl_fbr_submit()
        self.assertEqual(invoice.bl_fbr_status, "submitted")
        self.assertTrue(invoice.bl_fbr_invoice_number)
        self.assertTrue(invoice.bl_fbr_qr_code_image)
        with self.assertRaises(UserError):
            invoice.action_bl_fbr_submit()

    def test_mock_failure_queue_then_retry(self):
        invoice = self._invoice()
        self.config.connection_mode = "mock_failure"
        invoice.action_bl_fbr_submit()
        self.assertEqual(invoice.bl_fbr_status, "failed")
        self.assertTrue(invoice.bl_fbr_queue_ids)
        self.config.connection_mode = "mock_success"
        invoice.bl_fbr_queue_ids.action_process()
        self.assertEqual(invoice.bl_fbr_status, "submitted")
        self.assertEqual(invoice.bl_fbr_queue_ids[:1].status, "done")

    @patch("odoo.addons.bl_fbr_digital_invoicing_pk.services.fbr_api_service.requests.post")
    def test_live_submit_parses_direct_fbr_success_response(self, mock_post):
        self._configure_live_mode()
        invoice = self._invoice()
        payload = invoice._bl_fbr_payload()
        mock_post.return_value = FakeResponse(
            200,
            {
                "invoiceNumber": "7000007DI1747119701593",
                "dated": "2025-05-13 12:01:41",
                "validationResponse": {
                    "statusCode": "00",
                    "status": "Valid",
                    "error": "",
                    "invoiceStatuses": [
                        {
                            "itemSNo": "1",
                            "statusCode": "00",
                            "status": "Valid",
                            "invoiceNo": "7000007DI1747119701593-1",
                            "errorCode": "",
                            "error": "",
                        }
                    ],
                },
            },
        )
        response = FbrApiService(self.env).submit(invoice, payload, self.config)
        self.assertTrue(response["success"])
        self.assertEqual(response["fbr_invoice_number"], "7000007DI1747119701593")
        self.assertEqual(response["sent_payload"]["invoiceType"], "Sale Invoice")

    @patch("odoo.addons.bl_fbr_digital_invoicing_pk.services.fbr_api_service.requests.post")
    def test_live_validate_surfaces_fbr_error_codes(self, mock_post):
        self._configure_live_mode()
        invoice = self._invoice()
        payload = invoice._bl_fbr_payload()
        mock_post.return_value = FakeResponse(
            401,
            {
                "dateTime": "2026-07-01T09:13:47.450228533",
                "errorCode": "0401",
                "error": "Unauthorized access: Provided seller registration number is not 13 digits (CNIC) or 7 digits (NTN) or the authorized token does not exist against seller registration number",
                "status": "Unauthorized",
            },
        )
        response = FbrApiService(self.env).validate(invoice, payload, self.config)
        self.assertFalse(response["success"])
        self.assertEqual(response["error_code"], "0401")
