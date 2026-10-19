import asyncio
from models import WalletModel, TransactionCreate, MLPredictionRequest
from database import db_manager
from services.ml_client import ml_client

async def run_checks():
    print("[1/4] Testing Pydantic Models...")
    w = WalletModel()
    assert w.bdtBalance == 24850.50, f"Unexpected balance {w.bdtBalance}"
    assert w.activeLoan.amount == 15000.0, "Unexpected active loan"

    print("[2/4] Testing ML Client with Preset Profiles...")
    req_trusted = MLPredictionRequest(preset_profile="profile_trusted_farmer")
    res_trusted = await ml_client.predict_loan_risk(req_trusted)
    assert res_trusted.decision == "TRUSTED", f"Expected TRUSTED, got {res_trusted.decision}"
    assert res_trusted.prediction == 0, f"Expected prediction 0, got {res_trusted.prediction}"
    assert res_trusted.model_version == "vhre-v3-research-1.0.3"

    req_fraud = MLPredictionRequest(preset_profile="profile_fraud_ring")
    res_fraud = await ml_client.predict_loan_risk(req_fraud)
    assert res_fraud.decision == "FRAUD_RISK", f"Expected FRAUD_RISK, got {res_fraud.decision}"
    assert res_fraud.prediction == 1, f"Expected prediction 1, got {res_fraud.prediction}"

    print("[3/4] Testing ML Client with Custom 19 Numeric Features...")
    req_19 = MLPredictionRequest(
        credit_limit=20000,
        pay_sep=2, pay_aug=2, pay_jul=-1, pay_jun=1, pay_may=-1, pay_apr=2,
        bill_sep=3913, bill_aug=3102, bill_jul=689, bill_jun=0, bill_may=0, bill_apr=0,
        payment_sep=0, payment_aug=689, payment_jul=0, payment_jun=0, payment_may=0, payment_apr=0
    )
    res_19 = await ml_client.predict_loan_risk(req_19)
    assert res_19.prediction == 1
    assert res_19.prediction_label == "high_risk"
    print(f"      Live Model Output: {res_19.prediction_label}, prob={res_19.default_probability}")

    print("[4/4] Testing Database In-Memory & Transaction logic...")
    wallet = await db_manager.get_wallet()
    assert "bdtBalance" in wallet, "Missing bdtBalance in wallet"

    tx = await db_manager.add_transaction({
        "id": "TXN-TEST-1",
        "type": "send_money",
        "title": "Test Send",
        "recipient": "Karim",
        "amount": -50.0,
        "currency": "৳",
        "timestamp": "Now",
        "status": "Completed"
    })
    txs = await db_manager.get_transactions(5)
    assert len(txs) > 0, "Transactions list empty"
    assert txs[0]["id"] == "TXN-TEST-1", "Transaction ordering mismatch"

    print("ALL CHECKS PASSED SUCCESSFULLY WITH LIVE MODEL INTEGRATION!")

if __name__ == "__main__":
    asyncio.run(run_checks())
