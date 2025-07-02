from fastapi import APIRouter, HTTPException, status
from models.indent import Indent, IndentCreate, IndentResponse
from fastapi.responses import StreamingResponse
import barcode
from barcode.writer import ImageWriter
from io import BytesIO
import logging

router = APIRouter()

## indent issue route

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.post("/create_indent_for_Non_Consumable", tags=["Indent"])
async def create_indent_non_consumable(indent: IndentCreate):
    try:
        indent_model = Indent(
            item_name=indent.item_name,
            Quantity=indent.Quantity,
            Department=indent.Department,
            Item_Type="Non Consumable"
        )
        await indent_model.insert()
        

        # Generate Barcode
        barcode_data = (
            f"Indent ID: {str(indent_model.id)}, "
            f"Date of Indent: {indent_model.date_of_indent}, "
            f"Item Name: {indent_model.item_name}, "
            f"Quantity: {indent_model.Quantity}, "
            f"Department: {indent_model.Department}, "
            f"Item Type: {indent_model.Item_Type}"
        )
        barcode_class = barcode.get_barcode_class('code128')
        barcode_instance = barcode_class(barcode_data, writer=ImageWriter())

        # Save the barcode image to a BytesIO object
        img_io = BytesIO()
        barcode_instance.write(img_io)
        img_io.seek(0)

        return StreamingResponse(img_io, media_type="image/png")
    
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate barcode"
        )

# indent issue for consumable items
@router.post("/create_indent_for_Consumable",response_model=IndentResponse, tags=["Indent"])
async def create_indent_consumable(indent: IndentCreate):
    """
    Create a Consumable indent and return its data.
    """
    try:
        indent_model = Indent(
            item_name=indent.item_name,
            Quantity=indent.Quantity,
            Department=indent.Department,
            Item_Type="Consumable"
        )
        await indent_model.insert()
        return indent_model
    except Exception as e:
        logger.error(f"Error while creating consumable indent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create indent"
        )

## get indent detail by indent id

@router.get("/get_indent/{indent_id}", response_model=IndentResponse, tags=["Indent"])
async def get_indent(indent_id: str):
    indent = await Indent.get(indent_id)
    if not indent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Indent not found")
    return indent