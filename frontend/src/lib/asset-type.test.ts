import { describe, expect, it } from 'vitest'
import {
  TROY_OUNCE_GRAMS,
  defaultMetalTicker,
  holdingUnitPrice,
  isPhysicalMetalType,
  locksQuoteCurrency,
  resolvedPurchaseUnitPrice,
  typeFromQuote,
} from './asset-type'

describe('typeFromQuote', () => {
  it('maps COMEX gold futures to gold', () => {
    expect(typeFromQuote('FUTURE', 'GC=F')).toBe('gold')
  })

  it('maps COMEX silver futures to silver', () => {
    expect(typeFromQuote('FUTURE', 'SI=F')).toBe('silver')
  })

  it('maps metal spot symbols by ticker', () => {
    expect(typeFromQuote('CURRENCY', 'XAUUSD=X')).toBe('gold')
    expect(typeFromQuote('CURRENCY', 'XAGUSD=X')).toBe('silver')
  })

  it('maps GoldPriceZ spot symbols to gold and silver', () => {
    expect(typeFromQuote('METAL', 'GOLD')).toBe('gold')
    expect(typeFromQuote('METAL', 'SILVER')).toBe('silver')
  })

  it('leaves unrelated futures as investment', () => {
    expect(typeFromQuote('FUTURE', 'CL=F')).toBe('investment')
  })

  it('keeps equity and ETF mappings', () => {
    expect(typeFromQuote('EQUITY', 'AAPL')).toBe('stock')
    expect(typeFromQuote('ETF', 'GLD')).toBe('etf')
  })
})

describe('holdingUnitPrice', () => {
  it('converts a troy-ounce gold quote into a per-gram price', () => {
    expect(holdingUnitPrice('GC=F', Number(TROY_OUNCE_GRAMS) * 100)).toBeCloseTo(100, 8)
  })

  it('leaves goldpricez gram quotes unchanged', () => {
    expect(holdingUnitPrice('GOLD', 7080)).toBe(7080)
  })

  it('scales gold by karat', () => {
    expect(holdingUnitPrice('GOLD', 2400, 24)).toBe(2400)
    expect(holdingUnitPrice('GOLD', 2400, 22)).toBe(2200)
    expect(holdingUnitPrice('GOLD', 2400, 18)).toBe(1800)
  })

  it('does not scale silver by gold karat', () => {
    expect(holdingUnitPrice('SILVER', 100, 22)).toBe(100)
  })
})

describe('defaultMetalTicker', () => {
  it('uses GoldPriceZ spot symbols for physical metal', () => {
    expect(defaultMetalTicker('gold')).toBe('GOLD')
    expect(defaultMetalTicker('silver')).toBe('SILVER')
  })
})

describe('isPhysicalMetalType', () => {
  it('is true only for gold and silver', () => {
    expect(isPhysicalMetalType('gold')).toBe(true)
    expect(isPhysicalMetalType('silver')).toBe(true)
    expect(isPhysicalMetalType('valuable')).toBe(false)
  })
})

describe('locksQuoteCurrency', () => {
  it('locks stocks to the quote currency', () => {
    expect(locksQuoteCurrency('stock', 'market_price')).toBe(true)
  })

  it('lets gold and silver pick a holding currency', () => {
    expect(locksQuoteCurrency('gold', 'market_price')).toBe(false)
    expect(locksQuoteCurrency('silver', 'market_price')).toBe(false)
  })
})

describe('resolvedPurchaseUnitPrice', () => {
  it('uses the entered purchase price when the user typed one', () => {
    expect(resolvedPurchaseUnitPrice('6500', 13624.52)).toBe(6500)
  })

  it('falls back to market price when purchase price is skipped', () => {
    expect(resolvedPurchaseUnitPrice('', 13624.52)).toBe(13624.52)
    expect(resolvedPurchaseUnitPrice('  ', 13624.52)).toBe(13624.52)
  })

  it('returns null when both purchase price and market are missing', () => {
    expect(resolvedPurchaseUnitPrice('', null)).toBeNull()
  })
})
