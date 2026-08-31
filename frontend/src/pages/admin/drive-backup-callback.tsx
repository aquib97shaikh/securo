import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { toast } from 'sonner'
import axios from 'axios'
import { admin } from '@/lib/api'

export default function DriveBackupCallbackPage() {
  const { t } = useTranslation()
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const code = params.get('code')
  const state = params.get('state')
  const errorParam = params.get('error')
  const errorDescription = params.get('error_description')
  const [busy, setBusy] = useState(true)

  useEffect(() => {
    if (errorParam) {
      toast.error(errorDescription || errorParam)
      navigate('/admin', { replace: true })
      return
    }
    if (!code || !state) {
      toast.error(t('admin.settings.driveBackupConnectError'))
      navigate('/admin', { replace: true })
      return
    }
    const submitKey = `drive-oauth-submitted:${code}:${state}`
    if (sessionStorage.getItem(submitKey)) return
    sessionStorage.setItem(submitKey, '1')

    ;(async () => {
      try {
        await admin.completeDriveBackupOAuth(code, state)
        toast.success(t('admin.settings.driveBackupConnected'))
        navigate('/admin', { replace: true })
      } catch (err) {
        sessionStorage.removeItem(submitKey)
        const message =
          axios.isAxiosError(err) && err.response?.data?.detail
            ? String(err.response.data.detail)
            : t('admin.settings.driveBackupConnectError')
        toast.error(message)
        navigate('/admin', { replace: true })
      } finally {
        setBusy(false)
      }
    })()
  }, [code, state, errorParam, errorDescription, navigate, t])

  return (
    <div className="flex items-center justify-center min-h-[40vh] text-sm text-muted-foreground">
      {busy ? t('admin.settings.driveBackupConnecting') : t('common.loading')}
    </div>
  )
}
