from time import time
import json
import hashlib
from uuid import uuid4
from flask import Flask, jsonify, request
import requests

from urlparse import urlparse
class Learnchain:
    def __init__(self):
        self.chain=[]
        self.transactions=[]
        self.genesis_block=self.new_block(proof=100,previous_hash=1)
        self.nodes=set()

    def add_node(self,address):
        self.nodes.add(urlparse(address).netloc) #to removes http 

    def valid_chain(self,chain):
        last_block=chain[0]
        indx=1
        while(indx<len(chain)):
            block=chain[indx]

            if(block['previous_hash']!=self.hash(last_block)):
                return False
            if(not self.valid_proof(last_block['proof'],block['proof'])):
                return False
            last_block=block
            indx+=1
        print 'Returning true'
        return True

    def resolve_conflicts(self):
        maxlen=len(self.chain)
        new_chain=None
        for node in self.nodes:
            response=requests.get('http://%s/chain'%(node))

            if(response.status_code==200):
                length=response.json()['length']
                chain=response.json()['chain']
                print length 
                if(length>maxlen and self.valid_chain(chain)):
                    new_chain=chain
                    maxlen=length
        if(new_chain is not None):
            self.chain=new_chain
            return True
        else:
            return False


    def new_block(self,proof,previous_hash=None):
        #makes a new block and returns it after appending to chain
        if(previous_hash is None):
            previous_hash=self.hash(self.chain[-1])
        block={
            'index': len(self.chain)+1,
            'timestamp': time(),
            'proof': proof,
            'transactions' : self.transactions,
            'previous_hash': previous_hash
        }
        self.transactions=[]
        self.chain.append(block)
        return block

    @staticmethod
    def hash(block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1]

    def new_transaction(self,sender,recipient,amount):

        current_transaction={
            'sender': sender,
            'recipient':recipient,
            'amount':amount
        }

        self.transactions.append(current_transaction)

        return self.last_block['index']+1

    def proof_of_work(self,last_proof):
        proof=0
        while not self.valid_proof(last_proof,proof):
            proof+=1
        return proof

    @staticmethod
    def valid_proof(last_proof,proof):
        guess='%s%s'%(last_proof,proof)
        guess_hash=hashlib.sha256(guess).hexdigest()
        return (guess_hash[:4]=="0000")

app=Flask(__name__)
unique_identifier=str(uuid4()).replace('-','')
blockchain=Learnchain()

@app.route('/mine',methods=['GET'])
def mine():
    last_block=blockchain.last_block
    last_proof=last_block['proof']
    proof=blockchain.proof_of_work(last_proof)

    blockchain.new_transaction(
        sender=0,
        recipient=unique_identifier,
        amount=1)

    previous_hash=blockchain.hash(last_block)
    block=blockchain.new_block(proof,previous_hash)
    response = {
    'message': "New Block Forged",
    'index': block['index'],
    'transactions': block['transactions'],
    'proof': block['proof'],
    'previous_hash': block['previous_hash'],
    }
    return jsonify(response),200

@app.route('/transactions/new',methods=['POST'])
def new_transaction():
    values=request.get_json()
    required=['sender','recipient','amount']
    if(not all(k in values for k in required)):
        return 'Missing values',400
    index=blockchain.new_transaction(values['sender'],values['recipient'],values['amount'])
    response={'message':'Transaction will be added to block %d' % (index)}
    return jsonify(response),200

@app.route("/chain",methods=['GET'])
def full_cahin():
    response={
        'chain' : blockchain.chain,
        'length' : len(blockchain.chain)
    }
    return jsonify(response), 200

@app.route("/node/register",methods=['POST'])
def register_nodes():
    values=request.get_json()

    nodes=values['nodes']
    if nodes is None:
        return "Error : Invalid list of nodes",400

    for node in nodes:
        blockchain.add_node(node)

    response={
        'message': 'New node has been added',
        'available_nodes': list(blockchain.nodes)
    }

    return jsonify(response),201

@app.route('/node/resolve',methods=['GET'])
def consensus():
    replaced=blockchain.resolve_conflicts()
    if replaced:
        response={
        'message':'Chain has been replaced',
        'chain': blockchain.chain
        }
    else:
        response={
        'message':'This chain is authoritative',
        'chain':blockchain.chain
        }
    return jsonify(response),200

if __name__ == '__main__':
    # app.run(host='0.0.0.0',port=5001)
    app.run(host='0.0.0.0', port=5000)