import hashlib
import json
import os
import sqlite3
from time import time
from typing import List, Dict

from database.db import DB_PATH  # Shared DB file

class Blockchain:
    def __init__(self):
        self.chain: List[Dict] = []
        self.pending_transactions: List[Dict] = []
        self.db_connection = None
        self.initialize_database()
        self.load_chain()
        # If no blocks exist, create genesis block
        if not self.chain:
            self.create_block(proof=1, previous_hash='0')

    def initialize_database(self):
        """Ensure the database file and tables exist."""
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self.db_connection = sqlite3.connect(DB_PATH)
        self.create_tables()

    def create_tables(self):
        """Create blocks and transactions tables if they don't exist."""
        with self.db_connection:
            self.db_connection.execute('''
                CREATE TABLE IF NOT EXISTS blocks (
                    block_index INTEGER PRIMARY KEY,
                    timestamp REAL,
                    transactions TEXT,
                    proof INTEGER,
                    previous_hash TEXT
                )
            ''')
            self.db_connection.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender TEXT,
                    data TEXT,
                    signature TEXT,
                    timestamp REAL
                )
            ''')

    def load_chain(self):
        """Load existing blocks from the database into memory."""
        cursor = self.db_connection.cursor()
        cursor.execute('SELECT block_index, timestamp, transactions, proof, previous_hash FROM blocks ORDER BY block_index')
        rows = cursor.fetchall()
        for row in rows:
            block = {
                'index': row[0],
                'timestamp': row[1],
                'transactions': json.loads(row[2]),
                'proof': row[3],
                'previous_hash': row[4]
            }
            self.chain.append(block)

    def create_block(self, proof: int, previous_hash: str) -> Dict:
        """Create a new block, add it to chain and DB, reset pending transactions."""
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.pending_transactions,
            'proof': proof,
            'previous_hash': previous_hash,
        }
        self.pending_transactions = []
        self.chain.append(block)
        self.save_block_to_db(block)
        return block

    def save_block_to_db(self, block: Dict):
        """Persist a block into the blocks table."""
        with self.db_connection:
            self.db_connection.execute(
                '''
                INSERT INTO blocks (block_index, timestamp, transactions, proof, previous_hash)
                VALUES (?, ?, ?, ?, ?)
                ''',
                (
                    block['index'],
                    block['timestamp'],
                    json.dumps(block['transactions']),
                    block['proof'],
                    block['previous_hash']
                )
            )

    @staticmethod
    def hash(block: Dict) -> str:
        """Generate SHA-256 hash of a block."""
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def proof_of_work(self, last_proof: int) -> int:
        """Find a proof such that hash(last_proof, proof) starts with '0000'."""
        proof = 0
        while not self.valid_proof(last_proof, proof):
            proof += 1
        return proof

    @staticmethod
    def valid_proof(last_proof: int, proof: int) -> bool:
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    def add_transaction(self, sender: str, data: Dict, signature: str) -> None:
        """Add a transaction to pending and persist it."""
        tx = {
            'sender': sender,
            'data': data,
            'signature': signature,
            'timestamp': time()
        }
        self.pending_transactions.append(tx)
        self.save_transaction_to_db(sender, data, signature)

    def save_transaction_to_db(self, sender: str, data: Dict, signature: str):
        """Persist a transaction into the transactions table."""
        with self.db_connection:
            self.db_connection.execute(
                '''
                INSERT INTO transactions (sender, data, signature, timestamp)
                VALUES (?, ?, ?, ?)
                ''',
                (sender, json.dumps(data), signature, time())
            )

    def is_chain_valid(self, chain: List[Dict]) -> bool:
        """Verify chain integrity and proof of work."""
        previous_block = chain[0]
        for block in chain[1:]:
            if block['previous_hash'] != self.hash(previous_block):
                return False
            if not self.valid_proof(previous_block['proof'], block['proof']):
                return False
            previous_block = block
        return True

    def close_connection(self):
        """Close the DB connection when done."""
        if self.db_connection:
            self.db_connection.close()