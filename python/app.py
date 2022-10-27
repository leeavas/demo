from sol import WrappedSolana, WRAPPED_SOL_MINT
from raydium import RaydiumAmm

# solana = WrappedSolana("http://localhost:8899")
local = False
node_url = "http://localhost:8899" if local else "https://solana-api.projectserum.com"
solana = WrappedSolana(node_url)
usdc = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
sol = WRAPPED_SOL_MINT
print("Getting USDC-SOL market data on Raydium...")
raydium = RaydiumAmm(solana, usdc, sol)
while True:
    reserves, _, slot = raydium.getReserves()
    print("Slot {} - Reserves {}".format(slot, reserves))
