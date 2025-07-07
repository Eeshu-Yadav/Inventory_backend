from beanie import Document, Link
from pydantic import BaseModel, Field, ConfigDict, model_validator
from datetime import date
from typing import List, Optional
import enum

ALLOWED_CONSUMABLE_ITEMS = [
    "Brown Tape", "Transparent Tap Medium Size", "Clip Binder small", "Clip M Size (Boxes)", 
    "Diary Register", "Fevicol (Gum) 100 Gram Bottle", "File Board", 
    "File Cover with DSEU print", "File Tag Small (Bunch)", "Multi Color Flag/ Post it (pkt)",
    "Nothing Sheet Legal- Ream","Paper Ream (A4 Size)","Pen Uniball Black" , "Punching Machine Double", "Stapler Heavy Duty",
    "Stapler Small" , "Tissue Box","Extension Cord (Multiple Switches)"
]

# Enums
class ItemTypeEnum(str, enum.Enum):
    CONSUMABLE = "Consumable"
    NON_CONSUMABLE = "Non Consumable"

class StatusEnum(str, enum.Enum):
    Pending = "Pending"
    Approved = "Approved"
    Rejected = "Rejected"


class StockBase(BaseModel):
    vendor_name: str
    date_of_order: date
    date_of_purchase: date

class Stock(StockBase, Document):
    date_of_adding: date = Field(default_factory=date.today)
    items: Optional[List[Link["Item"]]] = Field(default_factory=list)

    model_config = ConfigDict(
        name="stocks",
        arbitrary_types_allowed=True
    )

class ItemBase(BaseModel):
    item_name: str
    item_type: str
    item_quantity: int
    item_price: float

class Item(ItemBase, Document):
    stock: Optional[Link["Stock"]] = None

    model_config = ConfigDict(
        name="items",
        arbitrary_types_allowed=True
    )

    
class ItemCreate(BaseModel):
    item_name: str
    item_type: ItemTypeEnum
    item_quantity: int = Field(gt=0)
    item_price: float = Field(gt=0)
    @model_validator(mode="before")
    @classmethod
    def validate_non_consumable_item(cls, data):
        item_type = data.get("item_type")
        item_name = data.get("item_name")
        if item_type == ItemTypeEnum.CONSUMABLE:
            if item_name not in ALLOWED_CONSUMABLE_ITEMS:
                raise ValueError(
                    f"Invalid item for Non Consumable: '{item_name}'. Must be one of: {', '.join(ALLOWED_CONSUMABLE_ITEMS)}"
                )
        return data

class StockCreate(StockBase):
    items: List[ItemCreate]
    
class ItemResponse(BaseModel):
    item_id: str
    item_name: str
    item_type: ItemTypeEnum
    item_quantity: int
    item_price: float
    
class StockResponse(StockBase):
    date_of_adding: date
    items: List[ItemResponse]

# Request Models    
class RequestItemResponse(BaseModel):
    item_name: str
    qty: int
    
class RequestResponse(BaseModel):
    campus_name: str
    date_of_request: date
    status: StatusEnum
    items: List[RequestItemResponse]
    
class ReqIssueResponse(BaseModel):
    item_name: str
    qty: int
    Item_Type: ItemTypeEnum
    
class RequestIssueResponse(BaseModel):
    request_id: str
    campus_name: str
    date_of_request: date
    status: StatusEnum
    reason: Optional[str]
    items: List[RequestItemResponse]
    issued: List[ReqIssueResponse]
    
class ReqIssueBase(BaseModel):
    item_name: str
    qty: int = Field(gt=0)
    Item_Type: ItemTypeEnum
    
class CountsResponse(BaseModel):
    Approved: int
    Rejected: int
    Pending: int

class InventoryItemTotal(Document):
    item_name: str
    total_quantity: int = 0
    item_type: ItemTypeEnum
