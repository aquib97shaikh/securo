import { describe, expect, it } from 'vitest'
import { payeeNetAmount, summarizePayeeNets } from './payee-nets'

describe('payeeNetAmount', () => {
  it('is spent minus received', () => {
    expect(payeeNetAmount({ total_spent: 150, total_received: 30 })).toBe(120)
  })
})

describe('summarizePayeeNets', () => {
  it('splits counterparties into you-owe vs owed-to-you and nets them', () => {
    const totals = summarizePayeeNets([
      { total_spent: 1000, total_received: 50 },
      { total_spent: 200, total_received: 5000 },
      { total_spent: 0, total_received: 0 },
    ])
    expect(totals.youOwe).toBe(950)
    expect(totals.owedToYou).toBe(4800)
    expect(totals.net).toBe(-3850)
  })

  it('is zero when there are no payees', () => {
    expect(summarizePayeeNets([])).toEqual({ youOwe: 0, owedToYou: 0, net: 0 })
  })
})
