### import the libraries
import datetime
import hashlib
import json
import pandas as pd
from flask import Flask,jsonify,request
import requests
from uuid import uuid4
from urllib.parse import urlparse

## PArt 1- Building the BlockChain

class BlockChain:
    def __init__(slf):
        slf.chain=[]
        slf.transactions=[]
        slf.nodes=set()
        slf.create_block(proof=1,previous_hash='0')
        
    def create_block(slf,proof,previous_hash):
        blc={'index':len(slf.chain)+1,
               'timestamp':str(datetime.datetime.now()),
               'proof':proof,
               'previous_hash':previous_hash,
               'transactions':slf.transactions
            
            }
        slf.transactions=[]
        slf.chain.append(blc)
        return blc
    
    def get_prev_block(slf):
        return slf.chain[-1]
    
    def proof_of_work(slf, prev_proof):
        new_proof = 1
        chk_proof = False
        while chk_proof is False:
            hash_operation = hashlib.sha512(str(new_proof**2 - prev_proof**2).encode()).hexdigest()
            if hash_operation[:4] == '0000':
                chk_proof = True
            else:
                new_proof += 1
        return new_proof
    
    def hash(slf, blc):
        enc_blc = json.dumps(blc, sort_keys = True).encode()
        return hashlib.sha512(enc_blc).hexdigest()
    
    def is_chain_valid(slf, chain):
        prev_blc = chain[0]
        blc_index = 1
        while blc_index < len(chain):
            blc = chain[blc_index]
            if blc['previous_hash'] != slf.hash(prev_blc):
                return False
            prev_proof = prev_blc['proof']
            proof = blc['proof']
            hash_operation = hashlib.sha512(str(proof**2 - prev_proof**2).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False
            prev_blc = blc
            blc_index += 1
        return True 
    
    def add_transaction(slf,sender,receiver,amount, pancard):
        df = pd.read_excel (r'Pancard.xlsx')
        if df['Pancard'].str.contains(pancard).any():
            slf.transactions.append({
                'sender':sender,
                'receiver':receiver,
                'amount':amount,
                'pancard': pancard
              
            })
            
            prev_block=slf.get_prev_block()
            return prev_block['index']+1
       
    def add_node(slf,add):
        parsed_url=urlparse(add)
        slf.nodes.add(parsed_url.netloc)
        
    ### consensus protocol
    
    def replace_chain(slf):
        network=slf.nodes
        longest_chain=None
        max_length=len(slf.chain)
        
        for node in network:
            response=requests.get(f'http://{node}/get_chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and slf.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        if longest_chain:
            slf.chain = longest_chain
            return True
        return False
        
            

## Part 2- Mining the BlockChain

app=Flask(__name__)


node_address=str(uuid4()).replace('-','')

### Create The BlockChain
blockchain=BlockChain()

## Create a web app for the API
### Mining the new block
@app.route('/mine_block', methods = ['GET'])
def mine_block():
    prev_block = blockchain.get_prev_block()
    prev_proof = prev_block['proof']
    proof = blockchain.proof_of_work(prev_proof)
    previous_hash = blockchain.hash(prev_block)
    blockchain.add_transaction(sender = node_address, receiver = 'sam', amount = 1, pancard='None')
    block = blockchain.create_block(proof, previous_hash)
    response = {'message': 'Congratulations, you just mined a block!',
                'index': block['index'],
                'timestamp': block['timestamp'],
                'proof': block['proof'],
                'previous_hash': block['previous_hash'],
                'transactions': block['transactions']}
    return jsonify(response), 200

# Getting the full Blockchain
@app.route('/get_chain', methods = ['GET'])
def get_chain():
    response = {'chain': blockchain.chain,
                'length': len(blockchain.chain)}
    return jsonify(response), 200


# Checking if the Blockchain is valid
@app.route('/is_valid', methods = ['GET'])
def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if is_valid:
        response = {'message': 'All good. The Blockchain is valid.'}
    else:
        response = {'message': 'Houston, we have a problem. The Blockchain is not valid.'}
    return jsonify(response), 200


# Adding a new transaction to the Blockchain
@app.route('/add_transaction', methods = ['POST'])
def add_transaction():
    json = request.get_json()
    pa=json['pancard']
    transaction_keys = ['sender', 'receiver', 'amount','pancard']
    if not all(key in json for key in transaction_keys):
        return 'Some elements of the transaction are missing', 400
    df = pd.read_excel (r'C:/Users/SHUBHAM/Desktop/Desktop Folder/GIMBlockchainDemo-main/Pancard.xlsx')
    if df['Pancard'].str.contains(pa).any():
       index = blockchain.add_transaction(json['sender'], json['receiver'], json['amount'], json['pancard'])
       response = {'message': f'This transaction will be added to Block {index}'}
    else:
        return 'This transaction can not be added to Block because of incorrect pancard'
    return jsonify(response), 201

# Part 3 - Decentralizing our Blockchain

# Connecting new nodes
@app.route('/connect_node', methods = ['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')
    if nodes is None:
        return "No node", 400
    for node in nodes:
        blockchain.add_node(node)
    response = {'message': 'All the nodes are now connected. The Blockchain now contains the following nodes:',
                'total_nodes': list(blockchain.nodes)}
    return jsonify(response), 201

# Replacing the chain by the longest chain if needed
@app.route('/replace_chain', methods = ['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        response = {'message': 'The nodes had different chains so the chain was replaced by the longest one.',
                    'new_chain': blockchain.chain}
    else:
        response = {'message': 'All good. The chain is the largest one.',
                    'actual_chain': blockchain.chain}
    return jsonify(response), 200



# Running the app
app.run(host = '0.0.0.0', port = 7001)