from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import auth, wallets, strategies, trades, portfolio
from .database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="DeFiAgent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(wallets.router, prefix="/wallets", tags=["wallets"])
app.include_router(strategies.router, prefix="/strategies", tags=["strategies"])
app.include_router(trades.router, prefix="/trades", tags=["trades"])
app.include_router(portfolio.router, prefix="/portfolio", tags=["portfolio"])