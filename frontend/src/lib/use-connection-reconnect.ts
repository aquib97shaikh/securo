import { useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { toast } from 'sonner'
import { connections } from '@/lib/api'

export const OAUTH_RETURN_TO_KEY = 'securo:oauth-return-to'

export function connectionNeedsReconnect(status: string): boolean {
  return status === 'error' || status === 'expired'
}

export function readOAuthReturnTo(fallback = '/accounts'): string {
  const stored = sessionStorage.getItem(OAUTH_RETURN_TO_KEY)
  sessionStorage.removeItem(OAUTH_RETURN_TO_KEY)
  if (stored && stored.startsWith('/')) {
    return stored
  }
  return fallback
}

export function useOAuthReconnect() {
  const { t } = useTranslation()

  const startOAuthReconnect = useCallback(
    async (connectionId: string, returnTo?: string) => {
      if (returnTo) {
        sessionStorage.setItem(OAUTH_RETURN_TO_KEY, returnTo)
      }
      try {
        const url = await connections.getReauthUrl(connectionId)
        window.location.assign(url)
      } catch (e) {
        sessionStorage.removeItem(OAUTH_RETURN_TO_KEY)
        const message = e instanceof Error ? e.message : String(e)
        toast.error(message || t('accounts.connectError'))
      }
    },
    [t],
  )

  return { startOAuthReconnect }
}
