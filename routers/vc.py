from fastapi import APIRouter, Depends, HTTPException, status
from models.inventory import RequestIssueResponse, Request
from models.stock import CountsResponse
from typing import List

router = APIRouter(prefix="/vc", tags=["VC"])


def build_request_response(request: Request) -> RequestIssueResponse:
    return RequestIssueResponse(
        request_id=str(request.id),
        campus_name=request.campus_name,
        date_of_request=request.date_of_request,
        status=request.status,
        reason=request.reason,
        items=[{"item_name": item.item_name, "qty": item.qty} for item in request.items or []],
        issued=[
            {"item_name": issue.item_name, "qty": issue.qty, "Item_Type": issue.Item_Type}
            for issue in request.issued or []
        ]
    )

@router.get("/all_requests", response_model=List[RequestIssueResponse])
async def get_all_requests():
    requests = await Request.find_all(fetch_links=True).sort("date_of_request").to_list()
    if not requests:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No requests found")
    return [build_request_response(r) for r in requests]


@router.get("/all_approved", response_model=List[RequestIssueResponse])
async def get_all_approved():
    requests = await Request.find(Request.status == "Approved", fetch_links=True).to_list()
    if not requests:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No approved requests found")
    return [build_request_response(r) for r in requests]

@router.get("/all_rejected", response_model=List[RequestIssueResponse])
async def get_all_rejected():
    requests = await Request.find(Request.status == "Rejected", fetch_links=True).to_list()
    if not requests:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No rejected requests found")
    return [build_request_response(r) for r in requests]

@router.get("/all_pending", response_model=List[RequestIssueResponse])
async def get_all_pending():
    requests = await Request.find(Request.status == "Pending", fetch_links=True).to_list()
    if not requests:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No pending requests found")
    return [build_request_response(r) for r in requests]

@router.get("/counts", response_model=CountsResponse)
async def get_counts():
    approved_count = await Request.find(Request.status == "Approved").count()
    rejected_count = await Request.find(Request.status == "Rejected").count()
    pending_count = await Request.find(Request.status == "Pending").count()

    return CountsResponse(
        Approved=approved_count,
        Rejected=rejected_count,
        Pending=pending_count
    )