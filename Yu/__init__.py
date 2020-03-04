"""
Kotohira Yu
License: MIT License (See LICENSE)
"""

import os
import gettext

from Yu import YuChan
from Yu import Util
from Yu.Timelines import local, home
from Yu.Web import WEBRUN
from .config import config
from . import log

def i18n_Setup():
    __I18NLOCALEDIR = os.path.abspath(
        os.path.join(
            'locale'
        )
    )

    TRANSLATER = gettext.translation(
        'messages',
        localedir=__I18NLOCALEDIR,
        languages=[config["i18n"]["lang"]],
        fallback=True
    )

    TRANSLATER.install()

i18n_Setup()
__all__ = ['YuChan', 'Util', 'local', 'home', 'WEBRUN', 'log']
