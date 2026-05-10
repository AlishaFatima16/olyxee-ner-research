from enum import Enum

SCHEMA_VERSION = "1.3"

class Status(str, Enum):
    supported   = "supported"
    review      = "review"
    ambiguous   = "ambiguous"
    unsupported = "unsupported"