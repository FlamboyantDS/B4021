import json
from web3 import Web3
from web3.middleware import geth_poa_middleware
import time

def main():
    with open('config.json', 'r') as f:
        config = json.load(f)

    w3 = Web3(Web3.HTTPProvider(config['rpcUrl']))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    print(f"Connected to BSC. Chain ID: {w3.eth.chain_id}")

    relayer_contract = w3.eth.contract(address=config['relayerAddress'], abi=config['relayerAbi'])

    private_key = input("Enter your private key: ")
    account = w3.eth.account.from_key(private_key)
    print(f"Using address: {account.address}")

    to_address = input("Enter the recipient address (the 'to' field in the authorization): ")
    value_str = input("Enter the amount of tokens to send (e.g., 0.1 for 0.1 USDT): ")
    token_address = input("Enter the token contract address (e.g., USDT address): ")

    value = w3.to_wei(value_str, 'ether') # Assuming the token has 18 decimals, like USDT

    valid_after = int(time.time()) - 60  # 1 minute in the past
    valid_before = int(time.time()) + 3600  # 1 hour in the future
    nonce = w3.solidity_keccak(['uint256'], [int(time.time())])

    domain_separator = relayer_contract.functions.DOMAIN_SEPARATOR().call()

    message = {
        "types": {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "chainId", "type": "uint256"},
                {"name": "verifyingContract", "type": "address"},
            ],
            "Authorization": [
                {"name": "from", "type": "address"},
                {"name": "to", "type": "address"},
                {"name": "value", "type": "uint256"},
                {"name": "validAfter", "type": "uint256"},
                {"name": "validBefore", "type": "uint256"},
                {"name": "nonce", "type": "bytes32"},
            ],
        },
        "primaryType": "Authorization",
        "domain": {
            "name": "B402 Relayer",
            "version": "2",
            "chainId": config['chainId'],
            "verifyingContract": config['relayerAddress'],
        },
        "message": {
            "from": account.address,
            "to": to_address,
            "value": value,
            "validAfter": valid_after,
            "validBefore": valid_before,
            "nonce": nonce,
        },
    }

    try:
        signature = account.sign_typed_data(message)
    except Exception as e:
        print(f"Could not sign the message: {e}")
        return

    v, r, s = signature.v, signature.r, signature.s

    auth = (
        account.address,
        to_address,
        value,
        valid_after,
        valid_before,
        nonce
    )

    try:
        tx = relayer_contract.functions.transferWithAuthorization(
            auth,
            token_address,
            v,
            r,
            s
        ).build_transaction({
            'from': account.address,
            'nonce': w3.eth.get_transaction_count(account.address),
            'gas': 500000,
            'gasPrice': w3.eth.gas_price,
        })

        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        print(f"Transaction sent! Tx hash: {tx_hash.hex()}")

        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print("Transaction confirmed!")
        print(receipt)

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
