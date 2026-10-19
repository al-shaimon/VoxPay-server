import os
import logging
from typing import Optional, Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from models import WalletModel, TransactionModel

load_dotenv()

logger = logging.getLogger("voxpay.database")
logging.basicConfig(level=logging.INFO)

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "voxpay_db")

# In-memory store fallback if MongoDB is not running locally during development
_in_memory_wallet: Dict[str, Any] = WalletModel().model_dump()
_in_memory_transactions: List[Dict[str, Any]] = [
    {
        "id": "TXN-9021",
        "type": "send_money",
        "title": "টাকা পাঠানো (Send Money)",
        "recipient": "আব্দুল রহিম (01819-332145)",
        "amount": -500.0,
        "currency": "৳",
        "timestamp": "আজ, ১০:৪২ AM",
        "status": "Completed",
        "verifiedBy": "Voice Biometric AI",
        "zkpHash": "0x3f8a...99c2"
    },
    {
        "id": "TXN-9020",
        "type": "recharge",
        "title": "মোবাইল রিচার্জ (Grameenphone)",
        "recipient": "01712-984521 (Self)",
        "amount": -120.0,
        "currency": "৳",
        "timestamp": "গতকাল, ০৬:১৫ PM",
        "status": "Completed",
        "verifiedBy": "Instant Pinless Voice",
        "zkpHash": "0x9d11...bb01"
    },
    {
        "id": "TXN-9019",
        "type": "ecny_remit",
        "title": "Cross-Border e-CNY Remittance",
        "recipient": "Shenzhen Hardware Supplies Ltd.",
        "amount": -3380.0,
        "currency": "¥",
        "timestamp": "১৬ অক্টোবর, ০২:২০ PM",
        "status": "Completed",
        "verifiedBy": "CBDC Ledger Bridge",
        "zkpHash": "0x7e44...81df"
    },
    {
        "id": "TXN-9018",
        "type": "cash_in",
        "title": "টাকা গ্রহণ (Soundbox Merchant Pay)",
        "recipient": "করিম জেনারেল স্টোর (Agent)",
        "amount": 2500.0,
        "currency": "৳",
        "timestamp": "১৫ অক্টোবর, ১১:০০ AM",
        "status": "Completed",
        "verifiedBy": "NFC Soundbox Confirmation",
        "zkpHash": "0x1c88...e332"
    }
]

class DatabaseManager:
    client: Optional[AsyncIOMotorClient] = None
    db = None
    is_connected: bool = False

    async def connect(self):
        try:
            logger.info(f"Connecting to MongoDB at {MONGODB_URI}...")
            self.client = AsyncIOMotorClient(MONGODB_URI, serverSelectionTimeoutMS=2000)
            # Ping to verify
            await self.client.admin.command('ping')
            self.db = self.client[DATABASE_NAME]
            self.is_connected = True
            logger.info("Connected to MongoDB successfully!")
            await self._seed_defaults()
        except Exception as e:
            self.is_connected = False
            logger.warning(
                f"MongoDB not reachable ({e}). Operating in resilient In-Memory fallback mode. "
                "All routes will work normally in-memory without crashing!"
            )

    async def close(self):
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed.")

    async def _seed_defaults(self):
        if not self.is_connected or self.db is None:
            return
        wallet_count = await self.db.wallets.count_documents({})
        if wallet_count == 0:
            await self.db.wallets.insert_one(WalletModel().model_dump())
            logger.info("Seeded initial default wallet into MongoDB.")

        tx_count = await self.db.transactions.count_documents({})
        if tx_count == 0:
            await self.db.transactions.insert_many(_in_memory_transactions)
            logger.info("Seeded initial transactions into MongoDB.")

    # Data Access Methods (Transparently use Mongo if connected, else In-Memory)
    async def get_wallet(self) -> Dict[str, Any]:
        if self.is_connected and self.db is not None:
            doc = await self.db.wallets.find_one({})
            if doc:
                doc.pop("_id", None)
                return doc
        return dict(_in_memory_wallet)

    async def update_wallet(self, update_fields: Dict[str, Any]) -> Dict[str, Any]:
        global _in_memory_wallet
        if self.is_connected and self.db is not None:
            await self.db.wallets.update_one({}, {"$set": update_fields}, upsert=True)
            return await self.get_wallet()
        else:
            _in_memory_wallet.update(update_fields)
            return dict(_in_memory_wallet)

    async def get_transactions(self, limit: int = 20) -> List[Dict[str, Any]]:
        if self.is_connected and self.db is not None:
            cursor = self.db.transactions.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit)
            txs = await cursor.to_list(length=limit)
            return txs
        return list(_in_memory_transactions[:limit])

    async def add_transaction(self, tx: Dict[str, Any]) -> Dict[str, Any]:
        global _in_memory_transactions
        if self.is_connected and self.db is not None:
            doc = dict(tx)
            await self.db.transactions.insert_one(doc)
            doc.pop("_id", None)
            return doc
        else:
            _in_memory_transactions.insert(0, tx)
            return tx

db_manager = DatabaseManager()
