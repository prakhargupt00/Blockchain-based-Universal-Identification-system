

import datetime 
import hashlib
import json 
from  flask import Flask, jsonify, request
import requests 
from uuid import uuid4
from urllib.parse import urlparse 


class Blockchain:
    
    def __init__(self):
        self.chain = []
        self.transactions = []
        self.create_block(proof = 1, previous_hash = '0')
        self.nodes = set()
        self.transaction_types = set()
         
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
    
    
    def  get_previous_block(self):
        return self.chain[-1]
    
    def proof_of_work(self, previous_proof):
        new_proof = 1 
        check_proof = False
        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()  
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
    
    def add_employment_transactions(self, employeeName, employeeUID, employerName, employerUID, startDate, endDate):
        self.transactions.append({
									"recordType": "employment",
									"recordData": {
										"employeeName": employeeName,
										"employeeUID": employeeUID,
										"employerName": employerName,
										"employerUID": employerUID,
										"startDate": startDate,
										"endDate": endDate,
									},
								})
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1

    def add_criminal_transactions(self, accusedUID, accusedName, offenceDetails, policeStationUID, stateHead, status, IPCRule):
        self.transactions.append({ "recordType": "criminal",
                                    "recordData" :{
                                       "accusedUID": accusedUID,
                                       "accusedName": accusedName,
                                       "offenceDetails": offenceDetails,
                                       "policeStationUID": policeStationUID,
                                       "stateHead": stateHead,
                                       "status": status,
                                       "IPCRule": IPCRule
                                       }
                                    })
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1

    def add_health_transactions(self, name, UID, fingerprint, retinaScan, vaccinations, medicines, majorAccidents):
        self.transactions.append({  "recordType" : "health",
                                    "recordData": {
                                        "name":name,
                                        "UID": UID,
                                        "fingerprint": fingerprint,
                                        "retinaScan": retinaScan,
                                        "vaccinations": vaccinations,
                                        "medicines": medicines,
                                        "majorAccidents": majorAccidents
                                        }
                                    })
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1

    
    def add_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def add_transaction_type(self, transaction_type):
    	self.transaction_type.add(transaction_type)

    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length  = len(self.chain)
        for  node in network:
            response = requests.get(f'http://{node}/get_chain')  
            if response.status_code == 200:
                length = response.json()['length']
                chain  = response.json()['chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        
        if longest_chain: 
            self.chain = longest_chain
            return True
        return False

    # Added by Kshitiz
    def sync_transactions(self):
        network = self.nodes
        record_type = None
        record_data = None
        transactions_in_node = None
        for node in network:
            response = requests.get(f'http://{node}/get_transactions/')
            if response.status_code == 200:
                transactions_in_node = response.json()['transactions']
                if transactions_in_node:
                    for transaction in transactions_in_node:
                        record_type = transaction['recordType']
                        record_data = transaction['recordData']
                        if record_type and record_data:
                        	if record_type == "criminal":
                        		self.add_criminal_transactions(record_data['accusedName'],
                                    record_data['accusedUID'],
                                    record_data['offenceDetails'],
                                    record_data['policeStationUID'],
                                    record_data['status'],
                                    record_data['IPCRule'],
                                    record_data['stateHead']
                                    )
                        	if record_type == "employment":
                        		self.add_employment_transaction(record_data['employeeName'],
                        			record_data['employeeUID'],
                        			record_data['employerName'],
                        			record_data['employerUID'],
                        			record_data['startDate'],
                        			record_data['endDate']
                        			)
                        	if record_type == "health":
                        		self.add_health_transactions(record_data['name'],
                                    record_data['UID'],
                                    record_data['fingerprint'],
                                    record_data['retinaScan'],
                                    record_data['vaccinations'],
                                    record_data['medicines']
                                    )
        if transactions_in_node:
            return True
        return False
    
            
    def empty_transactions(self):
        network = self.nodes
        for node in network:
            response = requests.get(f'http://{node}/empty_transactions/')
            if response.status_code != 200:
                return False
        return True
        
app = Flask(__name__)

node_address =  str(uuid4()).replace('-','')

blockchain = Blockchain()

@app.route('/home/' , methods = ['GET'])
def home():
	response = "<h1>Welcome to Blockchain based Unique Identification System</h1>";
	res2 = "<h3>You can use following functionalities: </h3>"
	func = "<ul><li>mine_block</li><li>get_chain</li><li>is_valid</li><li>add_employment_transaction</li><li>add_health_transaction</li>"
	fucn2 = "<li>add_criminal_transaction</li><li>connect_node</li><li>replace_chain</li><li>get_transactions</li><li>empty_transactions</li></ul>"
	return response+res2+func+fucn2

@app.route('/mine_block' , methods = ['GET'])
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    # blockchain.add_transactions(sender = node_address, reciever = 'Prakhar',amount = 10)

    # Added by Kshitiz
    blockchain.sync_transactions()
    
    block = blockchain.create_block(proof, previous_hash)
    
    # Added by Kshitiz
    blockchain.empty_transactions()
    response = {
                'message': "Congratulations, You just mined a block!!",
                'index': block['index'],
                'timestamp': block['timestamp'],
                'proof': block['proof'],
                'previous_hash': block['previous_hash'],
                'transactions': block['transactions']
                }
    return jsonify(response), 200

@app.route('/get_chain', methods = ['GET'])
def get_chain():
    response = {
                'chain': blockchain.chain,
                'length': len(blockchain.chain)
                }
    return jsonify(response), 200

@app.route('/is_valid', methods = ['GET'])
def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if is_valid:
        response = {'message': "All good !!! Nothing to worry about. Blockchain is valid."}
    else:
        response = {'message': "Nope... So, we got issues.. blockchain not valid !!!"}
    return jsonify(response), 200


@app.route('/add_employment_transaction', methods = ['POST'])
def add_employment_transaction():
	json = request.get_json()
    transaction_keys = ['recordType','recordData']
    if not all (key in json for key in transaction_keys):
        return "Some elements of transaction are misssing" , 400
	record_data = json['recordData']
    index =  blockchain.add_employment_transaction(record_data['employeeName'],
                        			record_data['employeeUID'],
                        			record_data['employerName'],
                        			record_data['employerUID'],
                        			record_data['startDate'],
                        			record_data['endDate']
                        			)
    response = {'message': f'The employment transaction will be added to block {index}'}

@app.route('/add_criminal_transaction', methods = ['POST'])
def add_criminal_transaction():
    json = request.get_json()
    transaction_keys = ['recordType','recordData']
    if not all (key in json for key in transaction_keys):
        return "Some elements of transaction are misssing" , 400
    record_data = json[recordData]
    index =  blockchain.add_criminal_transactions( record_data['accusedName'],
                                    record_data['accusedUID'],
                                    record_data['offenceDetails'],
                                    record_data['policeStationUID'],
                                    record_data['status'],
                                    record_data['IPCRule'],
                                    record_data['stateHead'])
    response = {'message': f'The criminal transaction will be added to block {index}'}
    return jsonify(response), 201

@app.route('/add_health_transaction', methods = ['POST'])
def add_health_transaction():
    json = request.get_json()
    transaction_keys = ['recordType','recordData']
    if not all (key in json for key in transaction_keys):
        return "Some elements of transaction are misssing" , 400
    record_data = json[recordData]
    index =  blockchain.add_health_transactions( record_data['name'],
                                    record_data['UID'],
                                    record_data['fingerprint'],
                                    record_data['retinaScan'],
                                    record_data['vaccinations'],
                                    record_data['medicines']
                                    )
    response = {'message': f'The health transaction will be added to block {index}'}
    return jsonify(response), 201


@app.route('/connect_node', methods = ['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes') 
    if nodes is None:
        return "No nodes in network", 400
    for node in nodes:
        blockchain.add_node(node)
    
    response = {
                "message": "All nodes are connected.The freecoin blockchain contains following nodes:", 
                "total_nodes": list(blockchain.nodes)
                }
    return jsonify(response), 201

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


# Code added by Kshitiz
@app.route('/get_transactions/', methods=['GET'])
def get_transactions():
    """
        Method to get transactions currently not addded in the block from specific node.
    """
    response = {
        'number_of_transactions': len(blockchain.transactions),
        'transactions': blockchain.transactions,
    }
    return jsonify(response), 200

@app.route('/empty_transactions/', methods=['GET'])
def empty_transactions():
    blockchain.transactions = []
    response = {'message': 'Transactions were successfully emptied'}
    return jsonify(response), 200

app.run(host = '0.0.0.0', port = 5002)













