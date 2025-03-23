from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException  # type: ignore
from decimal import Decimal

# Establish connection to Bitcoin Core
RPC_USER = "divyam13"
RPC_PASSWORD = "divyam1234"
RPC_PORT = "18443"
RPC_URL = f"http://{RPC_USER}:{RPC_PASSWORD}@127.0.0.1:{RPC_PORT}"

rpc_connection = AuthServiceProxy(RPC_URL)
print("\n✅ Successfully connected to Bitcoin Core\n")

# Initialize or load wallet
WALLET_NAME = "test_wallet"
try:
    rpc_connection.loadwallet(WALLET_NAME)
    print(f"✅ Wallet '{WALLET_NAME}' successfully loaded\n")
except JSONRPCException as e:
    if "not found" in str(e):
        rpc_connection.createwallet(WALLET_NAME)
        rpc_connection.loadwallet(WALLET_NAME)
        print(f"✅ Wallet '{WALLET_NAME}' created and loaded\n")
    elif "already loaded" in str(e):
        print(f"✅ Wallet '{WALLET_NAME}' is already loaded\n")
    else:
        print(f"❌ Failed to load wallet: {e}\n")

wallet_rpc = AuthServiceProxy(f"{RPC_URL}/wallet/{WALLET_NAME}")

# Generate legacy Bitcoin addresses
address_A = wallet_rpc.getnewaddress("", "legacy")
address_B = wallet_rpc.getnewaddress("", "legacy")
address_C = wallet_rpc.getnewaddress("", "legacy")

print(f"Generated Address A: {address_A}")
print(f"Generated Address B: {address_B}")
print(f"Generated Address C: {address_C}\n")

# Send funds to Address A
try:
    amount_to_send = Decimal('0.5')
    transaction_id = wallet_rpc.sendtoaddress(address_A, amount_to_send)
    print(f"✅ Sent {amount_to_send} BTC to Address A. Transaction ID: {transaction_id}\n")

    # Mine a block to confirm the transaction
    rpc_connection.generatetoaddress(1, address_A)
    print("✅ Transaction successfully confirmed\n")
except JSONRPCException as e:
    print(f"❌ Error while funding Address A: {e}\n")

# Create a transaction from Address A to Address B
raw_transaction = None
try:
    unspent_outputs = wallet_rpc.listunspent()
    if not unspent_outputs:
        raise Exception("No unspent outputs available for spending\n")

    largest_utxo = max(unspent_outputs, key=lambda x: x['amount'])
    total_amount = Decimal(largest_utxo['amount'])
    transaction_fee = Decimal('0.00001')
    transfer_amount = Decimal('0.5')
    change_amount = total_amount - transfer_amount - transaction_fee

    inputs = [{
        "txid": largest_utxo['txid'],
        "vout": largest_utxo['vout']
    }]

    outputs = {address_B: float(transfer_amount)}
    if change_amount > Decimal('0.00000546'):
        outputs[address_A] = float(change_amount)

    raw_transaction = wallet_rpc.createrawtransaction(inputs, outputs)
    print(f"✅ Raw transaction successfully created\n")

except Exception as e:
    print(f"❌ Error while creating transaction: {e}\n")

# Sign and broadcast the transaction
if raw_transaction:
    try:
        signed_transaction = wallet_rpc.signrawtransactionwithwallet(raw_transaction)
        if not signed_transaction.get('complete'):
            raise Exception("Transaction signing was unsuccessful\n")

        print(f"✅ Transaction successfully signed\n")

        transaction_id = wallet_rpc.sendrawtransaction(signed_transaction['hex'])
        print(f"✅ Transaction broadcasted successfully! Transaction ID: {transaction_id}\n")

        # Decode and inspect the transaction
        decoded_transaction = wallet_rpc.decoderawtransaction(signed_transaction['hex'])
        print(f"✅ Decoded Transaction Details:\n{decoded_transaction}\n")

        for output in decoded_transaction['vout']:
            if output['scriptPubKey']['address'] == address_B:
                print(f"🔐 Locking Script for Address B:\n  {output['scriptPubKey']['asm']}\n")

    except JSONRPCException as e:
        print(f"❌ Error while broadcasting transaction: {e}\n")

# Display final wallet balance
final_balance = wallet_rpc.getbalance()
print(f"💰 Final Wallet Balance: {final_balance:.8f} BTC\n")

# Mine a block to confirm the transaction
miner_address = wallet_rpc.getnewaddress("", "legacy")
mined_block_hash = rpc_connection.generatetoaddress(1, miner_address)
print(f"✅ Block successfully mined: {mined_block_hash[0]}\n")

# Save generated addresses to a file
with open("addresses.txt", "w") as file:
    file.write(f"{address_A}\n{address_B}\n{address_C}")

print("✅ Task completed successfully!\n")