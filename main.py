from autocompounder import Garden, Faucet
from helpers import utils
import argparse
import configparser
import json
import logging
import os
import time
import traceback


def get_faucet_data(faucet):
    try:
        deposits = faucet.get_user_deposits()
        available = faucet.get_user_available()
        price = faucet.get_drip_price()
        deposits_usd = faucet.get_usd_value(deposits, price)
        available_usd = faucet.get_usd_value(available, price)
        return {
            'deposits': deposits,
            'available': available,
            'price': price,
            'deposits_usd': deposits_usd,
            'available_usd': available_usd,
            'usd_to_compound': faucet.usd_to_compound
        }
    except Exception:
        logging.debug(traceback.format_exc())
    return {}


def handle_faucet(faucet, new_faucet_batch):
    faucet_data = get_faucet_data(faucet)
    message = json.dumps({'faucet': faucet_data}, indent=4)
    logging.debug(message)
    print(message)
    available_usd = faucet_data.get('available_usd')
    usd_to_compound = faucet_data.get('usd_to_compound')
    if available_usd >= usd_to_compound:
        ready_faucet_batch = faucet.get_faucet_batch(
            available_usd, usd_to_compound
        )
        if faucet.check_new_faucet_batch(
            ready_faucet_batch, new_faucet_batch
        ):
            new_faucet_batch = ready_faucet_batch
            new_faucet_batch = faucet.roll_batch(ready_faucet_batch)
    return new_faucet_batch


def get_garden_data(garden):
    try:
        seed_count = garden.get_user_seeds()
        plant_count = garden.get_my_plants()
        seeds_per_plant = garden.get_seeds_per_plant()
        if seed_count >= seeds_per_plant:
            ready_plants = seed_count // seeds_per_plant
        else:
            ready_plants = 0
        plants_to_compound = garden.get_plants_to_compound(
            plant_count, seeds_per_plant
        )
        seed_remainder = garden.get_seed_remainder(seed_count, seeds_per_plant)
        seed_ratio = garden.get_seed_ratio(seed_remainder, seeds_per_plant)
        return {
            'seeds': seed_count,
            'plants': plant_count,
            'ready_plants': ready_plants,
            'plants_to_compound': plants_to_compound,
            'seeds_per_plant': seeds_per_plant,
            'seed_remainder': seed_remainder,
            'seed_ratio': seed_ratio,
        }
    except Exception:
        logging.debug(traceback.format_exc())
    return {}


def handle_garden(garden, new_plants):
    garden_data = get_garden_data(garden)
    message = json.dumps({'garden': garden_data}, indent=4)
    logging.debug(message)
    print(message)
    ready_plants = garden_data.get('ready_plants', 0)
    plants_to_compound = garden_data.get('plants_to_compound', 0)
    seed_ratio = garden_data.get('seed_ratio', 0)
    if ready_plants >= plants_to_compound:
        if garden.check_new_plants(ready_plants, new_plants) and \
                garden.check_seed_ratio(seed_ratio):
            new_plants = ready_plants
            new_plants = garden.plant_seeds(ready_plants)
    return new_plants


def main(args, config):

    garden = Garden(
        args.private_key,
        args.wallet_address,
        config["garden"]["contract_address"],
        "./abis/Garden.json",
        config.getint('default', 'max_tries'),
        config.getboolean('garden', 'compound_plants_grown_in_day'),
        config.getint('garden', 'plants_to_compound'),
        config.getfloat('garden', 'seed_ratio_allowed'),
        config.getboolean('garden', 'ignore_seed_ratio')
    )

    faucet = Faucet(
        args.private_key,
        args.wallet_address,
        config["faucet"]["contract_address"],
        "./abis/Faucet.json",
        config.getint('default', 'max_tries'),
        config.getfloat('faucet', 'usd_to_compound'),
    )

    new_plants = 0
    new_faucet_batch = 0
    while True and (args.compound_garden or args.compound_faucet):
        if args.compound_garden:
            new_plants = handle_garden(garden, new_plants)
        if args.compound_faucet:
            new_faucet_batch = handle_faucet(faucet, new_faucet_batch)
        time.sleep(5)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Drip Network Autocompounder')
    parser.add_argument(
        "-w", "--wallet-address",
        help="Your wallet address. Can use env var WALLET_ADDRESS",
        type=str, dest='wallet_address',
        default=os.environ.get('WALLET_ADDRESS')
    )
    parser.add_argument(
        "-k", "--private-key",
        help="Your private key. Can use env var PRIVATE_KEY",
        type=str, dest='private_key',
        default=os.environ.get('PRIVATE_KEY')
    )
    parser.add_argument(
        "-g", "--garden",
        help="Autocompound drip garden. Can use env var COMPOUND_GARDEN",
        action='store_true', dest='compound_garden',
        default=os.environ.get('COMPOUND_GARDEN')
    )
    parser.add_argument(
        "-f", "--faucet",
        help="Autocompound drip faucet. Can use env var COMPOUND_FAUCET",
        action='store_true', dest='compound_faucet',
        default=os.environ.get('COMPOUND_FAUCET')
    )
    args = parser.parse_args()
    if not (args.wallet_address and args.private_key):
        exit(parser.print_help())

    config = configparser.ConfigParser()
    config.read(['config_global.ini', 'config_user.ini'])

    logging.basicConfig(
        level=utils.get_log_level(config.get('default', 'log_level')),
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("autocompounder.log"),
            logging.StreamHandler()
        ]
    )

    config = configparser.ConfigParser()
    config.read(['config_global.ini', 'config_user.ini'])

    main(args, config)
