from beanie import Document
from pydantic import BaseModel, Field ,ConfigDict
from datetime import date
from models.stock import ItemTypeEnum


class IndentBase(BaseModel):
    item_name: str
    Quantity: int
    Department: str
    Item_Type: str

class Indent(Document, IndentBase):
    date_of_indent: date = Field(default_factory=date.today)
    
    model_config = ConfigDict(
        name="indents",
        arbitrary_types_allowed=True
    )
    
class IndentCreate(BaseModel):
    item_name: str
    Quantity: int = Field(gt=0)
    Department: str
    
class IndentUpdate(BaseModel):
    Quantity: int
    
class IndentResponse(BaseModel):
    date_of_indent: date
    item_name: str
    Quantity: int
    Department: str
    Item_Type: ItemTypeEnum