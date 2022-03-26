# dripnetwork-autocompounder

Autocompounder for products on the drip network:
* [animal farm drip garden](https://theanimal.farm/garden)
* [drip community faucet](https://drip.community/faucet)

## Setup

You will need to install `python3` to run this once this is done install the requirements:

    pip3 install -r requirements.txt

To run this program you will need to pass in your metamask wallet address and private key. Prior to running you should check that the default values in config.ini are correct for what you want to compound.

## Securing your private key

* If running this locally you could use [sops](https://github.com/mozilla/sops) to pass through `PRIVATE_KEY` as an environment variable
  * Download [sops](https://github.com/mozilla/sops)
  * Download something to encrypt this with e.g. [age](https://github.com/FiloSottile/age)
  * Generate key `age-keygen -o key.txt`
  * Move file to correct location for sops
  * Create a file ending .env with the following text.
  ```
  PRIVATE_KEY=<your-private-key>
  ```
  * Other environment variables can be added to the file if desired
  * Encrypt the file
  ```
  sops --encrypt --age <age-public-key> .env > enc.env
  ```
  * Decrypt this at runtime
  ```
  sops exec-env enc.env 'python3 main.py <flags>'
  ```
* If running this via a cloud service you could use inbuilt secrets provide the environment variable to the script

## Running

    python3 main.py
    usage: main.py [-h] [-w WALLET_ADDRESS] [-k PRIVATE_KEY] [-g] [-f]

    Drip Network Autocompounder

    optional arguments:
      -h, --help            show this help message and exit
      -w WALLET_ADDRESS, --wallet-address WALLET_ADDRESS
                            Your wallet address. Can use env var WALLET_ADDRESS
      -k PRIVATE_KEY, --private-key PRIVATE_KEY
                            Your private key. Can use env var PRIVATE_KEY
      -g, --garden          Autocompound drip garden. Can use env var COMPOUND_GARDEN
      -f, --faucet          Autocompound drip faucet. Can use env var COMPOUND_FAUCET

You can compound as many areas of the drip network as you want, by passing in the flags or relevant environment variables. The program will run in a loop and check each area to see if they are ready to compound. It attempts to avoid repeated failed compounds to minimize on redundant gas fees.

### Configuring

The [config_global.ini](config_global.ini) has the config you require to run the compounder. You may wish to override some of this config, which you could do by copying `config_global.ini` to `config_user.ini` and changing values there.

### Garden

The [drip garden](https://theanimal.farm/garden) on animal farm is a high risk, high reward game that produces up to 3% daily (1095% APR). The harvest efficiency rate rises and falls as you and other animals buy PLANTS, harvest SEEDS and compound earnings. The more plants you have the more seeds your garden produces and the quicker you create more plants. Each plant needs a certain number of seeds and you should ensure you are not wasting these seeds and compound or claim as close to losing 0 seeds as you can. This compounder will help you achieve that. The compounder will check for ready plants and compound them at the right time, with minimal seed wastage.

### Faucet

The [drip faucet](https://drip.community/faucet) on drip community is a low risk, high reward game that produces a consistent 1% daily return up to a 365% maximum payout. You can compound earnings via regular deposits and compounding rewards. The more that is compounded the larger the daily reward and maximum payout will be. This compounder will check the available dollar amount exceeds the amount to compound. Unlike the garden though, there is no effect doing this with a larger amount.