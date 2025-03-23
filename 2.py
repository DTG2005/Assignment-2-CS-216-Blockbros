from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException  # type: ignore
from decimal import Decimal, ROUND_DOWN

# RPC connection details
RPC_USER = "divyam13"
RPC_PASSWORD = "divyam1234"
RPC_PORT = "18443"

rpc_connection = AuthServiceProxy(f"http://{RPC_USER}:{RPC_PASSWORD}@127.0.0.1:{RPC_PORT}")

WALLET_NAME = "test_wallet"
wallet_rpc = AuthServiceProxy(f"http://{RPC_USER}:{RPC_PASSWORD}@127.0.0.1:{RPC_PORT}/wallet/{WALLET_NAME}")

# Load addresses from file
with open("./addresses.txt", "r") as file:
    address_A, address_B, address_C = [line.strip() for line in file.readlines()]

print("\n🔎 Retrieving UTXOs for Address B...")
utxos = wallet_rpc.listunspent()
utxo_B = next((utxo for utxo in utxos if utxo['address'] == address_B and utxo['spendable']), None)

if not utxo_B:
    raise Exception(f"No spendable UTXO available for Address B ({address_B}).")

print(f"✅ Found UTXO for Address B:\n  Address: {address_B}\n  TxID: {utxo_B['txid']}\n  Amount: {utxo_B['amount']:.8f} BTC\n")

# Create a transaction from Address B to Address C
print("\n💸 Initiating Transaction from B to C...")
FEE = Decimal('0.00001')
send_amount = Decimal('0.05').quantize(Decimal('0.00000001'), rounding=ROUND_DOWN)
change_amount = Decimal(utxo_B['amount']) - send_amount - FEE

if change_amount <= Decimal('0.00000546'):
    raise ValueError("Insufficient change — adjust send amount or UTXO value.")

inputs = [{"txid": utxo_B['txid'], "vout": utxo_B['vout']}]
outputs = {
    address_C: float(send_amount),
    address_B: float(change_amount)
}

raw_transaction = wallet_rpc.createrawtransaction(inputs, outputs)
print(f"✅ Raw Transaction Created: {raw_transaction}\n")

# Sign and send the transaction
signed_transaction = wallet_rpc.signrawtransactionwithwallet(raw_transaction)
if not signed_transaction.get('complete'):
    raise Exception("Failed to sign the transaction.")

print(f"✅ Transaction Signed: {signed_transaction['hex']}\n")

transaction_id = wallet_rpc.sendrawtransaction(signed_transaction['hex'])
print(f"✅ Transaction Broadcasted! TxID: {transaction_id}\n")

# Decode and inspect the transaction
print("\n🔎 Decoding the Transaction...")
decoded_transaction = wallet_rpc.decoderawtransaction(signed_transaction['hex'])

# Display decoded transaction details
print(f"✅ Decoded Transaction: {decoded_transaction}\n")

# Analyze scripts
for vin in decoded_transaction['vin']:
    print(f"🔒 Unlocking Script (ScriptSig): {vin['scriptSig']['asm']}")
    print(f"ScriptSig (Hex): {vin['scriptSig']['hex']}\n")

for vout in decoded_transaction['vout']:
    if vout['scriptPubKey']['address'] == address_C:
        print(f"🔑 Locking Script (ScriptPubKey) for Address C: {vout['scriptPubKey']['asm']}")
        print(f"ScriptPubKey (Hex): {vout['scriptPubKey']['hex']}\n")

# Display final wallet balance
wallet_balance = wallet_rpc.getbalance()
print(f"💰 Final Wallet Balance: {wallet_balance:.8f} BTC\n")

# Mine a block to confirm the transaction
miner_address = wallet_rpc.getnewaddress("", "legacy")
mined_block_hash = rpc_connection.generatetoaddress(1, miner_address)
print(f"✅ Block Mined: {mined_block_hash[0]}\n")

# Save updated addresses back to the file
with open("addresses.txt", "w") as file:
    file.write(f"{address_A}\n{address_B}\n{address_C}")

print("✅ Task Completed!\n")
