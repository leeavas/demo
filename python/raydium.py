import base58
import base64
from decimal import Decimal
import requests
import struct
import time

from layout import (ACCOUNT_LAYOUT,
                     AMM_INFO_LAYOUT_V4,
                     GET_INSTRUCTION_LAYOUT,
                     LIQUIDITY_POOL_PROGRAM_ID_V4,
                     MARKET_STATE_LAYOUT_V2,
                     OPEN_ORDERS_LAYOUT,
                     RAYDIUM_SWAP_INSTRUCTION_IDX,
                     SWAP_INSTRUCTION_FORMAT,
                     TRANSFER_LAYOUT)
from sol import (AccountMeta,
                    ConstError,
                    Keypair,
                    MemcmpOpts,
                    PublicKey,
                    SERUM_PROGRAM_ID_V3,
                    TOKEN_PROGRAM_ID,
                    Transaction,
                    TransactionInstruction,
                    TxOpts,
                    WRAPPED_SOL_MINT,
                    WrappedSolana)

class RaydiumApi:
    def __init__(self, solana):
        self.solana = solana
        
    def getAmmAddress(self,
                      token0,
                      token1,
                      remove_deprecated = False):
        token0 = str(token0)
        token1 = str(token1)
        amm_accounts = self.getAmmProgramAccounts(token0, token1, remove_deprecated)
        token0_base = True
        if len(amm_accounts) == 0:
            amm_accounts = self.getAmmProgramAccounts(token1, token0, remove_deprecated)
            token0_base = False
        if len(amm_accounts) == 0:
            raise ValueError("Pair of tokens {} and {} has no amm market".format(token0, token1))
        elif len(amm_accounts) > 1:
            max_value = 0
            for address, value in amm_accounts.items():
                if value > max_value:
                    amm_address = address
                    max_value = value
        else:
            amm_address = list(amm_accounts.keys())[0]
        return (amm_address, token0_base)
        
    def getMarketAddress(self,
                         token0,
                         token1,
                         remove_deprecated):
        token0 = str(token0)
        token1 = str(token1)
        market_accounts = self.getMarketProgramAccounts(token0, token1, remove_deprecated)
        token0_base = True
        if len(market_accounts) == 0:
            market_accounts = self.getMarketProgramAccounts(token1, token0, remove_deprecated)
            token0_base = False
        if len(market_accounts) == 0:
            raise ValueError("Pair of tokens {} and {} has no serum market".format(token0, token1))
        elif len(market_accounts) > 1:
            max_value = 0
            for address, value in market_accounts.items():
                if value > max_value:
                    market_address = address
                    max_value = value
        else:
            market_address = list(market_accounts.keys())[0]
        return (market_address, token0_base)
        
    def getAmmProgramAccounts(self,
                              base,
                              quote,
                              remove_deprecated):
        memcmp_opts = [
            MemcmpOpts(offset=400, bytes=base),
            MemcmpOpts(offset=432, bytes=quote)
        ]
        accounts = self.solana.getProgramAccounts(LIQUIDITY_POOL_PROGRAM_ID_V4, 
                                                  memcmp_opts=memcmp_opts, 
                                                  encoding='base64')
        amm_accounts = {}
        if accounts:
            for acc in accounts:
                try:
                    parsed_acc = AMM_INFO_LAYOUT_V4.parse(base64.b64decode(acc['account']['data'][0]))
                except ConstError:
                    continue
                if remove_deprecated:
                    if parsed_acc['swapCoinInAmount'] > 0 and parsed_acc['swapPcOutAmount'] > 0:
                        amm_accounts[acc['pubkey']] = parsed_acc['swapCoinInAmount'] + parsed_acc['swapPcOutAmount']
                else:
                    amm_accounts[acc['pubkey']] = parsed_acc['swapCoinInAmount'] + parsed_acc['swapPcOutAmount']
        return amm_accounts
    
    def getMarketProgramAccounts(self,
                                 base,
                                 quote,
                                 remove_deprecated):
        memcmp_opts = [
            MemcmpOpts(53, base),
            MemcmpOpts(85, quote)
        ]
        accounts = self.solana.getProgramAccounts(SERUM_PROGRAM_ID_V3, 
                                                  memcmp_opts=memcmp_opts, 
                                                  encoding='base64')
        market_accounts = {}
        for acc in accounts:
            try:
                parsed_acc = MARKET_STATE_LAYOUT_V2.parse(base64.b64decode(acc['account']['data'][0]))
            except ConstError:
                continue
            if remove_deprecated:
                if parsed_acc['baseDepositsTotal'] > 0 and parsed_acc['quoteDepositsTotal'] > 0:
                    market_accounts[acc['pubkey']] = parsed_acc['baseDepositsTotal'] + parsed_acc['quoteDepositsTotal']
            else:
                market_accounts[acc['pubkey']] = parsed_acc['baseDepositsTotal'] + parsed_acc['quoteDepositsTotal']
        return market_accounts
    
    def getPoolInfo(self,
                    amm_address,
                    market_address,
                    base,
                    quote):
        base = str(base)
        quote = str(quote)
        info_id = self.solana.publicKey(LIQUIDITY_POOL_PROGRAM_ID_V4)
        (d, encoding), _ = self.solana.getAccountData(amm_address)
        self.verifyEncoding(amm_address, encoding)
        parsed_amm = AMM_INFO_LAYOUT_V4.parse(base64.b64decode(d))

        amm_authority = self.solana.findProgramAddress([bytes('amm authority', 'utf8')], info_id)
        pool_coin_token_account = self.solana.publicKey(parsed_amm['poolCoinTokenAccount'])
        pool_pc_token_account = self.solana.publicKey(parsed_amm['poolPcTokenAccount'])
        lp_mint_address = self.solana.publicKey(parsed_amm['lpMintAddress'])
        pool_temp_lp_token_account = self.solana.publicKey(parsed_amm['poolTempLpTokenAccount'])
        amm_target_orders = self.solana.publicKey(parsed_amm['ammTargetOrders'])
        pool_withdraw_queue = self.solana.publicKey(parsed_amm['poolWithdrawQueue'])
        amm_open_orders = self.solana.publicKey(parsed_amm['ammOpenOrders'])
        
        market_info_id = self.solana.publicKey(SERUM_PROGRAM_ID_V3)
        (d, encoding), _ = self.solana.getAccountData(market_address)
        self.verifyEncoding(market_address, encoding)
        parsed_market = MARKET_STATE_LAYOUT_V2.parse(base64.b64decode(d))
        
        market_amm_id = self.solana.getProgramAddress(market_info_id,
                                                        market_address,
                                                        'AMM_ASSOCIATED_SEED'.lower())
        market_pool_coin_token_account = self.solana.getProgramAddress(market_info_id,
                                                                        market_address,
                                                                        'COIN_VAULT_ASSOCIATED_SEED'.lower())
        market_pool_pc_token_account = self.solana.getProgramAddress(market_info_id,
                                                                        market_address,
                                                                        'PC_VAULT_ASSOCIATED_SEED'.lower())
        market_lp_mint_address = self.solana.getProgramAddress(market_info_id,
                                                                market_address,
                                                                'LP_MINT_ASSOCIATED_SEED'.lower())
        market_pool_temp_lp_token_account = self.solana.getProgramAddress(market_info_id,
                                                                            market_address,
                                                                            'TEMP_LP_TOKEN_ASSOCIATED_SEED'.lower())
        market_amm_target_orders = self.solana.getProgramAddress(market_info_id,
                                                                    market_address,
                                                                    'TARGET_ASSOCIATED_SEED'.lower())
        market_pool_withdraw_queue = self.solana.getProgramAddress(market_info_id,
                                                                    market_address,
                                                                    'WITHDRAW_ASSOCIATED_SEED'.lower())
        market_amm_open_orders = self.solana.getProgramAddress(market_info_id,
                                                                market_address,
                                                                'OPEN_ORDER_ASSOCIATED_SEED'.lower())
        market_vault_signer = self.solana.createProgramAddress(
            [bytes(PublicKey(market_address)),
                parsed_market['vaultSignerNonce'].to_bytes(8, byteorder="little")],
            market_info_id,
        )

        pool_info = {}
        pool_info["id"] = amm_address
        pool_info["baseMint"] = base
        pool_info["quoteMint"] = quote
        pool_info["lpMint"] = lp_mint_address
        pool_info["version"] = 4
        pool_info["programId"] = LIQUIDITY_POOL_PROGRAM_ID_V4
        pool_info["authority"] = amm_authority
        pool_info["openOrders"] = amm_open_orders
        pool_info["targetOrders"] = amm_target_orders
        pool_info["baseVault"] = pool_coin_token_account
        pool_info["quoteVault"] = pool_pc_token_account
        pool_info["withdrawQueue"] = pool_withdraw_queue
        pool_info["lpVault"] = pool_temp_lp_token_account
        pool_info["marketVersion"] = 3
        pool_info["marketProgramId"] = SERUM_PROGRAM_ID_V3
        pool_info["marketId"] = market_address
        pool_info["marketAuthority"] = market_vault_signer
        pool_info["marketBaseVault"] = str(PublicKey(parsed_market['baseVault']))
        pool_info["marketQuoteVault"] = str(PublicKey(parsed_market['quoteVault']))
        pool_info["marketBids"] = str(PublicKey(parsed_market['bids']))
        pool_info["marketAsks"] = str(PublicKey(parsed_market['asks']))
        pool_info["marketEventQueue"] = str(PublicKey(parsed_market['eventQueue']))
        return pool_info
    
    def verifyEncoding(self, address, encoding):
        if encoding != 'base64':
            raise ValueError("Account data for {} is not base64 encoded. It is {}".format(address, encoding))
            
    def getSwapAccounts(self, pool_id):
        (d, encoding), pool_slot = self.solana.getAccountData(pool_id)
        self.verifyEncoding(pool_id, encoding)
        swap_data = AMM_INFO_LAYOUT_V4.parse(base64.b64decode(d))
        pool_coin_token_account = self.solana.publicKey(swap_data['poolCoinTokenAccount'])
        pool_pc_token_account = self.solana.publicKey(swap_data['poolPcTokenAccount'])
        amm_open_orders_account = self.solana.publicKey(swap_data['ammOpenOrders'])
        return (pool_coin_token_account, pool_pc_token_account, amm_open_orders_account)
            
    def getReserves(self,
                    pool_id,
                    pool_coin_token_account,
                    pool_pc_token_account,
                    amm_open_orders_account):
        account_datas, slot = self.solana.getMultipleAccountsData([pool_id,
                                                                   pool_coin_token_account,
                                                                   pool_pc_token_account,
                                                                   amm_open_orders_account])
        self.verifyEncoding(pool_id, account_datas[0][1])
        swap_data = AMM_INFO_LAYOUT_V4.parse(base64.b64decode(account_datas[0][0]))
        self.verifyEncoding(pool_coin_token_account, account_datas[1][1])
        pool_coin = ACCOUNT_LAYOUT.parse(base64.b64decode(account_datas[1][0]))['amount']
        self.verifyEncoding(pool_pc_token_account, account_datas[2][1])
        pool_pc = ACCOUNT_LAYOUT.parse(base64.b64decode(account_datas[2][0]))['amount']
        self.verifyEncoding(amm_open_orders_account, account_datas[3][1])
        parsed_orders = OPEN_ORDERS_LAYOUT.parse(base64.b64decode(account_datas[3][0]))
                
        total_coin = pool_coin + parsed_orders['base_token_total'] - swap_data['needTakePnlCoin']
        total_pc = pool_pc + parsed_orders['quote_token_total'] - swap_data['needTakePnlPc']
        fees = (Decimal(swap_data['swapFeeDenominator']), Decimal(swap_data['swapFeeNumerator']))
        return ([total_pc, total_coin], fees, slot)
    
    def getAmountOut(self,
                     amount_in,
                     side,
                     pool_info,
                     reserves = None,
                     fees = None,
                     slot = None):
        if not reserves or not fees or not slot:
            reserves, fees, slot = self.getReserves(pool_info)
        swapFeeDenominator, swapFeeNumerator = fees
        amount_in_with_fee = amount_in * ((swapFeeDenominator - swapFeeNumerator) / swapFeeDenominator)
        if side == 'buy':
            in_token_pool_amount = reserves[0]
            out_token_pool_amount = reserves[1]
        else:
            in_token_pool_amount = reserves[1]
            out_token_pool_amount = reserves[0]
        denominator = in_token_pool_amount + amount_in_with_fee
        amount_out = out_token_pool_amount * (amount_in_with_fee / denominator)
        return (int(amount_out), slot)
    
    def swap(self,
             amount_in,
             min_amount_out,
             pool_info,
             from_token_account,
             to_token_account,
             keypair,
             transaction = None,
             tx_opts = None,
             send_transaction = True):
        if transaction is None:
            transaction = Transaction()
        swap_instruction = self.swapInstruction(self.solana.publicKey(pool_info["programId"]),
                                                self.solana.publicKey(pool_info["id"]),
                                                self.solana.publicKey(pool_info["authority"]),
                                                self.solana.publicKey(pool_info["openOrders"]),
                                                self.solana.publicKey(pool_info["targetOrders"]),
                                                self.solana.publicKey(pool_info["baseVault"]),
                                                self.solana.publicKey(pool_info["quoteVault"]),
                                                self.solana.publicKey(pool_info["marketProgramId"]),
                                                self.solana.publicKey(pool_info["marketId"]),
                                                self.solana.publicKey(pool_info["marketBids"]),
                                                self.solana.publicKey(pool_info["marketAsks"]),
                                                self.solana.publicKey(pool_info["marketEventQueue"]),
                                                self.solana.publicKey(pool_info["marketBaseVault"]),
                                                self.solana.publicKey(pool_info["marketQuoteVault"]),
                                                self.solana.publicKey(pool_info["marketAuthority"]),
                                                self.solana.publicKey(from_token_account),
                                                self.solana.publicKey(to_token_account),
                                                keypair.public_key,
                                                amount_in,
                                                min_amount_out)
        transaction.add(swap_instruction)
        if send_transaction:
            return self.solana.sendTransaction(transaction, [keypair], tx_opts)
        else:
            return transaction
        
    def swapInstruction(self,
                        program_id,
                        amm_id,
                        amm_authority,
                        amm_open_orders,
                        amm_target_orders,
                        pool_coin_token_account,
                        pool_pc_token_account,
                        serum_program_id,
                        serum_market,
                        serum_bids,
                        serum_asks,
                        serum_event_queue,
                        serum_coin_vault_account,
                        serum_pc_vault_account,
                        serum_vault_signer,
                        user_source_token_account,
                        user_dest_token_account,
                        user_owner,
                        amount_in,
                        min_amount_out):
        keys = [
            AccountMeta(TOKEN_PROGRAM_ID, False, False),
            AccountMeta(amm_id, False, True),
            AccountMeta(amm_authority, False, False),
            AccountMeta(amm_open_orders, False, True),
            AccountMeta(amm_target_orders, False, True),
            AccountMeta(pool_coin_token_account, False, True),
            AccountMeta(pool_pc_token_account, False, True),
            AccountMeta(serum_program_id, False, False),
            AccountMeta(serum_market, False, True),
            AccountMeta(serum_bids, False, True),
            AccountMeta(serum_asks, False, True),
            AccountMeta(serum_event_queue, False, True),
            AccountMeta(serum_coin_vault_account, False, True),
            AccountMeta(serum_pc_vault_account, False, True),
            AccountMeta(serum_vault_signer, False, False),
            AccountMeta(user_source_token_account, False, True),
            AccountMeta(user_dest_token_account, False, True),
            AccountMeta(user_owner, True, False)
        ]
        data = struct.pack(SWAP_INSTRUCTION_FORMAT, RAYDIUM_SWAP_INSTRUCTION_IDX, amount_in, min_amount_out)
        return TransactionInstruction(keys, program_id, data)

class RaydiumAmm(RaydiumApi):
    def __init__(self,
                 solana,
                 token0,
                 token1,
                 remove_deprecated = False):
        RaydiumApi.__init__(self, solana)
        amm_address, token0_base = self.getAmmAddress(self.solana.publicKey(token0), self.solana.publicKey(token1), remove_deprecated)
        self.amm_address = self.solana.publicKey(amm_address)
        market_address, token0_base = self.getMarketAddress(token0, token1, remove_deprecated)
        self.market_address = self.solana.publicKey(market_address)
        if token0_base:
            self.base = self.solana.publicKey(token0)
            self.quote = self.solana.publicKey(token1)
        else:
            self.base = self.solana.publicKey(token1)
            self.quote = self.solana.publicKey(token0)
        self.pool_info = self.getPoolInfo(self.amm_address, self.market_address, self.base, self.quote)
        (self.pool_coin_token_account,
        self.pool_pc_token_account,
        self.amm_open_orders_account) = self.getSwapAccounts(self.pool_info["id"])
        self.name = "Raydium"
        
    def getReserves(self):
        return super().getReserves(self.pool_info["id"],
                                   self.pool_coin_token_account,
                                   self.pool_pc_token_account,
                                   self.amm_open_orders_account)
    
    def getAmountOut(self, amount_in, side):
        reserves, fees, slot = self.getReserves()
        return super().getAmountOut(amount_in, side, self.pool_info, reserves, fees, slot)
    
    def swap(self,
             amount_in,
             min_amount_out,
             from_token_account,
             to_token_account,
             keypair,
             transaction = None,
             tx_opts = None,
             send_transaction = True):
        return super().swap(amount_in,
                            min_amount_out,
                            self.pool_info,
                            from_token_account,
                            to_token_account,
                            keypair,
                            transaction,
                            tx_opts,
                            send_transaction)

        