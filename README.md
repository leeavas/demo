# demo

Most of the code I have written is proprietary to the trading strategies I am running and therefore cannot be shared.

## TypeScript

This is a very basic demo of one of the concepts I have explored in running arbitrage on Solana.
I use the Jupiter sdk which computes profitable routes between tokenA and tokenB with up to 1 "hop" in the middle.
For example, computing USDC-SOL routes could determine that the most profitable route for that trade is USDC->RAY->SOL.
We then explore deeper by taking the output of that best route and plugging it back in to compute the best route in the reverse direction, SOL-USDC. Thus getting anywhere from 2 to 4 legs in our overall route.
This is essentially Triangular Arbitrage.

To run the typescript bot, run the following.

```
cd typescript
npm i
ts-node src/app.ts
```

## Python

The current version of the python bot just runs queries against a typescript-hosted Jupiter instance, which is basically what is demonstrated in the typescript example. So instead I have an example of how I have wrapped and customized solana-py code to get DEX information. In this case, I am building the entire Raydium market for USDC-SOL all from data stored on-chain (rather than the hosted raydium markets url). I originally did this to be able to "snipe" new tokens the moment they would appear on Raydium, since the markets url wouldn't have the market data yet. We use this custom Raydium-py code to get a snapshot of the reserves repeatedly over time.

To run the python bot, run the following

```
cd python
pip install -r requirements.txt
python app.py
```

## Notes

This is NOT a profitable trading strategy as coded here. Account state on Solana moves extremely fast, so computing routes in a sequential and inefficient way such as this will most likely lead to missed opportunities. In my strategies, I have refactored and optimized Jupiter and I am running my queries through PostgresQL to make it significantly faster.
