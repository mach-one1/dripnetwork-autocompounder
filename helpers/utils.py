from web3 import Web3
import logging


def get_log_level(log_level):
    return getattr(logging, log_level.upper(), 20)


def read_json_file(filepath):
    try:
        with open(filepath) as fp:
            results = fp.read()
    except Exception:
        logging.info('Error reading json file.')
        results = None
    return results


def eth2wei(eth, unit="ether"):
    return Web3.toWei(eth, unit)


def decimal_fix_places(decimal_number, decimals):
    return decimal_number / (10 ** decimals)
