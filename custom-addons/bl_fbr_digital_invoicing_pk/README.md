# Bashalog Pakistan FBR Digital Invoicing Connector

Odoo 19 module for Pakistan FBR Digital Invoicing readiness validation, mock submission, sandbox/production service structure, retry queue, logs, and invoice report details.

## Features

- Customer invoice and credit note readiness checks.
- Mock Success and Mock Failure modes with no internet or real credentials.
- Sandbox/Production service structure with token and base URL configuration.
- Product, partner, company, and invoice FBR fields.
- Payload builder isolated from invoice model logic.
- API service isolated from payload generation.
- Submission logs and retry queue.
- QR data and QR image generation for submitted invoices.
- Invoice report FBR compliance block.
- Manager/User security groups.

## Installation

Copy `bl_fbr_digital_invoicing_pk` into an Odoo addons path, update the Apps list, then install the module.

Docker example from this repo:

```bash
docker compose exec -T odoo python3 /opt/odoo/odoo/odoo-bin module install \
  -c /etc/odoo/odoo.conf \
  -d primemart_fmcg_poc \
  bl_fbr_digital_invoicing_pk
```

Upgrade:

```bash
docker compose exec -T odoo python3 /opt/odoo/odoo/odoo-bin module upgrade \
  -c /etc/odoo/odoo.conf \
  -d primemart_fmcg_poc \
  bl_fbr_digital_invoicing_pk
```

## Configuration

Open **FBR Digital Invoicing > Configuration** or **Accounting Settings > Pakistan FBR Digital Invoicing**.

Set:

- Enable FBR Integration
- Connection Mode: Mock Success, Mock Failure, Sandbox, or Production
- Seller registration, NTN, STRN, and province
- Sandbox/Production URL and API token when real credentials are available
- Retry and locking behavior

API tokens are stored on the company and shown as password fields in the UI.

## Mock Testing

Use `mock_success` to submit invoices without real credentials. The module generates a fake FBR invoice number and QR payload.

Use `mock_failure` to demonstrate failures, logs, and queue/retry behavior.

## Sandbox/Production

Sandbox and production modes use the configured base URL and API token. External errors are normalized into controlled failures and stored in FBR logs. The exact endpoint path may need adjustment once the official FBR/PRAL API specification for the taxpayer/integrator is confirmed.

## Tests

Typical Odoo test command:

```bash
./odoo-bin \
  -d fbr_test_19 \
  --addons-path=addons,custom-addons \
  --test-enable \
  --stop-after-init \
  -i bl_fbr_digital_invoicing_pk
```

## Packaging

```bash
zip -r bl_fbr_digital_invoicing_pk.zip bl_fbr_digital_invoicing_pk \
  -x "*/__pycache__/*" \
  -x "*.pyc" \
  -x "*/.git/*" \
  -x "*/.DS_Store"
```

## Known Limitations

- Real FBR sandbox/production mapping must be verified against the taxpayer or integrator’s current API documentation.
- Mock mode is for demonstrations and internal validation only.
- POS is intentionally out of scope for V1.

## Legal Disclaimer

This module is a technical Odoo connector and implementation aid. It does not by itself make a business legally compliant. Businesses should confirm FBR Digital Invoicing obligations, registration status, sandbox access, production rollout, and licensed integrator requirements with FBR, PRAL, their accountant, tax advisor, or licensed integrator.
