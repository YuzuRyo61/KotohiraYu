#!/usr/bin/env python3
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from Yu.webapi import app

if __name__ == "__main__":
    print(app.url_map)
    app.run(debug=True, port=8787)
