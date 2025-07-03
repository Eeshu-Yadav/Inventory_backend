from beanie import Document, Link, PydanticObjectId
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from datetime import date
from typing import List, Optional, Annotated
import enum
from models.stock import RequestItemResponse, ItemTypeEnum

# Enums
class StatusEnum(str, enum.Enum):
    Pending = "Pending"
    Approved = "Approved"
    Rejected = "Rejected"


# ----------- Base Models -----------
class RequestBase(BaseModel):
    your_mail_id: EmailStr
    campus_name: str
    reason: Optional[str]

class Request(RequestBase, Document):
    date_of_request: date = Field(default_factory=date.today)
    status: StatusEnum = Field(default=StatusEnum.Pending)
    date_of_approval: Optional[date] = None
    items: List[Link["RequestItem"]] = Field(default_factory=list)
    issued: List[Link["ReqIssue"]] = Field(default_factory=list)

    model_config = ConfigDict(
        name="requests",
        arbitrary_types_allowed=True
    )
    
class RequestItemBase(BaseModel):
    item_name: str
    qty: int = Field(gt=0, description="Quantity must be greater than 0")
    description: Optional[str] = Field(
        default=None,
        description="Description of the item",
        max_length=100
    )

class RequestItem(RequestItemBase, Document):
    request: Optional[Link["Request"]] = None
    model_config = ConfigDict(
        name="request_items",
        arbitrary_types_allowed=True
    )


class ReqIssueBase(BaseModel):
    item_name: str
    qty: int
    Item_Type: str

class ReqIssue(ReqIssueBase, Document):
    request: Optional[Link["Request"]] = None
    model_config = ConfigDict(
        name="issued_items",
        arbitrary_types_allowed=True
    )

class RequestResponse(BaseModel):
    campus_name: str
    date_of_request: date
    status: StatusEnum
    items: List[RequestItemBase]
    
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
    items: List[RequestItemBase]
    issued: List[ReqIssueResponse]
    
class RequestIssueResponse2(BaseModel):
    campus_name: str
    date_of_request: date
    date_of_approval: date
    issued: List[ReqIssueResponse]
    
    
class RequestItemResponse(BaseModel):
    item_name: str
    qty: int = Field(gt=0)
    
# ----------- Create Schema -----------

class RequestCreate(BaseModel):
    your_mail_id: EmailStr
    campus_name: str
    reason: str
    items: List[RequestItemBase]

