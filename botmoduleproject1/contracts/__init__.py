"""Versioned integration language.

Import ``botmoduleproject1.contracts.v1`` for the current schema set.
PM3-Strategy Engine and PM3 forecasting remain separate modules.
"""

from botmoduleproject1.contracts.v1 import SCHEMA_VERSION

__all__ = ["SCHEMA_VERSION"]
