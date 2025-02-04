from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins

def generate_tron_private_key(mnemonic_phrase):
    try:
        seed = Bip39SeedGenerator(mnemonic_phrase).Generate()
        bip44_tron_wallet = Bip44.FromSeed(seed, Bip44Coins.TRON).DeriveDefaultPath()
        private_key = bip44_tron_wallet.PrivateKey().Raw().ToHex()
        return private_key
    except:
        return False