#!/usr/bin/env python3
"""
IFP O2 Wallet Service
FastAPI microservice for O2 token management and monitoring
Integrates with Polygon blockchain and IFP monitoring stack
"""

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
from web3 import Web3
import logging
import json
import os
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
WALLET_BALANCE = Gauge('o2_wallet_balance', 'Current O2 token balance')
THERAPY_REQUESTS = Counter('o2_therapy_requests_total', 'Total therapy requests', ['tier', 'status'])
BALANCE_CHECKS = Counter('o2_balance_checks_total', 'Total balance checks')
TRANSACTION_CHECKS = Counter('o2_transaction_checks_total', 'Total transaction checks')
BLOCKCHAIN_ERRORS = Counter('o2_blockchain_errors_total', 'Blockchain connection errors', ['error_type'])
API_REQUESTS = Counter('o2_api_requests_total', 'Total API requests', ['endpoint', 'status'])
API_LATENCY = Histogram('o2_api_latency_seconds', 'API request latency', ['endpoint'])

# FastAPI app
app = FastAPI(
    title="IFP O2 Wallet Service",
    description="O2 Token management and therapy monitoring",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class WalletBalance(BaseModel):
    wallet_address: str
    balance: float
    balance_wei: int
    last_updated: str
    blockchain: str = "Polygon"

class TherapyTier(BaseModel):
    tier: str
    cost: float
    burn_amount: float
    treasury_amount: float
    description: str

class TherapyRequest(BaseModel):
    tier: str = "standard"
    stress_level: Optional[float] = None

class TransactionInfo(BaseModel):
    tx_hash: Optional[str]
    from_address: str
    to_address: str
    value: float
    timestamp: str
    status: str

# O2 Wallet Manager
class O2WalletManager:
    def __init__(self):
        """Initialize O2 Wallet Manager with blockchain connection"""
        # Configuration
        self.polygon_rpc = os.getenv("POLYGON_RPC_URL", "https://polygon-rpc.com")
        self.o2_token_address = os.getenv("O2_TOKEN_ADDRESS", "0xEfc21AceC2D99a8F4951125d67d9Cd129FB55DcE")
        self.wallet_address = os.getenv("THE_M_WALLET", "0x638C70f337fc63DB0E108308E3dD60f71eb97342")

        # Connect to blockchain
        try:
            self.w3 = Web3(Web3.HTTPProvider(self.polygon_rpc))
            logger.info(f"Blockchain connection: {'✅ Connected' if self.w3.is_connected() else '❌ Failed'}")
        except Exception as e:
            logger.error(f"Failed to connect to blockchain: {e}")
            BLOCKCHAIN_ERRORS.labels(error_type='connection').inc()
            self.w3 = None

        # ERC20 ABI for balanceOf
        self.erc20_abi = json.loads('[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]')

        # Therapy tiers
        self.therapy_tiers = {
            "micro": {"cost": 10, "description": "Quick stress relief"},
            "standard": {"cost": 100, "description": "Standard therapy session"},
            "intensive": {"cost": 1000, "description": "Intensive therapy program"},
            "hyperbaric": {"cost": 10000, "description": "Hyperbaric O2 therapy"}
        }

        # Cache
        self.balance_cache = None
        self.cache_timestamp = None
        self.cache_ttl = 30  # 30 seconds

        logger.info(f"O2 Wallet Manager initialized")
        logger.info(f"Token: {self.o2_token_address}")
        logger.info(f"Wallet: {self.wallet_address}")

    def get_balance(self, use_cache=True) -> Dict[str, Any]:
        """Get O2 token balance from blockchain"""
        BALANCE_CHECKS.inc()

        # Check cache
        if use_cache and self.balance_cache and self.cache_timestamp:
            age = time.time() - self.cache_timestamp
            if age < self.cache_ttl:
                logger.debug(f"Returning cached balance (age: {age:.1f}s)")
                return self.balance_cache

        try:
            if not self.w3 or not self.w3.is_connected():
                logger.error("Blockchain not connected")
                BLOCKCHAIN_ERRORS.labels(error_type='not_connected').inc()
                raise HTTPException(status_code=503, detail="Blockchain connection unavailable")

            # Get balance
            contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.o2_token_address),
                abi=self.erc20_abi
            )
            balance_wei = contract.functions.balanceOf(
                Web3.to_checksum_address(self.wallet_address)
            ).call()
            balance = balance_wei / 10**18

            # Update Prometheus gauge
            WALLET_BALANCE.set(balance)

            # Update cache
            result = {
                "wallet_address": self.wallet_address,
                "balance": balance,
                "balance_wei": balance_wei,
                "last_updated": datetime.utcnow().isoformat() + "Z",
                "blockchain": "Polygon"
            }
            self.balance_cache = result
            self.cache_timestamp = time.time()

            logger.info(f"Balance retrieved: {balance:,.2f} O2")
            return result

        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            BLOCKCHAIN_ERRORS.labels(error_type='balance_query').inc()
            raise HTTPException(status_code=500, detail=f"Failed to query balance: {str(e)}")

    def check_therapy_eligibility(self, tier: str, stress_level: float = None) -> Dict[str, Any]:
        """Check if therapy is affordable and recommended"""
        if tier not in self.therapy_tiers:
            raise HTTPException(status_code=400, detail=f"Invalid tier: {tier}")

        tier_info = self.therapy_tiers[tier]
        cost = tier_info["cost"]

        # Get current balance
        balance_info = self.get_balance()
        balance = balance_info["balance"]

        # Check affordability
        affordable = balance >= cost

        # Check recommendation based on stress
        recommended = False
        if stress_level is not None:
            if stress_level > 0.7:  # High stress
                recommended = tier in ["intensive", "hyperbaric"]
            elif stress_level > 0.4:  # Medium stress
                recommended = tier in ["standard", "intensive"]
            elif stress_level > 0.2:  # Low stress
                recommended = tier == "micro"

        return {
            "tier": tier,
            "cost": cost,
            "burn_amount": cost * 0.5,
            "treasury_amount": cost * 0.5,
            "description": tier_info["description"],
            "current_balance": balance,
            "affordable": affordable,
            "recommended": recommended if stress_level is not None else None,
            "stress_level": stress_level
        }

    def get_therapy_tiers(self) -> List[TherapyTier]:
        """Get all available therapy tiers"""
        tiers = []
        for tier_name, tier_data in self.therapy_tiers.items():
            cost = tier_data["cost"]
            tiers.append(TherapyTier(
                tier=tier_name,
                cost=cost,
                burn_amount=cost * 0.5,
                treasury_amount=cost * 0.5,
                description=tier_data["description"]
            ))
        return tiers

# Initialize wallet manager
wallet_manager = O2WalletManager()

# Routes

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    blockchain_connected = wallet_manager.w3 and wallet_manager.w3.is_connected()

    return {
        "status": "healthy" if blockchain_connected else "degraded",
        "service": "o2-wallet",
        "version": "1.0.0",
        "blockchain_connected": blockchain_connected,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@app.get("/api/balance", response_model=WalletBalance)
async def get_balance(force_refresh: bool = False):
    """Get current O2 wallet balance"""
    start_time = time.time()
    try:
        balance = wallet_manager.get_balance(use_cache=not force_refresh)
        API_REQUESTS.labels(endpoint='/api/balance', status='success').inc()
        return balance
    except HTTPException as e:
        API_REQUESTS.labels(endpoint='/api/balance', status='error').inc()
        raise
    finally:
        API_LATENCY.labels(endpoint='/api/balance').observe(time.time() - start_time)

@app.get("/api/therapy/tiers", response_model=List[TherapyTier])
async def get_therapy_tiers():
    """Get available therapy tiers"""
    start_time = time.time()
    try:
        tiers = wallet_manager.get_therapy_tiers()
        API_REQUESTS.labels(endpoint='/api/therapy/tiers', status='success').inc()
        return tiers
    except Exception as e:
        API_REQUESTS.labels(endpoint='/api/therapy/tiers', status='error').inc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        API_LATENCY.labels(endpoint='/api/therapy/tiers').observe(time.time() - start_time)

@app.post("/api/therapy/check")
async def check_therapy(request: TherapyRequest):
    """Check therapy eligibility and recommendation"""
    start_time = time.time()
    try:
        result = wallet_manager.check_therapy_eligibility(request.tier, request.stress_level)
        status = 'affordable' if result['affordable'] else 'insufficient_balance'
        THERAPY_REQUESTS.labels(tier=request.tier, status=status).inc()
        API_REQUESTS.labels(endpoint='/api/therapy/check', status='success').inc()
        return result
    except HTTPException as e:
        API_REQUESTS.labels(endpoint='/api/therapy/check', status='error').inc()
        raise
    finally:
        API_LATENCY.labels(endpoint='/api/therapy/check').observe(time.time() - start_time)

@app.get("/api/stats")
async def get_stats():
    """Get O2 wallet statistics"""
    start_time = time.time()
    try:
        balance_info = wallet_manager.get_balance()
        balance = balance_info["balance"]

        # Calculate therapy affordability
        affordable_tiers = []
        for tier_name, tier_data in wallet_manager.therapy_tiers.items():
            if balance >= tier_data["cost"]:
                affordable_tiers.append(tier_name)

        API_REQUESTS.labels(endpoint='/api/stats', status='success').inc()

        return {
            "balance": balance,
            "wallet_address": wallet_manager.wallet_address,
            "blockchain": "Polygon",
            "affordable_therapy_tiers": affordable_tiers,
            "therapy_count": len(affordable_tiers),
            "last_updated": balance_info["last_updated"]
        }
    except Exception as e:
        API_REQUESTS.labels(endpoint='/api/stats', status='error').inc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        API_LATENCY.labels(endpoint='/api/stats').observe(time.time() - start_time)

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "IFP O2 Wallet Service",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "balance": "/api/balance",
            "therapy_tiers": "/api/therapy/tiers",
            "therapy_check": "/api/therapy/check",
            "stats": "/api/stats",
            "metrics": "/metrics",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8085"))
    uvicorn.run(app, host="0.0.0.0", port=port)
