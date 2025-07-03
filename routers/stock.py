from fastapi import APIRouter, Depends, HTTPException, status
from models.stock import Stock, Item, StockCreate, StockResponse, RequestIssueResponse, ReqIssueBase, InventoryItemTotal
from typing import List
from models.inventory import Request, ReqIssue, RequestIssueResponse2
from datetime import date
import logging
from fastapi.responses import JSONResponse
from fastapi_mail import FastMail, MessageSchema, MessageType
from utils.mail import *
from bson import ObjectId

router = APIRouter(prefix="/central_stock", tags=["Central_Stock"])

# Configure the logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

@router.post("/create_stock", response_model=StockResponse, tags=["Central_Stock"])
async def create_stock(stock: StockCreate):
    # Check if gem_id already exists
    existing = await Stock.find_one(Stock.vendor_name == stock.vendor_name)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Stock from {stock.vendor_name} already exists."
            )
    # Create a new stock entry
    stock_model = Stock(
        vendor_name=stock.vendor_name,
        date_of_order=stock.date_of_order,
        date_of_purchase=stock.date_of_purchase
    )
    await stock_model.insert()

    item_docs = []
    for item in stock.items:
        item_doc = Item(
            item_name=item.item_name,
            item_type=item.item_type,
            item_quantity=item.item_quantity,
            item_price=item.item_price,
            stock=stock_model
        )
        await item_doc.insert()
        item_docs.append(item_doc)

        # Update central inventory
        existing = await InventoryItemTotal.find_one({
            "item_name": item.item_name,
            "item_type":item.item_type
        })

        if existing:
            existing.total_quantity = existing.total_quantity + item.item_quantity
            await existing.save()
        else:
            inventory_create = InventoryItemTotal(
                item_name=item.item_name,
                item_type=item.item_type,
                total_quantity=item.item_quantity,
            )
            await inventory_create.insert()
    stock_model.items = item_docs
    await stock_model.save()
    return StockResponse(
        vendor_name=stock_model.vendor_name,
        date_of_order=stock_model.date_of_order,
        date_of_purchase=stock_model.date_of_purchase,
        date_of_adding=stock_model.date_of_adding,
        items=[{
            "item_id": str(item.id),
            "item_name": item.item_name,
            "item_type": item.item_type,
            "item_quantity": item.item_quantity,
            "item_price": item.item_price
        } for item in item_docs]
    )

@router.get("/get_stock_with_items/{gem_id}", response_model=StockResponse, tags=["Central_Stock"])
async def get_stock_with_items(stock_id: str):
    stock = await Stock.get(stock_id, fetch_links=True)
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    return StockResponse(
        vendor_name=stock.vendor_name,
        date_of_order=stock.date_of_order,
        date_of_purchase=stock.date_of_purchase,
        date_of_adding=stock.date_of_adding,
        items=[
            {
                "item_id": str(item.id),
                "item_name": item.item_name,
                "item_type": item.item_type,
                "item_quantity": item.item_quantity,
                "item_price": item.item_price
            }
            for item in stock.items or []
        ]
    )


# issue to the request
@router.post("/item_issue_to_request/{request_id}", response_model=RequestIssueResponse, tags=["Central_Stock"], response_model_exclude={"reason"})
async def issue_request(request_id: str, issue: List[ReqIssueBase]):
    try:
        if not ObjectId.is_valid(request_id):
            raise HTTPException(status_code=400, detail="Invalid request ID")
        request = await Request.get(ObjectId(request_id), fetch_links=True)
        if not request:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
        
        if request.status != "Pending":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Request has already been '{request.status.value}' and cannot be approved again.")

        issued_items = []
        for item in issue:
            inventory_item = await InventoryItemTotal.find_one({
                "item_name": item.item_name,
                "item_type": item.Item_Type
            })

            if not inventory_item:
                raise HTTPException(status_code=404, detail=f"No inventory found for item: {item.item_name}")

            if item.qty>inventory_item.total_quantity:
                raise HTTPException(detail=f"Insufficient quantity for item: {item.item_name}")
            
            inventory_item.total_quantity = inventory_item.total_quantity - item.qty

            await inventory_item.save()

            issue_doc = ReqIssue(
                item_name=item.item_name,
                qty=item.qty,
                Item_Type=item.Item_Type,
                request=request
            )
            await issue_doc.insert()
            issued_items.append(issue_doc)
        
        

        request.status = "Approved"
        request.date_of_approval = date.today()
        request.issued = issued_items
        await request.save()
    
        # Create an HTML template
        html = f"""
        <html><body>
        <h1>Request Issued</h1>
        <p><strong>ID:</strong> {request.id}</p>
        <p><strong>Campus:</strong> {request.campus_name}</p>
        <p><strong>Status:</strong> Approved</p>
        <p><strong>Date of Approval:</strong> {request.date_of_approval}</p>
        <h2>Items</h2>
        <ul>{''.join([f'<li>{i.item_name}: {i.qty} ({i.Item_Type})</li>' for i in issued_items])}</ul>
        </body></html>
        """
        
        try:
            message = MessageSchema(
                subject="Your Request has been Approved",
                recipients=[request.your_mail_id],
                body=html,
                subtype=MessageType.html
            )

            fm = FastMail(conf)
            await fm.send_message(message)
            logger.info("Email sent successfully")
        except Exception as email_error:
            logger.error(f"Failed to send email: {email_error}")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error processing request: {str(e)}")

    return RequestIssueResponse(
        request_id=str(request.id),
        campus_name=request.campus_name,
        date_of_request=request.date_of_request,
        status=request.status,
        reason=request.reason,
        items=[{"item_name": i.item_name, "qty": i.qty} for i in request.items],
        issued=[{"item_name": i.item_name, "qty": i.qty, "Item_Type": i.Item_Type} for i in issued_items]
    )

@router.post("/reject_request/{request_id}/{reason}", response_model=RequestIssueResponse, tags=["Central_Stock"],response_model_exclude={"issued"})
async def reject_request(request_id: str, reason: str):
    try:
        request = await Request.get(request_id, fetch_links=True)
        if not request:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

        request.status = "Rejected"
        request.reason = reason
        await request.save()
        
        html = f"""
        <html>
        <body>
            <h1>Request Rejected</h1>
            <p>Request ID: {request.id}</p>
            <p>Campus Name: {request.campus_name}</p>
            <p>Date of Request: {request.date_of_request}</p>
            <p>Status: {"Rejected"}</p>
            <p>Reason: {reason}</p>
        </body>
        </html>
        """

        message = MessageSchema(
            subject="Your Request has been Rejected",
            recipients=[request.your_mail_id],
            body=html,
            subtype=MessageType.html
        )

        fm = FastMail(conf)
        await fm.send_message(message)

        return RequestIssueResponse(
            request_id=str(request.id),
            campus_name=request.campus_name,
            date_of_request=request.date_of_request,
            status=request.status,
            reason=request.reason,
            items=[{"item_name": i.item_name, "qty": i.qty} for i in request.items or []],
            issued=[]
    )

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred: {str(e)}")

@router.get("/all_issued_items", response_model=List[RequestIssueResponse2], tags=["Central_Stock"])
async def get_issued_items():
    requests = await Request.find(Request.status == "Approved").to_list()
    result = []
    for req in requests:
        full_req = await Request.get(req.id, fetch_links=True)
        result.append(RequestIssueResponse2(
            request_id=str(full_req.id),
            campus_name=full_req.campus_name,
            date_of_request=full_req.date_of_request,
            date_of_approval=full_req.date_of_approval,
            issued=[{"item_name": i.item_name, "qty": i.qty, "Item_Type": i.Item_Type} for i in full_req.issued or []]
        ))
    return result



#for the total inventory items
@router.get("/all_inventory_items", response_model=List[dict])
async def get_all_inventory_items():
    items = await InventoryItemTotal.find_all().to_list()
    return [
        {
            "item_name": item.item_name,
            "item_type": item.item_type,
            "total_quantity": item.total_quantity
        }
        for item in items
    ]