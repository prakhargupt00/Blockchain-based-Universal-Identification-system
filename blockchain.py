#Module 1,2 - Create a blockchain and Creating a Cryptocurrency based on it

import datetime 
import hashlib
import json 
from  flask import Flask, jsonify, request
import requests 
from uuid import uuid4
from urllib.parse import urlparse 

#Part 1 - Building the blockchain for Cryptocurrency 

class Blockchain:
    
    def __init__(self):
        self.chain = []
        self.transactions = []
        self.create_block(proof = 1, previous_hash = '0')
        self.nodes = set()
         
    def create_block(self, proof, previous_hash):
        block = {
                 "index": len(self.chain)+1 ,
                 "timestamp": str(datetime.datetime.now()),
                 "proof": proof,
                 "previous_hash": previous_hash,
                 "transactions": self.transactions
                 }
        self.transactions = []
        self.chain.append(block)
        return block 
    
# We need to modify our genral purpose blockchain into one for crpytocurrency by 
# adding the transactions field 
    
    def  get_previous_block(self):
        return self.chain[-1]
    
    def proof_of_work(self, previous_proof):
        new_proof = 1 
        check_proof = False
        #target 4 leading zeros
        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()  
            #operation passed need to be non symmetrical like subtraction but not addition
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof +=1 
        return new_proof 
    
    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys = True).encode()
        return  hashlib.sha256(encoded_block).hexdigest()
    
    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1 
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False
            previous_block = block
            block_index +=1 
        return True  
    
    def add_transactions(self, sender, reciever, amount):
        self.transactions.append({ "sender": sender,
                                   "reciever":reciever,
                                   "amount": amount
                                   })
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1

#add_node funciton adds nodes with netloc     
    def add_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    """ add_node function something like this 
    
    #address = 'http://127.0.0.1:5000/'
    #parsed_url = urlparse(address)
    #parsed_url
    #Out[4]: ParseResult(scheme='http', netloc='127.0.0.1:5000', path='/', params='', query='', fragment='')
    #parsed_url.netloc
    #Out[5]: '127.0.0.1:5000'
    
    """

#replace_chain applies consensus protocol and replaces each node's chain with longest chain in network 
    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length  = len(self.chain)
        for  node in network:
            response = requests.get(f'http://{node}/get_chain')  
            # f string funcntion pyhton 3.6+ syntax use variables {node} inside string
            if response.status_code == 200:
                length = response.json()['length']
                chain  = response.json()['chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        
        if longest_chain:  #i.e if longest chain is not None
            self.chain = longest_chain
            return True
        return False
        
        
#Part 2 - Mining our Blockchain  

# Creating a Web app        
app = Flask(__name__)

#Creating a address for the node on Port 5000
node_address =  str(uuid4()).replace('-','')

#creating a blockchain
blockchain = Blockchain()

#This route triggers mining of a block
@app.route('/mine_block' , methods = ['GET'])
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    blockchain.add_transactions(sender = node_address, reciever = 'Prakhar',amount = 10)
    block = blockchain.create_block(proof,previous_hash)
    response = {
                'message': "Congratulations, You just mined a block!!",
                'index': block['index'],
                'timestamp': block['timestamp'],
                'proof': block['proof'],
                'previous_hash': block['previous_hash'],
                'transactions': block['transactions']
                }
    return jsonify(response), 200

#getting the full blockchain displayed 
@app.route('/get_chain', methods = ['GET'])
def get_chain():
    response = {
                'chain': blockchain.chain,
                'length': len(blockchain.chain)
                }
    return jsonify(response), 200

#checking whether the blockchain is valid or whether some block has been corrupted and hence whole chain after that block is corrupted 
@app.route('/is_valid', methods = ['GET'])
def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if is_valid:
        response = {'message': "All good !!! Nothing to worry about. Blockchain is valid."}
    else:
        response = {'message': "Nope... So, we got issues.. blockchain not valid !!!"}
    return jsonify(response), 200

#Adding a new transaction to the blockchain using POST request
@app.route('/add_transaction', methods = ['POST'])
def add_transaction():
    json = request.get_json()
    transaction_keys = ['sender','reciever','amount']
    if not all (key in json for key in transaction_keys):
    #if not all keys in transacation_key list are not in are json then 
        return "Some elements of transaction are misssing" , 400
    index =  blockchain.add_transactions(json['sender'], json['reciever'], json['amount'])
    response = {'message': f'The transaction will be added to block {index}'}
    return jsonify(response), 201


#Part 3 - Decentralising our Blockchain

#Connecting  new nodes 
#for doing this add node in json file already containing existing nodes and post  this json file using postman 
@app.route('/connect_node', methods = ['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes') #nodes is  a list
    if nodes is None:
        return "No nodes in network", 400
    for node in nodes:
        blockchain.add_node(node)
    
    response = {
                "message": "All nodes are connected.The freecoin blockchain contains following nodes:", 
                "total_nodes": list(blockchain.nodes)
                }
    return jsonify(response), 201

#Replacing the chain by longest chain if needed :GET request
@app.route('/replace_chain', methods = ['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        response = {'message': "The nodes had different chains so chain was replaced by the longest one.",
                     'new_chain': blockchain.chain
                    }
    else:
        response = {'message': "All good. The chain was largest one.",
                    'actual_chain': blockchain.chain
                    }
    return jsonify(response), 200


#running the app 
app.run(host = '0.0.0.0', port = 5000)












