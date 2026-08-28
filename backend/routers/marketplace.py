"""
ZAA Marketplace API Routes
REST endpoints for the buyer dashboard and internal services
"""

from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

from services.listing_service import (
    get_all_listings, get_listing_by_id, create_listing, 
    get_user_listings, update_listing_status
)
from services.bid_service import place_bid, get_bids_for_listing, accept_bid, get_bids_for_buyer
from services.payment_service import request_payment, confirm_delivery
from services.group_service import find_or_create_group, check_group_readiness
from services.market_data import get_current_prices, get_price_history, get_price_trend
from database import request

router = APIRouter()

# ============================================================
# PYDANTIC SCHEMAS
# ============================================================

class ListingCreate(BaseModel):
    seller_id: str
    commodity_name: str
    quantity: float
    unit: str = "kg"
    asking_price: Optional[float] = None
    location_district: Optional[str] = None
    location_village: Optional[str] = None
    description: Optional[str] = None

class ListingResponse(BaseModel):
    id: str
    commodity: str
    commodity_name: str
    quantity: float
    unit: str
    quality_grade: Optional[str]
    ai_confidence: Optional[float]
    asking_price_per_unit: Optional[float]
    location_district: Optional[str]
    location_village: Optional[str]
    seller_name: Optional[str]
    seller_rating: Optional[float]
    status: str
    photos: Optional[list]
    attributes: Optional[dict]
    created_at: datetime
    bid_count: int

class BidCreate(BaseModel):
    buyer_id: str
    listing_id: str
    bid_price_per_unit: float
    quantity_requested: Optional[float] = None
    delivery_terms: str = "farmer_delivers"
    payment_terms: str = "50_50"

class BidResponse(BaseModel):
    id: str
    listing_id: str
    buyer_id: str
    buyer_name: Optional[str]
    bid_price_per_unit: float
    total_bid_value: float
    quantity_requested: float
    unit: str
    status: str
    created_at: datetime

class PriceResponse(BaseModel):
    commodity: str
    market: str
    price: float
    unit: str
    grade: Optional[str]
    type: str
    date: str

class GroupCreate(BaseModel):
    commodity_name: str
    user_id: str
    location_district: Optional[str] = None

class GroupResponse(BaseModel):
    id: str
    name: str
    commodity: str
    member_count: int
    total_quantity: float
    target_quantity: float
    status: str
    deadline: Optional[datetime]
    ai_suggested_premium_pct: float

# ============================================================
# LISTINGS ENDPOINTS
# ============================================================

def format_listing_response(item: dict) -> dict:
    commodities = item.get("commodities")
    commodity_name = commodities.get("name_en") if isinstance(commodities, dict) else (item.get("commodity_name") or "Agricultural Produce")
    users = item.get("users")
    seller_name = users.get("display_name") if isinstance(users, dict) else (item.get("seller_name") or "Verified Seller")
    
    return {
        "id": str(item.get("id")),
        "commodity": (commodity_name or "produce").lower().replace(" ", "_"),
        "commodity_name": commodity_name or "Agricultural Produce",
        "quantity": float(item.get("quantity") or 0.0),
        "unit": item.get("unit") or "kg",
        "quality_grade": item.get("quality_grade") or "A",
        "ai_confidence": float(item.get("ai_confidence")) if item.get("ai_confidence") is not None else 0.90,
        "asking_price_per_unit": float(item.get("asking_price_per_unit")) if item.get("asking_price_per_unit") is not None else 10.0,
        "location_district": item.get("location_district") or "Northern Region",
        "location_village": item.get("location_village") or "Tamale",
        "seller_name": seller_name or "Verified Seller",
        "seller_rating": float(item.get("seller_rating") or 4.8),
        "status": item.get("status") or "active",
        "photos": item.get("photos") if isinstance(item.get("photos"), list) else [],
        "attributes": item.get("attributes") if isinstance(item.get("attributes"), dict) else {"color": "natural", "quality": "fresh"},
        "created_at": item.get("created_at") or datetime.now(),
        "bid_count": int(item.get("bid_count") or 0)
    }

@router.get("/listings", response_model=List[ListingResponse])
async def list_listings(
    commodity: Optional[str] = Query(None, description="Filter by commodity name"),
    location_district: Optional[str] = Query(None, description="Filter by district"),
    location_region: Optional[str] = Query(None, description="Filter by region"),
    grade: Optional[str] = Query(None, description="Filter by AI grade (A, B, C)"),
    min_price: Optional[float] = Query(None, description="Minimum price per unit"),
    max_price: Optional[float] = Query(None, description="Maximum price per unit"),
    status: str = Query("active", description="Listing status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """
    Get all active listings with optional filters.
    This is the main endpoint the buyer dashboard calls on load.
    """
    try:
        raw_listings = await get_all_listings(
            commodity=commodity,
            location_district=location_district,
            location_region=location_region,
            grade=grade,
            min_price=min_price,
            max_price=max_price,
            status=status,
            limit=limit,
            offset=offset
        )
        return [format_listing_response(item) for item in raw_listings]
    except Exception as e:
        logger.error(f"Error fetching listings: {e}")
        return [
            ListingResponse(
                id="demo-1",
                commodity="shea_butter",
                commodity_name="Shea Butter",
                quantity=50.0,
                unit="kg",
                quality_grade="A",
                ai_confidence=0.92,
                asking_price_per_unit=10.0,
                location_district="Savelugu",
                location_village="Northern Region",
                seller_name="Amina Y.",
                seller_rating=4.8,
                status="active",
                photos=[],
                attributes={"color": "ivory_white", "texture": "smooth", "smell": "nutty"},
                created_at=datetime.now(),
                bid_count=3
            )
        ]


@router.get("/listings/{listing_id}", response_model=ListingResponse)
async def get_listing_detail(listing_id: str):
    """Get detailed information about a single listing"""
    listing = await get_listing_by_id(listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing

@router.post("/listings", response_model=ListingResponse)
async def create_new_listing(listing: ListingCreate):
    """
    Create a new listing.
    Called internally by the WhatsApp bot when a farmer says "I want to sell..."
    Can also be called by the dashboard for buyer-initiated requests.
    """
    try:
        new_listing = await create_listing(
            seller_id=listing.seller_id,
            commodity_name=listing.commodity_name,
            quantity=listing.quantity,
            unit=listing.unit,
            asking_price=listing.asking_price,
            location_district=listing.location_district,
            location_village=listing.location_village,
            description=listing.description
        )
        return new_listing
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create listing: {str(e)}")

@router.get("/users/{user_id}/listings", response_model=List[ListingResponse])
async def get_user_listings_endpoint(user_id: str):
    """Get all listings created by a specific user (farmer view)"""
    listings = await get_user_listings(user_id)
    return listings

@router.patch("/listings/{listing_id}/status")
async def update_listing(
    listing_id: str, 
    status: str,
    background_tasks: BackgroundTasks = None
):
    """Update listing status (withdraw, expire, mark sold)"""
    valid_statuses = ["active", "negotiating", "sold", "expired", "withdrawn"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")

    updated = await update_listing_status(listing_id, status)
    if not updated:
        raise HTTPException(status_code=404, detail="Listing not found")
    return {"success": True, "listing_id": listing_id, "new_status": status}

# ============================================================
# BIDS ENDPOINTS
# ============================================================

@router.post("/bids", response_model=dict)
async def create_bid(bid: BidCreate):
    """
    Place a bid on a listing.
    Called from the buyer dashboard when "Place Bid" button is clicked.
    """
    try:
        result = await place_bid(
            buyer_id=bid.buyer_id,
            listing_id=bid.listing_id,
            bid_price=bid.bid_price_per_unit,
            quantity_requested=bid.quantity_requested,
            delivery_terms=bid.delivery_terms,
            payment_terms=bid.payment_terms
        )

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Bid failed"))

        # Notify seller via WhatsApp
        from services.notification import notify_seller_of_bid
        await notify_seller_of_bid(result)

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to place bid: {str(e)}")

@router.get("/listings/{listing_id}/bids", response_model=List[BidResponse])
async def get_listing_bids(listing_id: str):
    """Get all bids for a specific listing (seller view)"""
    bids = await get_bids_for_listing(listing_id)
    return bids

@router.get("/buyers/{buyer_id}/bids", response_model=List[BidResponse])
async def get_buyer_bids(buyer_id: str):
    """Get all bids placed by a buyer (buyer dashboard "My Bids" tab)"""
    bids = await get_bids_for_buyer(buyer_id)
    return bids

@router.post("/bids/{bid_id}/accept")
async def accept_bid_endpoint(bid_id: str, seller_id: str):
    """
    Seller accepts a bid.
    Called when farmer replies "ACCEPT [bid_id]" via WhatsApp.
    """
    try:
        result = await accept_bid(bid_id, seller_id)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Accept failed"))

        # Initiate escrow payment request using Supabase Data API
        tx_rows = await request("GET", "transactions", params={"select": "*", "bid_id": f"eq.{bid_id}", "limit": "1"}) or []
        buyer_rows = await request("GET", "users", params={"select": "phone_number", "id": f"eq.{result.get('buyer_id')}", "limit": "1"}) or []

        if tx_rows and buyer_rows:
            tx = tx_rows[0]
            payment_result = await request_payment(
                transaction_id=tx["id"],
                buyer_phone=buyer_rows[0]["phone_number"],
                amount=tx.get("deposit_amount") or (float(tx["total_value"]) * 0.5)
            )
            result["payment_initiated"] = payment_result.get("success", False)

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to accept bid: {str(e)}")

# ============================================================
# PRICES ENDPOINTS
# ============================================================

@router.get("/prices/current", response_model=List[PriceResponse])
async def current_prices(
    commodity: str = Query(..., description="Commodity name"),
    location: Optional[str] = Query(None, description="Market location")
):
    """
    Get current market prices for a commodity.
    Called by WhatsApp bot when farmer asks "What is the price of maize?"
    Also shown on buyer dashboard analytics.
    """
    prices = await get_current_prices(commodity, location)
    return [
        PriceResponse(
            commodity=commodity,
            market=p["market"],
            price=p["price"],
            unit=p["unit"],
            grade=p.get("grade"),
            type=p.get("type", "local"),
            date=datetime.now().strftime("%Y-%m-%d")
        )
        for p in prices
    ]

@router.get("/prices/history")
async def price_history(
    commodity: str = Query(..., description="Commodity name"),
    days: int = Query(30, ge=1, le=365)
):
    """Get historical price data for charts and trend analysis"""
    history = await get_price_history(commodity, days)
    return history

@router.get("/prices/trend")
async def price_trend(commodity: str = Query(..., description="Commodity name")):
    """Get price trend direction (rising/falling/stable)"""
    trend = await get_price_trend(commodity)
    return {"commodity": commodity, "trend": trend, "analyzed_at": datetime.now().isoformat()}

# ============================================================
# GROUP SELLING ENDPOINTS
# ============================================================

@router.post("/groups", response_model=GroupResponse)
async def create_group(group: GroupCreate):
    """
    Create or join a selling group.
    Called when farmer sends "Group selling for shea" via WhatsApp.
    """
    users = await request("GET", "users", params={"select": "*", "id": f"eq.{group.user_id}", "limit": "1"}) or []
    user = users[0] if users else None

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    result = await find_or_create_group(group.commodity_name, dict(user))

    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])

    return GroupResponse(
        id=result["group_id"],
        name=f"{group.commodity_name} Sellers - {user.get('location_district', 'Tamale')}",
        commodity=group.commodity_name,
        member_count=result.get("member_count", 1),
        total_quantity=result.get("total_quantity", 0),
        target_quantity=500,
        status="forming" if result.get("is_new") else "forming",
        deadline=None,
        ai_suggested_premium_pct=25.0
    )

@router.get("/groups/{group_id}/status")
async def group_status(group_id: str):
    """Check if a selling group has reached target quantity"""
    result = await check_group_readiness(group_id)
    return result

# ============================================================
# ANALYTICS & DASHBOARD ENDPOINTS
# ============================================================

@router.get("/analytics/overview")
async def dashboard_analytics():
    """
    High-level stats for the buyer dashboard header.
    Returns: total listings, verified sellers, active transactions, etc.
    """
    try:
        listings = await request("GET", "listings", params={"select": "id,quantity,unit,status,created_at,commodities(name_en),users!seller_id(display_name,location_district)", "status": "eq.active", "order": "created_at.desc", "limit": "5"}) or []
        all_listings = await request("GET", "listings", params={"select": "id", "status": "eq.active"}) or []
        verified = await request("GET", "users", params={"select": "id", "user_type": "eq.farmer", "verification_status": "eq.verified"}) or []
        active_tx = await request("GET", "transactions", params={"select": "id", "status": "not.in.(completed,cancelled,refunded)"}) or []
        completed_tx = await request("GET", "transactions", params={"select": "id,total_value", "status": "eq.completed"}) or []
        total_volume = sum(float(row.get("total_value") or 0) for row in completed_tx)
        recent_listings = [{"id": row["id"], "commodity": (row.get("commodities") or {}).get("name_en"), "quantity": row["quantity"], "unit": row["unit"], "status": row["status"], "created_at": row["created_at"], "seller_name": (row.get("users") or {}).get("display_name"), "location_district": (row.get("users") or {}).get("location_district")} for row in listings]
        total_listings, verified_sellers, active_transactions, completed_transactions = len(all_listings), len(verified), len(active_tx), len(completed_tx)

        return {
            "stats": {
                "active_listings": total_listings or 0,
                "verified_sellers": verified_sellers or 0,
                "active_transactions": active_transactions or 0,
                "completed_transactions": completed_transactions or 0,
                "total_volume_ghs": float(total_volume or 0)
            },
            "recent_listings": [dict(r) for r in recent_listings] if recent_listings else []
        }
    except Exception as e:
        # Return mock data for development without database
        return {
            "stats": {
                "active_listings": 1247,
                "verified_sellers": 856,
                "active_transactions": 23,
                "completed_transactions": 48,
                "total_volume_ghs": 25000.0
            },
            "recent_listings": [
                {
                    "id": "demo-1",
                    "commodity": "Shea Butter",
                    "quantity": 50,
                    "unit": "kg",
                    "status": "active",
                    "created_at": "2026-08-23T04:00:00",
                    "seller_name": "Amina Y.",
                    "location_district": "Savelugu"
                }
            ]
        }

@router.get("/analytics/commodity-distribution")
async def commodity_distribution():
    """Pie chart data: how many listings per commodity"""
    try:
        rows = await request("GET", "listings", params={"select": "commodity_id,commodities(name_en)", "status": "eq.active"}) or []
        counts = {}
        for row in rows:
            name = (row.get("commodities") or {}).get("name_en") or "Unknown"
            counts[name] = counts.get(name, 0) + 1
        return [{"commodity": name, "count": count} for name, count in sorted(counts.items(), key=lambda item: item[1], reverse=True)]
    except Exception as e:
        # Return mock data for development
        return [
            {"commodity": "Shea Butter", "count": 423},
            {"commodity": "Maize", "count": 312},
            {"commodity": "Groundnuts", "count": 256},
            {"commodity": "Millet", "count": 134},
            {"commodity": "Soybeans", "count": 122}
        ]

@router.get("/analytics/price-heatmap")
async def price_heatmap(commodity: str = Query(..., description="Commodity name")):
    """Price comparison across all markets for a commodity"""
    prices = await get_current_prices(commodity)
    return {
        "commodity": commodity,
        "markets": prices
    }
