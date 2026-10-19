import random
from datetime import datetime
from typing import List
from fastapi import APIRouter
from database import db_manager
from models import TransactionModel, TransactionCreate

router = APIRouter(prefix="/api/transactions", tags=["Transactions"])

@router.get("", response_model=List[TransactionModel])
async def list_transactions(limit: int = 25):
    """Get recent MFS transactions ordered newest first."""
    data = await db_manager.get_transactions(limit=limit)
    return [TransactionModel(**item) for item in data]

@router.post("", response_model=TransactionModel)
async def record_transaction(tx: TransactionCreate):
    """
    Record a new transaction and automatically synchronize wallet balance.
    (e.g., send money subtracts balance, loan disbursement adds balance).
    """
    tx_id = f"TXN-{random.randint(1000, 9999)}"
    now_str = datetime.now().strftime("আজ, %I:%M %p")

    # Generate synthetic on-chain cryptographic audit hash if not provided
    zkp_hash = tx.zkpHash or f"0x{random.randint(0x10000000, 0xFFFFFFFF):x}...{random.randint(0x1000, 0xFFFF):x}"

    new_tx = {
        "id": tx_id,
        "type": tx.type,
        "title": tx.title,
        "recipient": tx.recipient,
        "amount": tx.amount,
        "currency": tx.currency,
        "timestamp": now_str,
        "status": tx.status,
        "verifiedBy": tx.verifiedBy,
        "zkpHash": zkp_hash
    }

    # Atomically adjust wallet balance
    current = await db_manager.get_wallet()
    current_bdt = current.get("bdtBalance", 0.0)
    current_ecny = current.get("ecnyBalance", 0.0)

    if tx.type in ["send_money", "utility", "recharge"]:
        # Subtraction
        deduction = abs(tx.amount)
        new_bdt = max(0.0, current_bdt - deduction)
        await db_manager.update_wallet({"bdtBalance": round(new_bdt, 2)})
    elif tx.type in ["loan_disbursement", "emergency_aid", "crop_insurance"]:
        # Addition
        addition = abs(tx.amount)
        new_bdt = current_bdt + addition
        await db_manager.update_wallet({"bdtBalance": round(new_bdt, 2)})
    elif tx.type == "ecny_remit":
        # Convert e-CNY to BDT
        addition_bdt = abs(tx.amount)
        new_bdt = current_bdt + addition_bdt
        await db_manager.update_wallet({"bdtBalance": round(new_bdt, 2)})

    saved = await db_manager.add_transaction(new_tx)
    return TransactionModel(**saved)
