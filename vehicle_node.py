import os
import json
import sqlite3
from time import time
from typing import Dict
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes

from blockchain import Blockchain
from database.db import DB_PATH

class VehicleNode:
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        self.public_key = self.private_key.public_key()
        self.blockchain = Blockchain()

        # Local transaction store
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self.db_connection = sqlite3.connect(DB_PATH)
        self.create_table()

    def create_table(self):
        cursor = self.db_connection.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT NOT NULL,
                data TEXT NOT NULL,
                signature TEXT NOT NULL,
                timestamp REAL NOT NULL
            )
        ''')
        self.db_connection.commit()

    def sign_transaction(self, data: Dict) -> str:
        transaction = {
            'sender': self.node_id,
            'data': data,
            'timestamp': time()
        }
        signature = self.private_key.sign(
            json.dumps(transaction).encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        sig_hex = signature.hex()
        # self.store_transaction(transaction, sig_hex)
        return sig_hex

    def store_transaction(self, transaction: Dict, signature: str) -> None:
        cursor = self.db_connection.cursor()
        cursor.execute(
            '''
            INSERT INTO transactions (sender, data, signature, timestamp)
            VALUES (?, ?, ?, ?)
            ''',
            (
                transaction['sender'],
                json.dumps(transaction['data']),
                signature,
                transaction['timestamp']
            )
        )
        self.db_connection.commit()

    def verify_transaction(self, transaction: Dict) -> bool:
        try:
            signature = bytes.fromhex(transaction['signature'])
            self.public_key.verify(
                signature,
                json.dumps({
                    'sender': transaction['sender'],
                    'data': transaction['data'],
                    'timestamp': transaction['timestamp']
                }).encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False

    def close_connection(self):
        self.db_connection.close()