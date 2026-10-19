from fastapi import APIRouter, HTTPException
from database import db_manager
from models import WalletModel, WalletBalanceUpdate

router = APIRouter(prefix="/api/wallet", tags=["Wallet"])

@router.get("", response_model=WalletModel)
async def get_wallet():
    """Retrieve current user wallet, balances, credit score and active loan info."""
    data = await db_manager.get_wallet()
    return WalletModel(**data)

@router.put("/balance", response_model=WalletModel)
async def adjust_balance(payload: WalletBalanceUpdate):
    """Adjust BDT, e-CNY or green tokens balance directly."""
    current = await db_manager.get_wallet()
    new_bdt = max(0.0, current.get("bdtBalance", 0.0) + payload.bdtDelta)
    new_ecny = max(0.0, current.get("ecnyBalance", 0.0) + payload.ecnyDelta)
    new_green = max(0, current.get("greenTokens", 0) + payload.greenTokensDelta)

    updated = await db_manager.update_wallet({
        "bdtBalance": round(new_bdt, 2),
        "ecnyBalance": round(new_ecny, 2),
        "greenTokens": new_green
    })
    return WalletModel(**updated)

@router.post("/reset", response_model=WalletModel)
async def reset_wallet():
    """Reset wallet back to clean demo state for repeat judging presentations."""
    default_data = WalletModel().model_dump()
    updated = await db_manager.update_wallet(default_data)
    return WalletModel(**updated)
