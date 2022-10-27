import { Jupiter, RouteInfo } from "@jup-ag/core";
import { Connection, PublicKey } from "@solana/web3.js";
import JSBI from "jsbi";

// Multiple groups of tokens are used when multithreading
function getTokenGroups(numGroups: number, jupiter: Jupiter, quoteMint: string): Map<number, string[]> {
    const orderedTokenRouteSegments: any[][] = [];
    jupiter.tokenRouteSegments.forEach((routeSegments, mint) => {
        if (mint == quoteMint) return;
        orderedTokenRouteSegments.push([routeSegments.size, mint]);
    })
    orderedTokenRouteSegments.sort((a, b) => {
        if (a[0] === b[0]) {
            return 0;
        }
        else {
            return (a[0] > b[0]) ? -1 : 1;
        }
    });
    
    const tokenGroups = new Map();
    const groupSizes: number[] = new Array(numGroups).fill(0);
    orderedTokenRouteSegments.forEach(mint => {
        const group = groupSizes.indexOf(Math.min(...groupSizes));
        const tokenList = tokenGroups.get(group);
        if (tokenList) {
            tokenList.push(mint[1]);
        } else {
            tokenGroups.set(group, [mint[1]]);
        }
        groupSizes[group] += mint[0];
    })
    return tokenGroups;
}

async function main() {
    const localNode = false;
    const nodeUrl = localNode ? "http://localhost:8899/" : "https://solana-api.projectserum.com"//"https://api.mainnet-beta.solana.com"
    const commitment = "confirmed";
    const connection = new Connection(nodeUrl, commitment);
    const inputAmount = JSBI.BigInt('10000000'); // 10 USDC
    Jupiter.load({
        connection: connection,
        cluster: "mainnet-beta"
    }).then(async jupiter => {
        const usdcMint = new PublicKey("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v");
        const tokenGroups = getTokenGroups(1, jupiter, usdcMint.toBase58());
        const tokenList = tokenGroups.get(0);
        const usdcDecimals = 1000000;
        if (!tokenList) throw Error(); // This won't happen
        for (let token of tokenList) {
            console.log(`Computing routes for ${token}`);
            const outMint = new PublicKey(token);
            const routesInfos: RouteInfo[] | void = await jupiter.computeRoutes({
                inputMint: usdcMint,
                outputMint: outMint,
                amount: inputAmount,
                slippageBps: 10 // 0.1% slippage
            }).then(route => {
                return route.routesInfos;
            }).catch(error => {
                // console.error(error);
            });
            if (routesInfos) {
                if (routesInfos[0]) {
                    // Index 0 is the route with the best price at this input amount
                    const midRouteAmount = routesInfos[0].outAmount;
                    const returnRoutesInfos: RouteInfo[] | void = await jupiter.computeRoutes({
                        inputMint: outMint,
                        outputMint: usdcMint,
                        amount: midRouteAmount,
                        slippageBps: 10 // 0.1% slippage
                    }).then(route => {
                        return route.routesInfos;
                    }).catch(error => {
                        // console.error(error);
                    });
                    if (returnRoutesInfos) {
                        if (returnRoutesInfos[0]) {
                            // Index 0 is the route with the best price at this input amount
                            const outAmount = returnRoutesInfos[0].outAmount;
                            if (JSBI.GT(outAmount, inputAmount)) {
                                console.log(`PROFIT! Amount: ${JSBI.toNumber(JSBI.subtract(outAmount, inputAmount)) / usdcDecimals}`);
                            }
                        }
                    }
                }
            }
        }
    })
}

main();