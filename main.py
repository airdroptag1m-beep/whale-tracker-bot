import asyncio
import aiohttp
from telegram import Bot

TELEGRAM_BOT_TOKEN = "এখানে_bot_token_বসান"
TELEGRAM_CHANNEL_ID = "@Tradecryptolife"
CHECK_INTERVAL = 30

WALLETS = {
    "eth": [
        "0xWalletAddress1",
    ],
    "bsc": [
        "0xWalletAddress2",
    ],
    "sol": [
        "SolanaWalletAddress1",
    ]
}

ETHERSCAN_API = "এখানে_etherscan_key"
BSCSCAN_API = "এখানে_bscscan_key"
HELIUS_API = "এখানে_helius_key"

seen_txs = set()
bot = Bot(token=TELEGRAM_BOT_TOKEN)

async def check_evm_wallet(session, address, chain="eth"):
    if chain == "eth":
        url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&sort=desc&apikey={ETHERSCAN_API}&offset=5"
        symbol, explorer = "ETH", "etherscan.io"
    else:
        url = f"https://api.bscscan.com/api?module=account&action=txlist&address={address}&sort=desc&apikey={BSCSCAN_API}&offset=5"
        symbol, explorer = "BNB", "bscscan.com"

    async with session.get(url) as res:
        data = await res.json()
        if data["status"] != "1":
            return
        for tx in data["result"]:
            if tx["hash"] in seen_txs:
                continue
            seen_txs.add(tx["hash"])
            value = int(tx["value"]) / 1e18
            if value < 0.01:
                continue
            direction = "📤 SENT" if tx["from"].lower() == address.lower() else "📥 RECEIVED"
            msg = (
                f"🐋 *Whale Alert!* [{chain.upper()}]\n\n"
                f"{direction}: `{value:.4f} {symbol}`\n"
                f"👛 Wallet: `{address[:8]}...{address[-6:]}`\n"
                f"🔗 [TX দেখুন](https://{explorer}/tx/{tx['hash']})"
            )
            await bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=msg, parse_mode="Markdown")

async def check_sol_wallet(session, address):
    url = f"https://api.helius.xyz/v0/addresses/{address}/transactions?api-key={HELIUS_API}&limit=5"
    async with session.get(url) as res:
        txs = await res.json()
        for tx in txs:
            tx_id = tx.get("signature", "")
            if tx_id in seen_txs:
                continue
            seen_txs.add(tx_id)
            amount = tx.get("nativeTransfers", [{}])[0].get("amount", 0) / 1e9
            if amount < 0.1:
                continue
            msg = (
                f"🐋 *Whale Alert!* [SOL]\n\n"
                f"💰 Amount: `{amount:.4f} SOL`\n"
                f"👛 Wallet: `{address[:8]}...{address[-6:]}`\n"
                f"🔗 [TX দেখুন](https://solscan.io/tx/{tx_id})"
            )
            await bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=msg, parse_mode="Markdown")

async def main():
    print("✅ Whale Tracker Bot চালু!")
    async with aiohttp.ClientSession() as session:
        while True:
            tasks = []
            for addr in WALLETS["eth"]:
                tasks.append(check_evm_wallet(session, addr, "eth"))
            for addr in WALLETS["bsc"]:
                tasks.append(check_evm_wallet(session, addr, "bsc"))
            for addr in WALLETS["sol"]:
                tasks.append(check_sol_wallet(session, addr))
            await asyncio.gather(*tasks, return_exceptions=True)
            await asyncio.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    asyncio.run(main())
