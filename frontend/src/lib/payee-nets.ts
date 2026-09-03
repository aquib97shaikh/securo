export function payeeNetAmount(payee: {
  total_spent: number
  total_received: number
}): number {
  return Number(payee.total_spent) - Number(payee.total_received)
}

export function summarizePayeeNets(
  payees: { total_spent: number; total_received: number }[],
): { youOwe: number; owedToYou: number; net: number } {
  let youOwe = 0
  let owedToYou = 0
  for (const payee of payees) {
    const net = payeeNetAmount(payee)
    if (net > 0) youOwe += net
    else if (net < 0) owedToYou += -net
  }
  return { youOwe, owedToYou, net: youOwe - owedToYou }
}
