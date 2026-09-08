import { describe, expect, it } from 'vitest'

import {
  formatCompactCurrency,
  formatCompactNumber,
  formatCurrency,
  resolveDateOrder,
  resolveDisplayLocale,
} from './format'

describe('resolveDisplayLocale', () => {
  it('maps the indian number format to en-IN', () => {
    expect(resolveDisplayLocale('indian', 'USD', 'en-US')).toBe('en-IN')
  })
})

describe('resolveDateOrder', () => {
  it('uses day-first dates when the number format is indian', () => {
    expect(resolveDateOrder('auto', 'indian', 'USD')).toBe('dmy')
  })
})

describe('formatCurrency', () => {
  it('groups a lakh-scale amount with Indian commas', () => {
    expect(formatCurrency(1234567.89, 'INR', 'en-IN')).toContain('12,34,567.89')
  })
})

describe('formatCompactCurrency', () => {
  it('abbreviates one lakh as L', () => {
    expect(formatCompactCurrency(100000, 'INR', 'en-IN')).toMatch(/1\s*L/)
  })

  it('abbreviates one crore as Cr', () => {
    expect(formatCompactCurrency(10000000, 'INR', 'en-IN')).toMatch(/1\s*Cr/)
  })
})

describe('formatCompactNumber', () => {
  it('abbreviates one lakh as L without a currency symbol', () => {
    expect(formatCompactNumber(100000, 'en-IN')).toMatch(/1\s*L/)
  })
})
