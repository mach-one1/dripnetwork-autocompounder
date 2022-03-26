from web3 import Web3
from helpers import utils
import logging
import time
import traceback


class Garden:
    def __init__(
        self,
        private_key,
        wallet_address,
        contract_address,
        abi_file,
        max_tries,
        compound_plants_grown_in_day,
        plants_to_compound,
        seed_ratio_allowed,
        ignore_seed_ratio,
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
        self.compound_plants_grown_in_day = compound_plants_grown_in_day
        self.plants_to_compound = plants_to_compound
        self.seed_ratio_allowed = seed_ratio_allowed
        self.ignore_seed_ratio = ignore_seed_ratio
        self.txn_timeout = txn_timeout
        self.gas_price = gas_price
        self.gas = gas
        self.rpc_host = rpc_host
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_host))
        self.contract = self.w3.eth.contract(
            self.contract_address,
            abi=utils.read_json_file(self.abi_file)
        )

    def get_user_seeds(self):
        response = None
        for i in range(self.max_tries):
            try:
                response = self.contract.functions.getUserSeeds(
                    self.wallet_address).call()
                return response
            except Exception:
                logging.debug(
                    "Attempt {}: {}".format(i, traceback.format_exc())
                )
                continue
        return response

    def get_my_plants(self):
        response = None
        for i in range(self.max_tries):
            try:
                response = self.contract.functions.hatcheryPlants(
                    self.wallet_address).call()
                return response
            except Exception:
                logging.debug(
                    "Attempt {}: {}".format(i, traceback.format_exc())
                )
                response = None
        return response

    def get_seeds_per_plant(self):
        try:
            self.seeds_per_plant = \
                self.contract.functions.SEEDS_TO_GROW_1PLANT().call()
        except Exception:
            self.seeds_per_plant = None
            logging.debug(traceback.format_exc())
        return self.seeds_per_plant

    def get_plants_to_compound(self, plant_count, seeds_per_plant):
        if self.compound_plants_grown_in_day:
            return int((plant_count * 86400) / seeds_per_plant)
        else:
            return self.plants_to_compound

    def get_seed_remainder(self, seed_count, seeds_per_plant):
        return seed_count % seeds_per_plant

    def get_seed_ratio(self, seed_remainder, seeds_per_plant):
        return (1 - (seed_remainder / seeds_per_plant))

    def check_new_plants(self, ready_plants, new_plants):
        if ready_plants > new_plants:
            message = ("Ready plants: {} which is greater than {}".
                       format(ready_plants, new_plants))
            logging.debug(message)
            print(message)
            return True
        else:
            message = ("Ready plants: {} should be greater than {}".format(
                    ready_plants, new_plants
            ))
            logging.debug(message)
            print(message)
            return False

    def check_seed_ratio(self, seed_ratio):
        passed = False
        if self.ignore_seed_ratio:
            passed = True
        else:
            passed = seed_ratio > self.seed_ratio_allowed
        if passed:
            logging.info("Current seeds above ratio or ratio ignored")
        else:
            message = ("Seed ratio is {}. ".format(seed_ratio) +
                       "should be above {}".format(
                        self.seed_ratio_allowed
                        )
                       )
            logging.debug(message)
            print(message)
        return passed

    def plant_seeds(self, new_plants):
        for i in range(self.max_tries):
            try:
                txn = self.contract.functions.plantSeeds(
                    self.wallet_address).buildTransaction(
                        {"gasPrice": utils.eth2wei(self.gas_price, "gwei"),
                         "gas": self.gas,
                         "nonce": self.nonce()
                         })
                signed_txn = self.w3.eth.account.sign_transaction(
                    txn,
                    self.private_key
                )
                txn = self.w3.eth.sendRawTransaction(signed_txn.rawTransaction)
                txn_receipt = self.w3.eth.waitForTransactionReceipt(txn)
                if txn_receipt and "status" in txn_receipt and \
                        txn_receipt["status"] == 1:
                    logging.info('Planted seeds successfully!')
                    new_plants = 0
                    break
                else:
                    logging.info('Could not plant seeds.')
                    logging.debug(txn_receipt)
                    time.sleep(10)
            except Exception:
                logging.debug(
                    "Attempt {}: {}".format(i, traceback.format_exc())
                )
                time.sleep(10)
        return new_plants

    def nonce(self):
        return self.w3.eth.getTransactionCount(self.wallet_address)
