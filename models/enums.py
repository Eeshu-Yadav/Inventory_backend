from enum import Enum

class StatusEnum(str, Enum):
    Pending = "Pending"
    SemiApproved = "Semi Approved"
    MediatorApproved = "Mediator Approved"
    Approved = "Approved"
    Rejected = "Rejected"

class ItemTypeEnum(str, Enum):
    CONSUMABLE = "Consumable"
    NON_CONSUMABLE = "Non Consumable"

class StatusEnum(str, Enum):
    Pending = "Pending"
    Approved = "Approved"
    Rejected = "Rejected"

