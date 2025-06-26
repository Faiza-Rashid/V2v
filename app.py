import streamlit as st
import time

from blockchain import Blockchain
from vehicle_node import VehicleNode
from database.db import initialize_database, add_transaction_to_db, get_all_transactions


def main():
    st.set_page_config(page_title="Vehicle Blockchain System", layout="wide")

    # Shared blockchain instance (not persisted) for UI
    if 'blockchain' not in st.session_state:
        st.session_state.blockchain = Blockchain()
    if 'nodes' not in st.session_state:
        st.session_state.nodes = {}

    initialize_database()

    st.sidebar.title("Node Management")
    node_id = st.sidebar.text_input("New Vehicle Node ID")
    if st.sidebar.button("Create Vehicle Node"):
        if node_id:
            st.session_state.nodes[node_id] = VehicleNode(node_id)
            st.sidebar.success(f"Node '{node_id}' created.")
        else:
            st.sidebar.error("Enter a non-empty node ID.")

    st.title("🚗 Vehicle Communication Security System")
    st.subheader("Blockchain-based Secure V2V Communication")

    if st.session_state.nodes:
        selected = st.selectbox("Select Vehicle Node", list(st.session_state.nodes.keys()))
        node = st.session_state.nodes[selected]

        col1, col2 = st.columns(2)

        with col1:
            st.header("Vehicle Data Transmission")
            with st.form("tx_form"):
                speed = st.number_input("Speed (km/h)", 0, 300)
                location = st.text_input("GPS Location")
                emergency = st.checkbox("Emergency Status")
                if st.form_submit_button("Send Transaction"):
                    data = {'speed': speed, 'location': location, 'emergency': emergency}
                    signature = node.sign_transaction(data)
                    node.blockchain.add_transaction(node.node_id, data, signature)
                    # add_transaction_to_db(node.node_id, data, signature)
                    st.success("Transaction added to pending pool.")

        with col2:
            st.header("Blockchain Operations")
            if st.button("Mine Block"):
                last_block = node.blockchain.chain[-1]
                proof = node.blockchain.proof_of_work(last_block['proof'])
                prev_hash = node.blockchain.hash(last_block)
                node.blockchain.create_block(proof, prev_hash)
                st.success("New block mined!")

            if st.button("Validate Chain"):
                valid = node.blockchain.is_chain_valid(node.blockchain.chain)
                if valid:
                    st.success("Blockchain is valid.")
                else:
                    st.error("Blockchain is invalid!")

        st.header("Blockchain Explorer")
        st.write(f"Chain Length: {len(node.blockchain.chain)}")
        for block in reversed(node.blockchain.chain):
            with st.expander(f"Block #{block['index']}"):
                st.json({
                    "Index": block['index'],
                    "Timestamp": time.ctime(block['timestamp']),
                    "Transactions": block['transactions'],
                    "Proof": block['proof'],
                    "Previous Hash": block['previous_hash']
                })

        st.header("Transaction History (DB)")
        for tx in get_all_transactions():
            st.json(tx)
    else:
        st.info("No nodes available—create one via the sidebar.")

if __name__ == "__main__":
    main()