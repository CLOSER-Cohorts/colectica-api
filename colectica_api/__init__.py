# what things to expose to users

"""
The colectica_api module exposes a ColecticaObject which
handles communication with a Colectica server (using its
REST api).
"""

__version__ = "0.0.6"

from .colectica import ColecticaObject, ColecticaBasicAPI

# what happens on `from colectica_api import *`, also controls docs
__all__ = ["ColecticaObject", "ColecticaBasicAPI"]
