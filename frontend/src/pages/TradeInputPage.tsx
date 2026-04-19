import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { listCounterparties } from '../api/counterparties'
import { listReferenceData } from '../api/referenceData'
import { createTrade } from '../api/trades'
import { PageLayout } from '../components/PageLayout'
import { BTN_PRIMARY, BTN_SECONDARY, CARD, COLOR, INPUT, LABEL } from '../styles/theme'
import type { Counterparty } from '../types/counterparty'
import type { ReferenceData } from '../types/referenceData'

function deriveCurrencies(instrumentId: string): string[] {
  if (instrumentId.length === 6) {
    return [instrumentId.slice(0, 3), instrumentId.slice(3, 6)]
  }
  return []
}

export function TradeInputPage() {
  const navigate = useNavigate()

  const [tradeId, setTradeId] = useState('')
  const [tradeDate, setTradeDate] = useState('')
  const [valueDate, setValueDate] = useState('')
  const [counterpartyLei, setCounterpartyLei] = useState('')
  const [instrumentId, setInstrumentId] = useState('')
  const [currency, setCurrency] = useState('')
  const [amount, setAmount] = useState('')

  const [counterparties, setCounterparties] = useState<Counterparty[]>([])
  const [instruments, setInstruments] = useState<ReferenceData[]>([])

  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    listCounterparties({ limit: 100 }).then(r => setCounterparties(r.items.filter(c => c.is_active))).catch(() => {})
    listReferenceData().then(r => setInstruments(r.items.filter(i => i.is_active))).catch(() => {})
  }, [])

  useEffect(() => {
    setCurrency('')
  }, [instrumentId])

  const currencyOptions = deriveCurrencies(instrumentId)

  const handleCreate = async () => {
    if (!tradeId.trim() || !tradeDate || !valueDate || !counterpartyLei || !instrumentId || !currency || !amount) {
      setError('All fields are required.')
      return
    }
    const amountNum = parseFloat(amount)
    if (isNaN(amountNum) || amountNum <= 0) {
      setError('Amount must be a positive number.')
      return
    }
    setError('')
    setSaving(true)
    try {
      const trade = await createTrade({
        trade_id: tradeId.trim(),
        trade_date: tradeDate,
        value_date: valueDate,
        counterparty_lei: counterpartyLei,
        instrument_id: instrumentId,
        currency,
        amount: amountNum,
      })
      navigate(`/trades/${trade.trade_id}`)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err)
      setError(`Failed to create trade: ${msg}`)
    } finally {
      setSaving(false)
    }
  }

  return (
    <PageLayout title="New Trade">
      <div style={{ maxWidth: 560 }}>
        <div style={CARD}>
          {error && (
            <div style={{ backgroundColor: '#fee2e2', color: '#991b1b', padding: '0.75rem', borderRadius: 6, marginBottom: '1rem', fontSize: '0.875rem' }}>
              {error}
            </div>
          )}

          <div style={{ marginBottom: '1rem' }}>
            <label style={LABEL}>Trade ID</label>
            <input
              style={INPUT}
              value={tradeId}
              onChange={e => setTradeId(e.target.value)}
              placeholder="TRD-020"
            />
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={LABEL}>Trade Date</label>
            <input
              type="date"
              style={INPUT}
              value={tradeDate}
              onChange={e => setTradeDate(e.target.value)}
            />
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={LABEL}>Value Date</label>
            <input
              type="date"
              style={INPUT}
              value={valueDate}
              onChange={e => setValueDate(e.target.value)}
            />
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={LABEL}>Counterparty</label>
            <select
              style={{ ...INPUT }}
              value={counterpartyLei}
              onChange={e => setCounterpartyLei(e.target.value)}
            >
              <option value="">— select —</option>
              {counterparties.map(cp => (
                <option key={cp.lei} value={cp.lei}>{cp.name} ({cp.lei})</option>
              ))}
            </select>
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={LABEL}>Instrument</label>
            <select
              style={{ ...INPUT }}
              value={instrumentId}
              onChange={e => setInstrumentId(e.target.value)}
            >
              <option value="">— select —</option>
              {instruments.map(i => (
                <option key={i.instrument_id} value={i.instrument_id}>
                  {i.instrument_id} — {i.description}
                </option>
              ))}
            </select>
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={LABEL}>Currency (CCY)</label>
            <select
              style={{ ...INPUT }}
              value={currency}
              onChange={e => setCurrency(e.target.value)}
              disabled={currencyOptions.length === 0}
            >
              <option value="">{instrumentId ? '— select —' : '— select instrument first —'}</option>
              {currencyOptions.map(ccy => (
                <option key={ccy} value={ccy}>{ccy}</option>
              ))}
            </select>
            <span style={{ fontSize: '0.75rem', color: COLOR.textLight }}>
              Derived from instrument. Also used as settlement currency.
            </span>
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label style={LABEL}>Amount</label>
            <input
              type="number"
              style={INPUT}
              value={amount}
              onChange={e => setAmount(e.target.value)}
              placeholder="1000000"
              min="0.00001"
              step="0.00001"
            />
          </div>

          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <button onClick={handleCreate} disabled={saving} style={BTN_PRIMARY}>
              {saving ? 'Creating…' : 'Create Trade'}
            </button>
            <button onClick={() => navigate('/trades')} style={BTN_SECONDARY}>
              Cancel
            </button>
          </div>
        </div>
      </div>
    </PageLayout>
  )
}
