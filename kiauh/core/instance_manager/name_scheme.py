from enum import unique, Enum


@unique
class NameScheme(Enum):
    SINGLE = "SINGLE"
    INDEX = "INDEX"
    CUSTOM = "CUSTOM"
