# -*- coding: utf-8 -*-
from odoo import fields, models


class MaintenanceEquipment(models.Model):
    _inherit = "maintenance.equipment"

    image_1920 = fields.Image("Equipment Image", max_width=1920, max_height=1920)
    image_128 = fields.Image("Small Image", related="image_1920", max_width=128, max_height=128, store=True)
