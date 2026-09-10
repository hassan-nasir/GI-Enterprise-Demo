# -*- coding: utf-8 -*-
from . import models

def post_init_hook(env):
    env["gi.enterprise.demo.service"].seed()

