import { useEffect, useState } from 'react'
import { listSettings, updateSetting } from '../api/settings'
import { PageLayout } from '../components/PageLayout'
import { CARD, COLOR, LABEL } from '../styles/theme'
import type { AppSetting } from '../types/settings'

const TRIGGER_KEYS = ['fo_check_trigger', 'bo_check_trigger', 'fo_triage_trigger', 'bo_triage_trigger']
const TRIGGER_LABELS: Record<string, string> = {
  fo_check_trigger: 'FoCheck Trigger',
  bo_check_trigger: 'BoCheck Trigger',
  fo_triage_trigger: 'FO Triage Trigger',
  bo_triage_trigger: 'BO Triage Trigger',
}
const TRIGGER_DESCS: Record<string, string> = {
  fo_check_trigger: 'auto: runs FoCheck automatically after trade creation (Initial). manual: operator must trigger via API or UI.',
  bo_check_trigger: 'auto: runs BoCheck automatically when a trade reaches FoValidated. manual: operator must trigger via API or UI.',
  fo_triage_trigger: 'auto: starts FO triage automatically after FoCheck fails. manual: operator starts via Start FO Triage button.',
  bo_triage_trigger: 'auto: starts BO triage automatically after BoCheck fails. manual: operator starts via Start BO Triage button.',
}

function ToggleButton({
  value,
  onChange,
  saving,
}: {
  value: string
  onChange: (v: string) => void
  saving: boolean
}) {
  const btn = (v: string) => ({
    padding: '0.4rem 1rem',
    border: '1px solid',
    borderRadius: 6,
    fontWeight: 600,
    fontSize: '0.85rem',
    cursor: saving ? 'not-allowed' : 'pointer',
    borderColor: value === v ? COLOR.primary : COLOR.border,
    backgroundColor: value === v ? COLOR.primary : '#fff',
    color: value === v ? '#fff' : COLOR.textMuted,
    transition: 'all 0.15s',
  })
  return (
    <div style={{ display: 'flex', gap: 8 }}>
      <button style={btn('auto')} disabled={saving} onClick={() => onChange('auto')}>auto</button>
      <button style={btn('manual')} disabled={saving} onClick={() => onChange('manual')}>manual</button>
    </div>
  )
}

export function SettingsPage() {
  const [settings, setSettings] = useState<AppSetting[]>([])
  const [saving, setSaving] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    listSettings()
      .then(r => setSettings(r.items))
      .catch(() => setError('Failed to load settings.'))
      .finally(() => setLoading(false))
  }, [])

  const handleChange = async (key: string, value: string) => {
    setSaving(key)
    setError('')
    try {
      const updated = await updateSetting(key, value)
      setSettings(prev => prev.map(s => s.key === key ? { ...s, value: updated.value } : s))
    } catch {
      setError(`Failed to update ${key}.`)
    } finally {
      setSaving(null)
    }
  }

  const settingMap = Object.fromEntries(settings.map(s => [s.key, s]))

  return (
    <PageLayout title="Settings">
      {loading ? (
        <p style={{ color: COLOR.textMuted }}>Loading…</p>
      ) : (
        <div style={{ ...CARD, maxWidth: 600 }}>
          {error && (
            <div style={{ marginBottom: '1rem', padding: '0.75rem', backgroundColor: '#fee2e2', borderRadius: 6, color: '#991b1b', fontSize: '0.875rem' }}>
              {error}
            </div>
          )}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
            {TRIGGER_KEYS.map(key => {
              const s = settingMap[key]
              if (!s) return null
              return (
                <div key={key}>
                  <label style={LABEL}>{TRIGGER_LABELS[key]}</label>
                  <ToggleButton value={s.value} onChange={v => handleChange(key, v)} saving={saving === key} />
                  <p style={{ marginTop: '0.4rem', fontSize: '0.8rem', color: COLOR.textMuted }}>{TRIGGER_DESCS[key]}</p>
                  {saving === key && <p style={{ marginTop: '0.3rem', fontSize: '0.8rem', color: COLOR.primary }}>Saving…</p>}
                </div>
              )
            })}
          </div>
        </div>
      )}
    </PageLayout>
  )
}
