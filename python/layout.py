from construct import Bytes, Padding, Int8ul, Int32ul, Int64ul, BytesInteger, Flag
from construct import Struct, BitsInteger, Const, BitsSwapped, BitStruct

LIQUIDITY_POOL_PROGRAM_ID_V4 = '675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8'
SERUM_PROGRAM_ID_V3 = '9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin'

ACCOUNT_FLAGS_LAYOUT = BitsSwapped(  # Swap to little endian
    BitStruct(
        "initialized" / Flag,
        "market" / Flag,
        "open_orders" / Flag,
        "request_queue" / Flag,
        "event_queue" / Flag,
        "bids" / Flag,
        "asks" / Flag,
        Const(0, BitsInteger(57)),  # Padding
    )
)

ACCOUNT_LAYOUT = Struct(
    "mint" / Bytes(32),
    "owner" / Bytes(32),
    "amount" / Int64ul,
    "delegateOption" / Int32ul,
    "delegate" / Bytes(32),
    "state" / Int8ul,
    "isNativeOption" / Int32ul,
    "isNative" / Int64ul,
    "delegatedAmount" / Int64ul,
    "closeAuthorityOption" / Int32ul,
    "closeAuthority" / Bytes(32)
)

TRANSFER_LAYOUT = Struct(
    "instruction" / Int8ul,
    "amount" / Int64ul
)

SWAP_LAYOUT = Struct(
    "instruction" / Int8ul,
    "amount0" / Int64ul,
    "amount1" / Int64ul
)

GET_INSTRUCTION_LAYOUT = Struct(
    "instruction" / Int8ul
)

RAYDIUM_SWAP_INSTRUCTION_IDX = 9
RAYDIUM_DEPOSIT_INSTRUCTION_IDX = 3
RAYDIUM_WITHDRAW_INSTRUCTION_IDX = 4

SWAP_INSTRUCTION_FORMAT = "<BQQ"

MARKET_STATE_LAYOUT_V2 = Struct(
    Padding(5),
    "accountFlags" / ACCOUNT_FLAGS_LAYOUT,
    "ownAddress" / Bytes(32),
    "vaultSignerNonce" / Int64ul,
    "baseMint" / Bytes(32),
    "quoteMint" / Bytes(32),
    "baseVault" / Bytes(32),
    "baseDepositsTotal" / Int64ul,
    "baseFeesAccrued" / Int64ul,
    "quoteVault" / Bytes(32),
    "quoteDepositsTotal" / Int64ul,
    "quoteFeesAccrued" / Int64ul,
    "quoteDustThreshold" / Int64ul,
    "requestQueue" / Bytes(32),
    "eventQueue" / Bytes(32),
    "bids" / Bytes(32),
    "asks" / Bytes(32),
    "baseLotSize" / Int64ul,
    "quoteLotSize" / Int64ul,
    "feeRateBps" / Int64ul,
    "referrerRebatesAccrued" / Int64ul,
    Padding(7),
)

# Serum Open Orders Book
OPEN_ORDERS_LAYOUT = Struct(
    Padding(5),
    "account_flags" / ACCOUNT_FLAGS_LAYOUT,
    "market" / Bytes(32),
    "owner" / Bytes(32),
    "base_token_free" / Int64ul,
    "base_token_total" / Int64ul,
    "quote_token_free" / Int64ul,
    "quote_token_total" / Int64ul,
    "free_slot_bits" / Bytes(16),
    "is_bid_bits" / Bytes(16),
    "orders" / BytesInteger(16)[128],
    "client_ids" / Int64ul[128],
    "referrer_rebate_accrued" / Int64ul,
    Padding(7),
)

AMM_INFO_LAYOUT_V4 = Struct(
    "status" / Int64ul,
    "nonce" / Int64ul,
    "orderNum" / Int64ul,
    "depth" / Int64ul,
    "coinDecimals" / Int64ul,
    "pcDecimals" / Int64ul,
    "state" / Int64ul,
    "resetFlag" / Int64ul,
    "minSize" / Int64ul,
    "volMaxCutRatio" / Int64ul,
    "amountWaveRatio" / Int64ul,
    "coinLotSize" / Int64ul,
    "pcLotSize" / Int64ul,
    "minPriceMultiplier" / Int64ul,
    "maxPriceMultiplier" / Int64ul,
    "systemDecimalsValue" / Int64ul,
    "minSeparateNumerator" / Int64ul,
    "minSeparateDenominator" / Int64ul,
    "tradeFeeNumerator" / Int64ul,
    "tradeFeeDenominator" / Int64ul,
    "pnlNumerator" / Int64ul,
    "pnlDenominator" / Int64ul,
    "swapFeeNumerator" / Int64ul,
    "swapFeeDenominator" / Int64ul,
    "needTakePnlCoin" / Int64ul,
    "needTakePnlPc" / Int64ul,
    "totalPnlPc" / Int64ul,
    "totalPnlCoin" / Int64ul,
    "poolTotalDepositPc" / BytesInteger(16, swapped=True), # Int128ul,
    "poolTotalDepositCoin" / BytesInteger(16, swapped=True), # Int128ul,
    "swapCoinInAmount" / BytesInteger(16, swapped=True), # Int128ul,
    "swapPcOutAmount" / BytesInteger(16, swapped=True), # Int128ul,
    "swapCoin2PcFee" / Int64ul,
    "swapPcInAmount" / BytesInteger(16, swapped=True), # Int128ul,
    "swapCoinOutAmount" / BytesInteger(16, swapped=True), # Int128ul,
    "swapPc2CoinFee" / Int64ul,
    'poolCoinTokenAccount' / Bytes(32),
    'poolPcTokenAccount' / Bytes(32),
    'coinMintAddress' / Bytes(32),
    'pcMintAddress' / Bytes(32),
    'lpMintAddress' / Bytes(32),
    'ammOpenOrders' / Bytes(32),
    'serumMarket' / Bytes(32),
    'serumProgramId' / Bytes(32),
    'ammTargetOrders' / Bytes(32),
    'poolWithdrawQueue' / Bytes(32),
    'poolTempLpTokenAccount' / Bytes(32),
    'ammOwner' / Bytes(32),
    'pnlOwner' / Bytes(32)
)

GENERAL_SWAP_LAYOUT = Struct(
    "version" / Int8ul,
    "isInitialized" / Int8ul,
    "bumpSeed" / Int8ul,
    "tokenProgramId" / Bytes(32),
    "tokenAccountA" / Bytes(32),
    "tokenAccountB" / Bytes(32),
    "tokenPool" / Bytes(32),
    "mintA" / Bytes(32),
    "mintB" / Bytes(32),
    "feeAccount" / Bytes(32),
    "tradeFeeNumerator" / Int64ul,
    "tradeFeeDenominator" / Int64ul,
    "ownerTradeFeeNumerator" / Int64ul,
    "ownerTradeFeeDenominator" / Int64ul,
    "hostFeeNumerator" / Int64ul,
    "hostFeeDenominator" / Int64ul,
    "curveType" / Int8ul,
    "curveParameters" / Bytes(32)
)

STEP_SWAP_LAYOUT = Struct(
    "version" / Int8ul,
    "isInitialized" / Int8ul,
    "bumpSeed" / Int8ul,
    "tokenProgramId" / Bytes(32),
    "tokenAccountA" / Bytes(32),
    "tokenAccountB" / Bytes(32),
    "tokenPool" / Bytes(32),
    "mintA" / Bytes(32),
    "mintB" / Bytes(32),
    "feeAccount" / Bytes(32),
    "tradeFeeNumerator" / Int64ul,
    "tradeFeeDenominator" / Int64ul,
    "ownerTradeFeeNumerator" / Int64ul,
    "ownerTradeFeeDenominator" / Int64ul,
    "curveType" / Int8ul,
    "curveParameters" / Bytes(32),
    "poolNonce" / Int8ul
)

MERCURIAL_SWAP_LAYOUT = Struct(
    "version" / Int8ul,
    "isInitialized" / Int8ul,
    "nonce" / Int8ul,
    "amplificationCoefficient" / Int64ul,
    "feeNumerator" / Int64ul,
    "adminFeeNumerator" / Int64ul,
    "tokenAccountsLength" / Int32ul,
    "precisionFactor" / Int64ul,
    "precisionMultiplierA" / Int64ul,
    "precisionMultiplierB" / Int64ul,
    "precisionMultiplierC" / Int64ul,
    "precisionMultiplierD" / Int64ul,
    "tokenAccountA" / Bytes(32),
    "tokenAccountB" / Bytes(32),
    "tokenAccountC" / Bytes(32),
    "tokenAccountD" / Bytes(32)
)

CROPPER_SWAP_LAYOUT = Struct(
    "version" / Int8ul,
    "isInitialized" / Int8ul,
    "nonce" / Int8ul,
    "ammId" / Bytes(32),
    "serumProgramId" / Bytes(32),
    "serumMarket" / Bytes(32),
    "tokenProgramId" / Bytes(32),
    "tokenAAccount" / Bytes(32),
    "tokenBAccount" / Bytes(32),
    "poolMint" / Bytes(32),
    "mintA" / Bytes(32),
    "mintB" / Bytes(32)
)

SENCHA_SWAP_LAYOUT = Struct(
    "discriminator" / Bytes(8),
    "factory" / Bytes(32),
    "bump" / Int8ul,
    "index" / Int64ul,
    "admin" / Bytes(32),
    "token0Reserves" / Bytes(32),
    "token0Mint" / Bytes(32),
    "token0Fees" / Bytes(32),
    "token1Reserves" / Bytes(32),
    "token1Mint" / Bytes(32),
    "token1Fees" / Bytes(32),
    "isPaused" / Int8ul,
    "poolMint" / Bytes(32),
    "tradeFeeKbps" / Int64ul,
    "withdrawFeeKbps" / Int64ul,
    "adminTradeFeeKbps" / Int64ul,
    "adminWithdrawFeeKbps" / Int64ul
)

FEES_LAYOUT = Struct(
    "tradeFeeNumerator" / Int64ul,
    "tradeFeeDenominator" / Int64ul,
    "ownerTradeFeeNumerator" / Int64ul,
    "ownerTradeFeeDenominator" / Int64ul,
    "ownerWithdrawFeeNumerator" / Int64ul,
    "ownerWithdrawFeeDenominator" / Int64ul,
)

ALDRIN_SWAP_LAYOUT = Struct(
    Padding(8),
    "lpTokenFreezeVault" / Bytes(32),
    "poolMint" / Bytes(32),
    "baseTokenVault" / Bytes(32),
    "baseTokenMint" / Bytes(32),
    "quoteTokenVault" / Bytes(32),
    "quoteTokenMint" / Bytes(32),
    "poolSigner" / Bytes(32),
    "poolSignerNonce" / Int8ul,
    "authority" / Bytes(32),
    "initializerAccount" / Bytes(32),
    "feeBaseAccount" / Bytes(32),
    "feeQuoteAccount" / Bytes(32),
    "feePoolTokenAccount" / Bytes(32),
    "feesLayout" / FEES_LAYOUT
)

SABER_FEES_LAYOUT = Struct(
    "adminTradeFeeNumerator" / Int64ul,
    "adminTradeFeeDenominator" / Int64ul,
    "adminWithdrawFeeNumerator" / Int64ul,
    "adminWithdrawFeeDenominator" / Int64ul,
    "tradeFeeNumerator" / Int64ul,
    "tradeFeeDenominator" / Int64ul,
    "withdrawFeeNumerator" / Int64ul,
    "withdrawFeeDenominator" / Int64ul,
)

SABER_SWAP_LAYOUT = Struct(
    "isInitialized" / Int8ul,
    "isPaused" / Int8ul,
    "nonce" / Int8ul,
    "initialAmpFactor" / Int64ul,
    "targetAmpFactor" / Int64ul,
    "startRampTs" / Int64ul,
    "stopRampTs" / Int64ul,
    "futureAdminDeadline" / Int64ul,
    "futureAdminAccount" / Bytes(32),
    "adminAccount" / Bytes(32),
    "tokenAccountA" / Bytes(32),
    "tokenAccountB" / Bytes(32),
    "tokenPool" / Bytes(32),
    "mintA" / Bytes(32),
    "mintB" / Bytes(32),
    "adminFeeAccountA" / Bytes(32),
    "adminFeeAccountB" / Bytes(32),
    "feesLayout" / SABER_FEES_LAYOUT
)

LIFINITY_SWAP_LAYOUT = Struct(
    "index" / Int64ul,
    "initializerKey" / Bytes(32),
    "initializerDepositTokenAccount" / Bytes(32),
    "initializerReceiveTokenAccount" / Bytes(32),
    "initializerAmount" / Int64ul,
    "takerAmount" / Int64ul,
    "initialized" / Int8ul,
    "bumpSeed" / Int8ul,
    "freezeTrade" / Int8ul,
    "freezeDeposit" / Int8ul,
    "freezeWithdraw" / Int8ul,
    "baseDecimals" / Int8ul,
    "tokenProgramId" / Bytes(32),
    "tokenAAccount" / Bytes(32),
    "tokenBAccount" / Bytes(32),
    "poolMint" / Bytes(32),
    "tokenAMint" / Bytes(32),
    "tokenBMint" / Bytes(32),
    "poolFeeAccount" / Bytes(32),
    "pythAccount" / Bytes(32),
    "pythPcAccount" / Bytes(32),
    "configAccount" / Bytes(32),
    "ammTemp1" / Bytes(32),
    "ammTemp2" / Bytes(32),
    "ammTemp3" / Bytes(32),
    "tradeFeeNumerator" / Int64ul,
    "tradeFeeDenominator" / Int64ul,
    "ownerTradeFeeNumerator" / Int64ul,
    "ownerTradeFeeDenominator" / Int64ul,
    "ownerWithdrawFeeNumerator" / Int64ul,
    "ownerWithdrawFeeDenominator" / Int64ul,
    "hostFeeNumerator" / Int64ul,
    "hostFeeDenominator" / Int64ul,
    "curveType" / Int8ul,
    "curveParameters" / Int64ul,
)

