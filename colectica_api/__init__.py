# what things to expose to users

"""
The collectica_api module exposes a ColecticaObject which
handles communication with a Colectica server (using its
REST api).
"""

__version__ = "0.0.3.dev0"

from .colectica import ColecticaObject

# what happens on `from colectica_api import *`, also controls docs
__all__ = ["ColecticaObject"]
