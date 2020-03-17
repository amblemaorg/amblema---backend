#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from app import create_app

config_instance = os.getenv('INSTANCE')
app = create_app(config_instance)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
