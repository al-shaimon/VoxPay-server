import random
from datetime import datetime
from fastapi import APIRouter
from database import db_manager
from models import DisasterTriggerRequest

router = APIRouter(prefix="/api/weather", tags=["Satellite Weather Protection"])

@router.post("/trigger-disaster")
async def trigger_disaster(req: DisasterTriggerRequest):
    """
    Automated Oracle trigger from satellite weather feed (e.g. Cyclone Remal / Flood).
    1. Freezes loan installments with 0% penalty.
    2. Automatically disburses crop insurance into user wallet.
    3. Writes immutable transaction audit log.
    """
    current = await db_manager.get_wallet()
    active_loan = current.get("activeLoan", {})

    insurance_payout = req.insurance_amount or 8500.0
    new_balance = current.get("bdtBalance", 0.0) + insurance_payout

    # Freeze loan installments
    updated_wallet = await db_manager.update_wallet({
        "bdtBalance": round(new_balance, 2),
        "activeLoan": {
            **active_loan,
            "isFrozenDueToDisaster": True,
            "disasterFreezeReason": req.title
        }
    })

    # Record crop insurance payout in ledger
    tx_id = f"TXN-{random.randint(1000, 9999)}"
    now_str = datetime.now().strftime("আজ, %I:%M %p")
    zkp_hash = f"0x{random.randint(0x10000000, 0xFFFFFFFF):x}...{random.randint(0x1000, 0xFFFF):x}"

    insurance_tx = {
        "id": tx_id,
        "type": "crop_insurance",
        "title": "স্বয়ংক্রিয় শস্যবীমা (Crop Insurance)",
        "recipient": "VoxPay Satellite Weather Oracle",
        "amount": insurance_payout,
        "currency": "৳",
        "timestamp": now_str,
        "status": "Completed",
        "verifiedBy": "Sentinel-3 Satellite Oracle",
        "zkpHash": zkp_hash
    }
    await db_manager.add_transaction(insurance_tx)

    return {
        "success": True,
        "disasterScenario": req.title,
        "loanFrozen": True,
        "insuranceDisbursed": insurance_payout,
        "newBalance": new_balance,
        "transactionId": tx_id
    }

@router.post("/reset")
async def reset_weather_normal():
    """Reset weather conditions to normal and unfreeze loan installments."""
    current = await db_manager.get_wallet()
    active_loan = current.get("activeLoan", {})

    updated_wallet = await db_manager.update_wallet({
        "activeLoan": {
            **active_loan,
            "isFrozenDueToDisaster": False,
            "disasterFreezeReason": None
        }
    })

    return {
        "success": True,
        "status": "Weather normalized, installments resumed.",
        "activeLoan": updated_wallet.get("activeLoan")
    }
