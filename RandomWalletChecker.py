import secrets
import time
import random
from eth_account import Account
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

# ===== CONFIGURATION =====
INFURA_PROJECT_ID = "280484d36..........f5f0a60c"  # <-- Replace with your actual ID
RPC_URL = f"https://mainnet.infura.io/v3/{INFURA_PROJECT_ID}"

# Optional: Add a custom User-Agent header (some nodes appreciate it)
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}


# ===== SETUP WEB3 CONNECTION =====
def create_web3_connection():
    """Establish connection to Infura Ethereum mainnet."""
    w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={'headers': HEADERS, 'timeout': 30}))

    # Inject POA middleware (harmless for mainnet, needed for some chains)
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

    # Verify connection
    if not w3.is_connected():
        raise ConnectionError("Failed to connect to Infura. Check your project ID and network.")

    # Test a simple call to ensure the node is responsive
    try:
        block = w3.eth.block_number
        print(f"✅ Connected to Infura. Current block: {block}")
    except Exception as e:
        raise ConnectionError(f"Connected but RPC call failed: {e}")

    return w3


# ===== BALANCE CHECK WITH RETRIES =====
def get_balance_with_retry(w3, address, max_retries=3):
    """Fetch balance with exponential backoff on failure."""
    for attempt in range(max_retries):
        try:
            balance_wei = w3.eth.get_balance(address)
            return balance_wei
        except Exception as e:
            print(f"⚠️  Balance check failed (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                sleep_time = 2 ** attempt  # 1, 2, 4 seconds
                time.sleep(sleep_time)
    raise Exception(f"Failed to get balance for {address} after {max_retries} retries.")


# ===== MAIN LOOP =====
def monitor_random_keys():
    try:
        w3 = create_web3_connection()
    except Exception as e:
        print(f"Fatal: {e}")
        return

    print("\n🚀 Starting wallet monitor. Press Ctrl+C to stop.\n")
    attempts = 0

    while True:
        # Generate a cryptographically secure random private key
        priv_key = "0x" + secrets.token_hex(32)
        account = Account.from_key(priv_key)
        address = account.address

        # Display progress (truncate private key for readability)
        print(f"[{attempts}] Checking Address: {address}  (Key: {priv_key[:10]}...)")

        try:
            balance_wei = get_balance_with_retry(w3, address)
            if balance_wei > 0:
                balance_eth = w3.from_wei(balance_wei, 'ether')
                print("\n" + "=" * 50)
                print("🎉🎉🎉 FUNDED WALLET FOUND! 🎉🎉🎉")
                print(f"Address:     {address}")
                print(f"Private Key: {priv_key}")
                print(f"Balance:     {balance_eth} ETH")
                print("=" * 50 + "\n")
                # Optionally write to a file
                with open("found_wallets.txt", "a") as f:
                    f.write(f"{address},{priv_key},{balance_eth} ETH\n")
                break  # Stop after first find (remove if you want to continue)
        except Exception as e:
            print(f"❌ Error checking balance: {e}")

        attempts += 1

        # ✅ Increased random delay (2 to 5 seconds) to stay well within Infura's free tier limits
        time.sleep(random.uniform(1.5, 3))


if __name__ == "__main__":
    try:
        monitor_random_keys()
    except KeyboardInterrupt:

        print("\n🛑 Monitor stopped by user.")
