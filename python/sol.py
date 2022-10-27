import base64
from construct.core import ConstError
from decimal import Decimal
import json
import requests
from requests.exceptions import ReadTimeout
import struct
import sys
import time

from layout import (ACCOUNT_LAYOUT,
                     AMM_INFO_LAYOUT_V4,
                     OPEN_ORDERS_LAYOUT,
                     SERUM_PROGRAM_ID_V3,
                     SWAP_INSTRUCTION_FORMAT,
                     RAYDIUM_SWAP_INSTRUCTION_IDX,
                     MARKET_STATE_LAYOUT_V2,
                     LIQUIDITY_POOL_PROGRAM_ID_V4)

from solana.rpc.api import Client
from solders.rpc.filter import Memcmp
from solana.system_program import create_account, CreateAccountParams, transfer, TransferParams
from solana.transaction import AccountMeta, Keypair, Transaction, TransactionInstruction
from spl.token.instructions import (close_account,
                                    create_associated_token_account,
                                    initialize_account,
                                    transfer_checked)
from spl.token.instructions import (ASSOCIATED_TOKEN_PROGRAM_ID,
                                    CloseAccountParams,
                                    InitializeAccountParams,
                                    TransferCheckedParams)
from solana.publickey import PublicKey
from solana.rpc.types import TxOpts, MemcmpOpts, TokenAccountOpts, DataSliceOpts
from spl.token.constants import TOKEN_PROGRAM_ID, WRAPPED_SOL_MINT

class WrappedSolana:
    def __init__(self, url: str):
        self.node_url = url
        self.connection = Client(url, timeout=300)
        
    def publicKey(self, address):
        return PublicKey(address)

    def sendTransaction(self,
                        transaction,
                        signers,
                        tx_opts = None):
        if not tx_opts:
            tx_opts = self.buildTransactionOpts()
        response = self.connection.send_transaction(transaction, *signers, opts=tx_opts)
        signature = response['result']
        return signature

    def buildTransactionOpts(self,
                             skip_confirmation = True,
                             skip_preflight = False,
                             preflight_commitment = 'finalized',
                             max_retries = None):
        return TxOpts(skip_confirmation=skip_confirmation, skip_preflight=skip_preflight, preflight_commitment=preflight_commitment, max_retries=max_retries)

    def getProgramAccounts(self,
                           address,
                           commitment = 'finalized',
                           encoding = None,
                           data_slice = None,
                           data_size = None,
                           memcmp_opts = None):
        return self.connection.get_program_accounts(address,
                                                    commitment=commitment,
                                                    encoding=encoding,
                                                    data_slice=data_slice,
                                                    data_size=data_size,
                                                    memcmp_opts=memcmp_opts)['result']
    
    def getAccountInfo(self, account):
        result = self.connection.get_account_info(account)['result']
        return (result['value'], result['context']['slot'])
    
    def getAccountData(self, account):
        account_info, slot = self.getAccountInfo(account)
        return (account_info['data'], slot)
    
    def getMultipleAccounts(self, accounts):
        result = self.connection.get_multiple_accounts(accounts)['result']
        slot = result['context']['slot']
        account_infos = result['value']
        return (account_infos, slot)
    
    def getMultipleAccountsData(self, accounts):
        account_infos, slot = self.getMultipleAccounts(accounts)
        account_datas = [account_info['data'] for account_info in account_infos]
        return account_datas, slot
    
    def findProgramAddress(self, seeds, program_id):
        return PublicKey.find_program_address(seeds, self.publicKey(program_id))[0]
    
    def createProgramAddress(self, seeds, program_id):
        return PublicKey.create_program_address(seeds, program_id)
    
    def getProgramAddress(self,
                          program_id,
                          market_address,
                          seed):
        program_id = self.publicKey(program_id)
        seeds = [
            bytes(program_id),
            bytes(self.publicKey(market_address)),
            bytes(seed, 'utf8')
        ]
        return self.findProgramAddress(seeds, program_id)

