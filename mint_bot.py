import json
import time
import random
from web3 import Web3
from web3.middleware import geth_poa_middleware
from config import RPC_URL, PRIVATE_KEY, RECIPIENT_ADDRESS, AMOUNT_TO_MINT, SLEEP_INTERVAL

# Alamat Kontrak
IMPLEMENTATION_CONTRACT_ADDRESS = "0xfd2e671e3bc60f1a9765f8b8c0c8f0cf8f8f0d64"
TOKEN_CONTRACT_ADDRESS = "0x55d398326f99059ff775485246999027b3197955"

# Muat ABI
with open("implementation_abi.json", "r") as f:
    implementation_abi = json.load(f)

with open("token_abi.json", "r") as f:
    token_abi = json.load(f)

# Inisialisasi Web3
web3 = Web3(Web3.HTTPProvider(RPC_URL))
web3.middleware_onion.inject(geth_poa_middleware, layer=0)

# Periksa koneksi
if not web3.is_connected():
    print("Gagal terhubung ke RPC BNB Chain.")
    exit()

print(f"Berhasil terhubung ke RPC BNB Chain. Chain ID: {web3.eth.chain_id}")

# Siapkan akun
try:
    account = web3.eth.account.from_key(PRIVATE_KEY)
    sender_address = account.address
    print(f"Bot akan berjalan menggunakan alamat: {sender_address}")
except Exception as e:
    print(f"Error saat memuat kunci pribadi: {e}")
    print("Pastikan Anda telah mengisi PRIVATE_KEY di file config.py dengan benar.")
    exit()


# Inisialisasi Kontrak
implementation_contract = web3.eth.contract(address=IMPLEMENTATION_CONTRACT_ADDRESS, abi=implementation_abi)
token_contract = web3.eth.contract(address=TOKEN_CONTRACT_ADDRESS, abi=token_abi)

def get_authorization_params():
    """Menyiapkan parameter untuk fungsi transferWithAuthorization."""
    valid_after = int(time.time()) - 3600  # Satu jam yang lalu
    valid_before = int(time.time()) + 3600 # Satu jam dari sekarang
    nonce = "0x" + ''.join([random.choice('0123456789abcdef') for _ in range(64)])
    return valid_after, valid_before, bytes.fromhex(nonce[2:])

def sign_authorization(token, from_addr, to_addr, value, valid_after, valid_before, nonce):
    """Membuat tanda tangan EIP-712 untuk otorisasi."""
    domain = {
        "name": "B402",
        "version": "1",
        "chainId": web3.eth.chain_id,
        "verifyingContract": IMPLEMENTATION_CONTRACT_ADDRESS,
    }

    types = {
        "TransferWithAuthorization": [
            {"name": "token", "type": "address"},
            {"name": "from", "type": "address"},
            {"name": "to", "type": "address"},
            {"name": "value", "type": "uint256"},
            {"name": "validAfter", "type": "uint256"},
            {"name": "validBefore", "type": "uint256"},
            {"name": "nonce", "type": "bytes32"},
        ]
    }

    message = {
        "token": token,
        "from": from_addr,
        "to": to_addr,
        "value": value,
        "validAfter": valid_after,
        "validBefore": valid_before,
        "nonce": nonce,
    }

    signable_message = {"domain": domain, "types": types, "primaryType": "TransferWithAuthorization", "message": message}

    # EIP-712 signing in web3.py is a bit tricky. We'll manually encode and sign.
    # Note: For a real-world scenario, a more robust EIP-712 signing library might be better.
    # This is a simplified implementation.

    encoded_message = web3.eth.account._encode_structured_data(signable_message)
    signed_message = web3.eth.account.sign_message(encoded_message, private_key=PRIVATE_KEY)

    return signed_message.signature


def mint():
    """Mencoba untuk melakukan mint token."""
    try:
        # 1. Periksa Saldo & Allowance
        balance = token_contract.functions.balanceOf(sender_address).call()
        print(f"Saldo USDT saat ini: {web3.from_wei(balance, 'ether')} USDT")

        if balance < AMOUNT_TO_MINT:
            print("Saldo tidak mencukupi.")
            return

        allowance = token_contract.functions.allowance(sender_address, IMPLEMENTATION_CONTRACT_ADDRESS).call()
        print(f"Allowance untuk kontrak relayer: {web3.from_wei(allowance, 'ether')} USDT")

        # 2. Approve jika diperlukan
        if allowance < AMOUNT_TO_MINT:
            print("Allowance tidak mencukupi. Melakukan approve...")
            approve_tx = token_contract.functions.approve(
                IMPLEMENTATION_CONTRACT_ADDRESS,
                AMOUNT_TO_MINT
            ).build_transaction({
                'from': sender_address,
                'nonce': web3.eth.get_transaction_count(sender_address),
                'gas': 100000,
                'gasPrice': web3.eth.gas_price
            })

            signed_approve_tx = web3.eth.account.sign_transaction(approve_tx, PRIVATE_KEY)
            approve_tx_hash = web3.eth.send_raw_transaction(signed_approve_tx.rawTransaction)
            print(f"Transaksi Approve dikirim. Hash: {approve_tx_hash.hex()}")
            web3.eth.wait_for_transaction_receipt(approve_tx_hash)
            print("Approve berhasil.")
            time.sleep(5) # Beri jeda setelah approve

        # 3. Siapkan parameter dan tanda tangan otorisasi
        print("Menyiapkan parameter otorisasi...")
        valid_after, valid_before, nonce = get_authorization_params()

        print("Membuat tanda tangan...")
        signature = sign_authorization(
            TOKEN_CONTRACT_ADDRESS,
            sender_address,
            RECIPIENT_ADDRESS,
            AMOUNT_TO_MINT,
            valid_after,
            valid_before,
            nonce
        )

        # 4. Bangun dan kirim transaksi transferWithAuthorization
        print("Membangun transaksi minting...")
        mint_tx = implementation_contract.functions.transferWithAuthorization(
            TOKEN_CONTRACT_ADDRESS,
            sender_address,
            RECIPIENT_ADDRESS,
            AMOUNT_TO_MINT,
            valid_after,
            valid_before,
            nonce,
            signature
        ).build_transaction({
            'from': sender_address,
            'nonce': web3.eth.get_transaction_count(sender_address),
            'gas': 300000, # Gas limit yang lebih tinggi untuk transaksi kompleks
            'gasPrice': web3.eth.gas_price
        })

        signed_mint_tx = web3.eth.account.sign_transaction(mint_tx, PRIVATE_KEY)
        mint_tx_hash = web3.eth.send_raw_transaction(signed_mint_tx.rawTransaction)

        print(f"Transaksi minting dikirim! Hash: {mint_tx_hash.hex()}")
        print(f"Menunggu konfirmasi transaksi...")

        receipt = web3.eth.wait_for_transaction_receipt(mint_tx_hash)

        if receipt.status == 1:
            print("Minting Berhasil!")
        else:
            print("Minting Gagal. Status transaksi: 0")

    except Exception as e:
        print(f"Terjadi error saat proses minting: {e}")

if __name__ == "__main__":
    if PRIVATE_KEY == "GANTI_DENGAN_KUNCI_PRIBADI_ANDA" or RECIPIENT_ADDRESS == "GANTI_DENGAN_ALAMAT_PENERIMA_ANDA":
        print("!!! PENTING: Harap edit file config.py dan isi PRIVATE_KEY serta RECIPIENT_ADDRESS Anda. !!!")
    else:
        while True:
            mint()
            print(f"Menunggu {SLEEP_INTERVAL} detik sebelum mencoba lagi...")
            time.sleep(SLEEP_INTERVAL)
