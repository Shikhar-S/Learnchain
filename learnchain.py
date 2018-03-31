from time import time
import json
import hashlib
from uuid import uuid4
from flask import Flask, jsonify, request
class Learnchain:
    def __init__(self):
        self.chain=[]
        self.transactions=[]
        self.genesis_block=self.new_block(proof=100,previous_hash=1)

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)









