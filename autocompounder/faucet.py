from web3 import Web3
from helpers import utils
import logging
import requests
import time
import traceback


class Faucet:
    def __init__(
        self,
        private_key,
        wallet_address,
        contract_address,
        abi_file,
        max_tries,
        usd_to_compound,
        txn_timeout=120,
        gas_price=5,
        gas=500000,
        rpc_host="https://bsc-dataseed.binance.org:443"
    ):
        self.private_key = private_key
        self.wallet_address = wallet_address
        self.contract_address = contract_address
        self.abi_file = abi_file
        self.max_tries = max_tries
        self.usd_to_compound = usd_to_compound
        self.txn_timeout = txn_timeout
        self.gas_price = gas_price
        self.gas = gas
        self.rpc_host = rpc_host
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_host))
        self.contract = self.w3.eth.contract(
            self.contract_address,
            abi=utils.read_json_file(self.abi_file)
        )

    def get_user_deposits(self):
        response = None
        for i in range(self.max_tries):
            try:
                response = self.contract.functions.userInfoTotals(
                    self.wallet_address).call()
                return utils.decimal_fix_places(response[1], 18)
            except Exception:
                logging.debug(
                    "Attempt {}: {}".format(i, traceback.format_exc())
                )
                continue
        return response

    def get_user_available(self):
        response = None
        for i in range(self.max_tries):
            try:
                response = self.contract.functions.claimsAvailable(
                    self.wallet_address).call()
                return utils.decimal_fix_places(response, 18)
            except Exception:
                logging.debug(
                    "Attempt {}: {}".format(i, traceback.format_exc())
                )
                continue
        return response

    def get_drip_price(self):
        response = None
        for i in range(self.max_tries):
            try:
                response = requests.get("https://api.drip.community/prices/")
                return response.json()[-1]['value']
            except Exception:
                logging.debug(
                    "Attempt {}: {}".format(i, traceback.format_exc())
                )
                continue
        return response

    def get_usd_value(self, num_drip, price):
        return num_drip * price

    def get_faucet_batch(self, available_usd, usd_to_compound):
        return round(available_usd / usd_to_compound)

    def check_new_faucet_batch(self, ready_faucet_batch, new_faucet_batch):
        if ready_faucet_batch > new_faucet_batch:
            message = ("Ready faucet batch: {} which is greater than {}".
                       format(ready_faucet_batch, new_faucet_batch))
            logging.debug(message)
            print(message)
            return True
        else:
            message = ("Ready faucet batch: {} should be greater than {}".
                       format(ready_faucet_batch, new_faucet_batch))
            logging.debug(message)
            print(message)
            return False

    def roll_batch(self, ready_faucet_batch):
        for i in range(self.max_tries):
            try:
                txn = self.contract.functions.roll().buildTransaction(
                        {
                            "from": self.wallet_address,
                            "gasPrice": utils.eth2wei(self.gas_price, "gwei"),
                            "gas": self.gas,
                            "nonce": self.nonce()
                         }
                )
                signed_txn = self.w3.eth.account.sign_transaction(
                    txn,
                    self.private_key
                )
                txn = self.w3.eth.sendRawTransaction(signed_txn.rawTransaction)
                txn_receipt = self.w3.eth.waitForTransactionReceipt(txn)
                if txn_receipt and "status" in txn_receipt and \
                        txn_receipt["status"] == 1:
                    logging.info('Rolled faucet batch successfully!')
                    ready_faucet_batch = 0
                    break
                else:
                    logging.info('Could not roll faucet batch.')
                    logging.debug(txn_receipt)
                    time.sleep(10)
            except Exception:
                logging.debug(
                    "Attempt {}: {}".format(i, traceback.format_exc())
                )
                time.sleep(10)
        return ready_faucet_batch

    def nonce(self):
        return self.w3.eth.getTransactionCount(self.wallet_address)