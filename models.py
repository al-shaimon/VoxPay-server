from typing import Optional, List
from pydantic import BaseModel, Field

class ActiveLoan(BaseModel):
    hasLoan: bool = True
    amount: float = 15000.0
    remainingInstallments: int = 3
    monthlyEmi: float = 5120.0
    isFrozenDueToDisaster: bool = False
    disasterFreezeReason: Optional[str] = None

class WalletModel(BaseModel):
    accountName: str = "মোহাম্মদ করিম (Mohammad Karim)"
    phone: str = "01712-984521"
    nid: str = "19922695482000314"
    avatarUrl: str = "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80"
    bdtBalance: float = 24850.50
    ecnyBalance: float = 1250.00
    greenTokens: int = 340
    soulboundDid: str = "did:vox:0x89C1...42F7"
    kycLevel: str = "Tier 3 (Voice Biometric + ZKP Verified)"
    trustScore: int = 785
    fraudRiskLevel: str = "LOW_RISK"
    creditTier: str = "Platinum Rural Pro"
    activeLoan: ActiveLoan = Field(default_factory=ActiveLoan)

class WalletBalanceUpdate(BaseModel):
    bdtDelta: float = 0.0
    ecnyDelta: float = 0.0
    greenTokensDelta: int = 0

class TransactionCreate(BaseModel):
    type: str # 'send_money', 'loan_disbursement', 'utility', 'ecny_remit', 'emergency_aid', 'recharge'
    title: str
    recipient: str
    amount: float
    currency: str = "৳"
    status: str = "Completed"
    verifiedBy: str = "Voice-Print Biometric (98.4%)"
    zkpHash: Optional[str] = None

class TransactionModel(TransactionCreate):
    id: str
    timestamp: str

# 19 Numeric Features for the Deployed ML Model (https://voicepay-ai.onrender.com/predict)
class MLPredictionRequest(BaseModel):
    # 1. Credit Limit
    credit_limit: Optional[float] = 20000.0

    # 2. Repayment Status (Sep to Apr)
    pay_sep: Optional[int] = 0
    pay_aug: Optional[int] = 0
    pay_jul: Optional[int] = 0
    pay_jun: Optional[int] = 0
    pay_may: Optional[int] = 0
    pay_apr: Optional[int] = 0

    # 3. Bill Amounts (Sep to Apr)
    bill_sep: Optional[float] = 0.0
    bill_aug: Optional[float] = 0.0
    bill_jul: Optional[float] = 0.0
    bill_jun: Optional[float] = 0.0
    bill_may: Optional[float] = 0.0
    bill_apr: Optional[float] = 0.0

    # 4. Previous Payment Amounts (Sep to Apr)
    payment_sep: Optional[float] = 0.0
    payment_aug: Optional[float] = 0.0
    payment_jul: Optional[float] = 0.0
    payment_jun: Optional[float] = 0.0
    payment_may: Optional[float] = 0.0
    payment_apr: Optional[float] = 0.0

    # Alternative / Presets metadata
    preset_profile: Optional[str] = None # 'profile_trusted_farmer', 'profile_fraud_ring', 'profile_gig_worker'
    applicant_phone: Optional[str] = "01712-984521"
    weekly_recharge_count: Optional[float] = None
    avg_recharge_bdt: Optional[float] = None
    consecutive_utilities_paid: Optional[int] = None
    peer_trust_velocity_index: Optional[int] = None
    rwa_collateral_token: Optional[bool] = None
    sim_age_days: Optional[int] = None

class MLPredictionResponse(BaseModel):
    # Official ML API Output fields from Render
    prediction: int = 0 # 0 = low risk, 1 = high risk
    prediction_label: str = "low_risk" # "low_risk" or "high_risk"
    default_probability: float = 0.12 # 0.0 to 1.0
    probability_type: str = "platt_calibrated"
    threshold: float = 0.276105
    model_version: str = "vhre-v3-research-1.0.3"
    disclaimer: Optional[str] = (
        "Research model trained on UCI Taiwan credit-card default dataset. "
        "Output calibrated for mobile financial risk research."
    )

    # VoxPay MFS presentation mappings
    decision: str = "TRUSTED" # "TRUSTED" or "FRAUD_RISK"
    risk_score: float = 0.12
    credit_score: int = 785 # 300 to 900
    approved_loan_limit: float = 25000.0
    verdict_text: str = "স্বীকৃত বিশ্বস্ত গ্রাহক (Trusted Borrower)"
    explainability_reasons: List[str] = []
    source: str = "voicepay_ai_render_live" # "voicepay_ai_render_live" or "local_ensemble_fallback"
    timestamp: str

class LoanApplicationRequest(BaseModel):
    amount: float
    prediction: Optional[dict] = None

class DisasterTriggerRequest(BaseModel):
    scenario_id: str
    title: str
    risk_level: str # 'SEVERE', 'HIGH', 'NORMAL'
    insurance_amount: float = 8500.0
