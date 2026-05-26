import asyncio
import aiohttp
from telegram import Bot

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID")
CHECK_INTERVAL = 30

ETHERSCAN_API = os.environ.get("ETHERSCAN_API_KEY")
BSCSCAN_API = os.environ.get("BSCSCAN_API_KEY")

WALLETS = {
    "eth": [
        "0xWalletAddress1",
    ],
    "bsc": [
        "0xWalletAddress2",
    ],
}

MIN_VALUE_50K = 50000
MIN_VALUE_100K = 100000

seen_txs = set()
bot = Bot(token=TELEGRAM_BOT_TOKEN)

async def check_evm_wallet(session, address, chain="eth"):
    if chain == "eth":
        url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&sort=desc&apikey={ETHERSCAN_API}"
        symbol, explorer = "ETH", "etherscan.io"
        eth_price = await get_eth_price(session)
    else:
        url = f"https://api.bscscan.com/api?module=account&action=txlist&address={address}&sort=desc&apikey={BSCSCAN_API}"
        symbol, explorer = "BNB", "bscscan.com"
        eth_price = await get_bnb_price(session)

    async with session.get(url) as res:
        data = await res.json()
        if data["status"] != "1":
            return
        for tx in data["result"]:
            if tx["hash"] in seen_txs:
                continue
            seen_txs.add(tx["hash"])
            value = int(tx["value"]) / 1e18
            usd_value = value * eth_price
            if usd_value < MIN_VALUE_50K:
                continue
            direction = "📤 SENT" if tx["from"].lower() == address.lower() else "📥 RECEIVED"
            if usd_value >= MIN_VALUE_100K:
                whale_tag = "🐋 Mega Whale Alert!"
            else:
                whale_tag = "🐬 Whale Alert!"
            msg = (
                f"{whale_tag} [{chain.upper()}]\n\n"
                f"{direction}: {value:.4f} {symbol} (${usd_value:,.0f})\n"
                f"💼 Wallet: {address[:8]}...{address[-6:]}\n"
                f"🔗 [TX দেখুন](https://{explorer}/tx/{tx['hash']})"
            )
            await bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=msg, parse_mode="Markdown")

async def get_eth_price(session):
    try:
        async with session.get("https://api.etherscan.io/api?module=stats&action=ethprice&apikey=" + ETHERSCAN_API) as res:
            data = await res.json()
            return float(data["result"]["ethusd"])
    except:
        return 2000

async def get_bnb_price(session):
    try:
        async with session.get("https://api.bscscan.com/api?module=stats&action=bnbprice&apikey=" + BSCSCAN_API) as res:
            data = await res.json()
            return float(data["result"]["ethusd"])
    except:
        return 600

async def main():
    print("✅ Whale Tracker Bot চালু!")
    async with aiohttp.ClientSession() as session:
        while True:
            tasks = []
            for addr in WALLETS["eth"]:
                tasks.append(check_evm_wallet(session, addr, "eth"))
            for addr in WALLETS["bsc"]:
                tasks.append(check_evm_wallet(session, addr, "bsc"))
            await asyncio.gather(*tasks, return_exceptions=True)
            await asyncio.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    import os
    asyncio.run(main())
