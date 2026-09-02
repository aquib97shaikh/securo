export const TROY_OUNCE_GRAMS = 31.1034768

const GOLD_OZ_TICKERS = new Set(['GC=F', 'MGC=F', 'XAUUSD=X', 'XAU=X'])
const SILVER_OZ_TICKERS = new Set(['SI=F', 'SIL=F', 'XAGUSD=X', 'XAG=X'])
const GOLD_GRAM_TICKERS = new Set(['GOLD', 'XAU'])
const SILVER_GRAM_TICKERS = new Set(['SILVER', 'XAG'])

export const GOLD_KARATS = [24, 22, 21, 18, 16, 14, 10] as const
export type GoldKarat = (typeof GOLD_KARATS)[number]
export const DEFAULT_GOLD_KARAT: GoldKarat = 24

export function isPhysicalMetalOzTicker(ticker?: string | null): boolean {
  const key = (ticker || '').trim().toUpperCase()
  return GOLD_OZ_TICKERS.has(key) || SILVER_OZ_TICKERS.has(key)
}

export function isPhysicalMetalGramTicker(ticker?: string | null): boolean {
  const key = (ticker || '').trim().toUpperCase()
  return GOLD_GRAM_TICKERS.has(key) || SILVER_GRAM_TICKERS.has(key)
}

export function isGoldTicker(ticker?: string | null): boolean {
  const key = (ticker || '').trim().toUpperCase()
  return GOLD_OZ_TICKERS.has(key) || GOLD_GRAM_TICKERS.has(key)
}

export function goldKaratFactor(karat?: number | null): number {
  if (karat == null || !(GOLD_KARATS as readonly number[]).includes(karat)) {
    return 1
  }
  return karat / DEFAULT_GOLD_KARAT
}

export function isPhysicalMetalType(type: string): boolean {
  return type === 'gold' || type === 'silver'
}

export function defaultMetalTicker(type: 'gold' | 'silver'): string {
  switch (type) {
    case 'gold':
      return 'GOLD'
    case 'silver':
      return 'SILVER'
    default: {
      const exhaustive: never = type
      return exhaustive
    }
  }
}

export function typeFromQuote(quoteType?: string | null, symbol?: string | null): string {
  const ticker = (symbol || '').trim().toUpperCase()
  if (GOLD_OZ_TICKERS.has(ticker) || GOLD_GRAM_TICKERS.has(ticker)) return 'gold'
  if (SILVER_OZ_TICKERS.has(ticker) || SILVER_GRAM_TICKERS.has(ticker)) return 'silver'
  switch ((quoteType || '').toUpperCase()) {
    case 'EQUITY':
      return 'stock'
    case 'ETF':
      return 'etf'
    case 'CRYPTOCURRENCY':
      return 'crypto'
    case 'MUTUALFUND':
    case 'INDEX':
      return 'fund'
    default:
      return 'investment'
  }
}

export function holdingUnitPrice(
  ticker: string | null | undefined,
  quotePrice: number,
  karat?: number | null,
): number {
  let unit = isPhysicalMetalOzTicker(ticker) ? quotePrice / TROY_OUNCE_GRAMS : quotePrice
  if (isGoldTicker(ticker) && karat != null) {
    unit *= goldKaratFactor(karat)
  }
  return unit
}

export function locksQuoteCurrency(type: string, valuationMethod: string): boolean {
  return valuationMethod === 'market_price' && !isPhysicalMetalType(type)
}

export function resolvedPurchaseUnitPrice(
  entered: string,
  marketPrice: number | null | undefined,
): number | null {
  const trimmed = entered.trim()
  if (trimmed) {
    const parsed = Number(trimmed)
    if (Number.isFinite(parsed) && parsed >= 0) return parsed
  }
  if (marketPrice != null && Number.isFinite(marketPrice)) return marketPrice
  return null
}
