import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Cloud, HardDrive } from 'lucide-react'
import { admin } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

export function DriveBackupSettings() {
  const { t, i18n } = useTranslation()
  const queryClient = useQueryClient()
  const [password, setPassword] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['admin', 'drive-backup'],
    queryFn: () => admin.getDriveBackup(),
  })

  const saveMutation = useMutation({
    mutationFn: (body: { schedule?: 'daily' | 'weekly'; password?: string; clear_password?: boolean }) =>
      admin.updateDriveBackup(body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'drive-backup'] })
      setPassword('')
      toast.success(t('admin.settings.driveBackupSaved'))
    },
    onError: () => toast.error(t('common.error')),
  })

  const disconnectMutation = useMutation({
    mutationFn: () => admin.disconnectDriveBackup(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'drive-backup'] })
      toast.success(t('admin.settings.driveBackupDisconnected'))
    },
    onError: () => toast.error(t('common.error')),
  })

  const connect = async () => {
    try {
      const { url } = await admin.getDriveBackupOAuthUrl()
      window.location.href = url
    } catch {
      toast.error(t('admin.settings.driveBackupConnectError'))
    }
  }

  const lastRunLabel = () => {
    if (!data?.last_run_at) return t('admin.settings.driveBackupLastRunNever')
    const when = new Date(data.last_run_at).toLocaleString(i18n.language)
    if (data.last_run_ok) return t('admin.settings.driveBackupLastRunOk', { when })
    return t('admin.settings.driveBackupLastRunFailed', {
      when,
      error: data.last_run_error || t('common.error'),
    })
  }

  return (
    <div className="rounded-xl border border-border/60 bg-card overflow-hidden mb-8">
      <div className="px-5 py-4 border-b border-border/40">
        <div className="flex items-center gap-2 mb-0.5">
          <HardDrive size={15} className="text-muted-foreground" />
          <h3 className="text-sm font-semibold text-foreground">{t('admin.settings.driveBackupTitle')}</h3>
        </div>
        <p className="text-xs text-muted-foreground">{t('admin.settings.driveBackupDesc')}</p>
      </div>

      {isLoading || !data ? (
        <div className="p-5">
          <Skeleton className="h-8 w-64" />
        </div>
      ) : !data.available ? (
        <div className="px-5 py-4 text-sm text-muted-foreground">
          {t('admin.settings.driveBackupUnavailable')}
        </div>
      ) : (
        <div className="p-5 space-y-4">
          <div className="flex items-center justify-between gap-3">
            <div className="min-w-0">
              <p className="text-sm text-foreground">
                {data.connected
                  ? t('admin.settings.driveBackupConnectedAs', { email: data.google_email || 'Google' })
                  : t('admin.settings.driveBackupNotConnected')}
              </p>
              <p className="text-xs text-muted-foreground mt-0.5">
                {t('admin.settings.driveBackupFolder', { folder: data.folder_name })}
              </p>
            </div>
            {data.connected ? (
              <Button
                variant="outline"
                size="sm"
                onClick={() => disconnectMutation.mutate()}
                disabled={disconnectMutation.isPending}
              >
                {t('admin.settings.driveBackupDisconnect')}
              </Button>
            ) : (
              <Button size="sm" onClick={connect}>
                <Cloud size={14} className="mr-1.5" />
                {t('admin.settings.driveBackupConnect')}
              </Button>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label className="text-xs">{t('admin.settings.driveBackupSchedule')}</Label>
              <Select
                value={data.schedule}
                onValueChange={(value) => {
                  if (value === 'daily' || value === 'weekly') {
                    saveMutation.mutate({ schedule: value })
                  }
                }}
              >
                <SelectTrigger className="h-9">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="daily">{t('admin.settings.driveBackupDaily')}</SelectItem>
                  <SelectItem value="weekly">{t('admin.settings.driveBackupWeekly')}</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">{t('admin.settings.driveBackupPassword')}</Label>
              <div className="flex gap-2">
                <Input
                  type="password"
                  className="h-9"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder={
                    data.has_password
                      ? t('admin.settings.driveBackupPasswordSet')
                      : t('admin.settings.driveBackupPasswordPlaceholder')
                  }
                  autoComplete="new-password"
                />
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  disabled={!password || password.length < 8 || saveMutation.isPending}
                  onClick={() => saveMutation.mutate({ password })}
                >
                  {t('common.save')}
                </Button>
              </div>
              {data.has_password && (
                <button
                  type="button"
                  className="text-xs text-muted-foreground hover:text-foreground"
                  onClick={() => saveMutation.mutate({ clear_password: true })}
                >
                  {t('admin.settings.driveBackupClearPassword')}
                </button>
              )}
            </div>
          </div>

          <p className="text-xs text-muted-foreground">{lastRunLabel()}</p>
        </div>
      )}
    </div>
  )
}
