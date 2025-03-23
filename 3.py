from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException  # type: ignore
from decimal import Decimal

# Step 1: Establish connection to bitcoind
RPC_USER = "divyam13"
RPC_PASSWORD = "divyam1234"
RPC_PORT = "18443"
RPC_URL = f"http://{RPC_USER}:{RPC_PASSWORD}@127.0.0.1:{RPC_PORT}"

rpc_connection = AuthServiceProxy(RPC_URL)
print("\n✅ Successfully connected to bitcoind\n")

# Step 2: Initialize or load wallet
WALLET_NAME = "test_wallet"
try:
    rpc_connection.loadwallet(WALLET_NAME)
    print(f"✅ Wallet '{WALLET_NAME}' loaded successfully\n")
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

# Step 3: Generate P2SH-SegWit addresses
address_A = wallet_rpc.getnewaddress("", "p2sh-segwit")
address_B = wallet_rpc.getnewaddress("", "p2sh-segwit")
address_C = wallet_rpc.getnewaddress("", "p2sh-segwit")

print(f"Generated Address A': {address_A}")
print(f"Generated Address B': {address_B}")
print(f"Generated Address C': {address_C}\n")

# Step 3.1: Fund Address A'
amount_to_send = Decimal('0.5')
try:
    txid = wallet_rpc.sendtoaddress(address_A, amount_to_send)
    print(f"✅ Sent {amount_to_send} BTC to Address A'. Transaction ID: {txid}\n")

    miner_address = wallet_rpc.getnewaddress("", "legacy")
    block_hash = rpc_connection.generatetoaddress(1, miner_address)
    print(f"✅ Transaction confirmed. Block mined: {block_hash[0]}\n")
except JSONRPCException as e:
    print(f"❌ Error funding Address A': {e}\n")

# Step 4: Transfer funds from A' to B'
try:
    utxos = wallet_rpc.listunspent()
    utxo = next((u for u in utxos if u['address'] == address_A), None)
    if not utxo:
        raise Exception(f"No spendable UTXO found for {address_A}\n")

    total_amount = Decimal(utxo['amount'])
    transfer_amount = Decimal('0.3')
    transaction_fee = Decimal('0.00001')
    change_amount = total_amount - transfer_amount - transaction_fee

    inputs = [{"txid": utxo['txid'], "vout": utxo['vout']}]
    outputs = {address_B: float(transfer_amount)}

    if change_amount > Decimal('0.00000546'):
        outputs[address_A] = float(change_amount)

    raw_transaction = wallet_rpc.createrawtransaction(inputs, outputs)
    print(f"✅ Raw transaction created\n")

    signed_transaction = wallet_rpc.signrawtransactionwithwallet(raw_transaction)
    if not signed_transaction.get('complete'):
        raise Exception("Transaction signing failed\n")

    txid = wallet_rpc.sendrawtransaction(signed_transaction['hex'])
    print(f"✅ Transaction broadcasted successfully! TxID: {txid}\n")

    decoded_transaction = wallet_rpc.decoderawtransaction(signed_transaction['hex'])
    print(f"✅ Decoded Transaction:\n{decoded_transaction}\n")

    for vout in decoded_transaction['vout']:
        if vout['scriptPubKey']['address'] == address_B:
            print(f"🔐 Locking Script for Address B': {vout['scriptPubKey']['asm']}\n")

except Exception as e:
    print(f"❌ Error during transaction from A' to B': {e}\n")

miner_address = wallet_rpc.getnewaddress("", "legacy")
block_hash = rpc_connection.generatetoaddress(1, miner_address)
print(f"✅ Block mined: {block_hash[0]}\n")

# Step 5: Transfer funds from B' to C'
try:
    utxos = wallet_rpc.listunspent()
    utxo_B = next((u for u in utxos if u['address'] == address_B), None)
    if not utxo_B:
        raise Exception(f"No spendable UTXO found for {address_B}\n")

    total_amount = Decimal(utxo_B['amount'])
    transfer_amount = Decimal('0.2')
    transaction_fee = Decimal('0.00001')
    change_amount = total_amount - transfer_amount - transaction_fee

    inputs = [{"txid": utxo_B['txid'], "vout": utxo_B['vout']}]
    outputs = {address_C: float(transfer_amount)}

    if change_amount > Decimal('0.00000546'):
        outputs[address_B] = float(change_amount)

    raw_transaction = wallet_rpc.createrawtransaction(inputs, outputs)
    print(f"✅ Raw transaction created\n")

    signed_transaction = wallet_rpc.signrawtransactionwithwallet(raw_transaction)
    if not signed_transaction.get('complete'):
        raise Exception("Transaction signing failed\n")

    txid = wallet_rpc.sendrawtransaction(signed_transaction['hex'])
    print(f"✅ Transaction broadcasted successfully! TxID: {txid}\n")

    decoded_transaction = wallet_rpc.decoderawtransaction(signed_transaction['hex'])
    print(f"✅ Decoded Transaction:\n{decoded_transaction}\n")

    for vin in decoded_transaction['vin']:
        print(f"🔒 Unlocking Script (scriptSig): {vin['scriptSig']['asm']}")
        print(f"ScriptSig (Hex): {vin['scriptSig']['hex']}\n")

    for vout in decoded_transaction['vout']:
        if vout['scriptPubKey']['address'] == address_C:
            print(f"🔑 Locking Script for Address C': {vout['scriptPubKey']['asm']}")
            print(f"ScriptPubKey (Hex): {vout['scriptPubKey']['hex']}\n")

except Exception as e:
    print(f"❌ Error during transaction from B' to C': {e}\n")

# Step 6: Display final wallet balance
final_balance = wallet_rpc.getbalance()
print(f"💰 Final Wallet Balance: {final_balance:.8f} BTC\n")

block_hash = rpc_connection.generatetoaddress(1, miner_address)
print(f"✅ Block mined: {block_hash[0]}\n")

# Step 7: Save generated addresses to a file
with open("addresses.txt", "w") as file:
    file.write(f"{address_A}\n{address_B}\n{address_C}")

print("✅ Task completed successfully!\n")
