from enum import Enum, unique


@unique
class NameScheme(Enum):
    SINGLE = "SINGLE"
    INDEX = "INDEX"
    CUSTOM = "CUSTOM"
