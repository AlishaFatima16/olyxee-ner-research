from enum import Enum

SCHEMA_VERSION = "1.3"

class Status(str, Enum):
    SUPPORTED   = "supported"
    REVIEW      = "review"
    AMBIGUOUS   = "ambiguous"
    UNSUPPORTED = "unsupported"