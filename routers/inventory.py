from fastapi import APIRouter, HTTPException, status
from models.inventory import Request, RequestItem, ReqIssue, RequestCreate, RequestResponse, RequestIssueResponse
from fastapi.responses import JSONResponse
from fastapi_mail import FastMail, MessageSchema, MessageType
from typing import List
from utils.mail import conf
import logging

router = APIRouter(prefix="/inventory", tags=["Clg_Stock"])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Request with Items and send confirmation email
@router.post("/create_request", response_model=RequestResponse, tags=["Clg_Stock"], description="Warning: If your mail_id is wrong then also your request has been submitted, please don't request again")
async def create_request(request: RequestCreate):
    try:
        request_model = Request(
            your_mail_id=request.your_mail_id,
            campus_name=request.campus_name,
            reason=request.reason
        )
        await request_model.insert()

        item_models = []
        for item in request.items:
            item_model = RequestItem(
                item_name=item.item_name,
                qty=item.qty,
                description=item.description,
                request=request_model
            )
            await item_model.insert()
            
            item_models.append(item_model)
        
        # Update request with links to items
        request_model.items = item_models
        await request_model.save()

        # Email HTML template  
        html = f"""
        <html>
        <body>
            <h1>Request Created</h1>
            <p><strong>Your Request ID:</strong> {request_model.id}</p>
            <p><strong>Campus Name:</strong> {request_model.campus_name}</p>
            <p><strong>Status:</strong> Pending</p>
            <h2>Items</h2>
            <ul>
                {"".join([f"<li>{item.item_name}: {item.qty}</li>" for item in item_models])}
            </ul>
        </body>
        </html>
        """
        
        message = MessageSchema(
            subject="Your request has been created",
            recipients=[request.your_mail_id],
            body=html,
            subtype=MessageType.html)

        fm = FastMail(conf)
        await fm.send_message(message)
        logger.info("Email sent successfully")
        
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return JSONResponse(status_code=500, content={"message": "Failed to create request and send email"})

    return RequestResponse(
        id=request_model.id,
        campus_name=request_model.campus_name,
        date_of_request=request_model.date_of_request,
        status=request_model.status,
        items=[{
            "item_name": item.item_name,
            "qty": item.qty,
            "description" : item.description
        } for item in item_models]
    )


# Fetch Request with Items status

@router.get("/get_request_with_items_status/{request_id}/{campus_name}", response_model=RequestIssueResponse, tags=["Clg_Stock"])
async def get_request_with_items(request_id: str, campus_name: str):
    print(request_id)
    print(campus_name)
    request = await Request.get(request_id, fetch_links=True)
    if not request or request.campus_name != campus_name:
        raise HTTPException(status_code=404, detail="Request not found")
    return RequestIssueResponse(
        request_id=str(request.id),
        campus_name=request.campus_name,
        date_of_request=request.date_of_request,
        status=request.status,
        reason=request.reason,
        items=[{"item_name": item.item_name, "qty": item.qty} for item in request.items or []],
        issued=[{"item_name": issue.item_name, "qty": issue.qty, "Item_Type": issue.Item_Type}
                for issue in request.issued or []]
    )

@router.get("/get_history/{campus_name}", response_model=List[RequestIssueResponse])
async def get_history(campus_name: str):
    try:        
        requests = await Request.find(Request.campus_name == campus_name).to_list()
        result = []

        for req in requests:
            req_with_links = await Request.get(req.id, fetch_links=True)
            result.append(RequestIssueResponse(
                request_id=str(req_with_links.id),
                campus_name=req_with_links.campus_name,
                date_of_request=req_with_links.date_of_request,
                status=req_with_links.status,
                reason=req_with_links.reason,
                items=[{"item_name": item.item_name, "qty": item.qty} for item in req_with_links.items or []],
                issued=[{"item_name": issue.item_name, "qty": issue.qty, "Item_Type": issue.Item_Type}
                        for issue in req_with_links.issued or []]
            ))

        return result
    except Exception as e:
        logger.error(f"Failed to get history: {e}")
        return JSONResponse(status_code=500, content={"message": "Failed to get history"})

        
    
