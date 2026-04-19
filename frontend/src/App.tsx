import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { NavBar } from './components/NavBar'
import { CounterpartyEditPage } from './pages/CounterpartyEditPage'
import { CounterpartyListPage } from './pages/CounterpartyListPage'
import { ReferenceDataListPage } from './pages/ReferenceDataListPage'
import { SettingsPage } from './pages/SettingsPage'
import { SsiEditPage } from './pages/SsiEditPage'
import { SsiListPage } from './pages/SsiListPage'
import { StpExceptionCreatePage } from './pages/StpExceptionCreatePage'
import { StpExceptionListPage } from './pages/StpExceptionListPage'
import { TradeDetailPage } from './pages/TradeDetailPage'
import { TradeListPage } from './pages/TradeListPage'
import { TriageHistoryPage } from './pages/TriageHistoryPage'
import { TriagePage } from './pages/TriagePage'

export default function App() {
  return (
    <BrowserRouter>
      <div style={{ minHeight: '100vh', backgroundColor: '#f1f5f9', paddingTop: 52, overflowX: 'hidden' }}>
        <NavBar />
        <Routes>
          <Route path="/" element={<TriagePage />} />
          <Route path="/history" element={<TriageHistoryPage />} />
          <Route path="/trades" element={<TradeListPage />} />
          <Route path="/trades/:trade_id" element={<TradeDetailPage />} />
          <Route path="/stp-exceptions" element={<StpExceptionListPage />} />
          <Route path="/stp-exceptions/new" element={<StpExceptionCreatePage />} />
          <Route path="/counterparties" element={<CounterpartyListPage />} />
          <Route path="/counterparties/:lei" element={<CounterpartyEditPage />} />
          <Route path="/ssis" element={<SsiListPage />} />
          <Route path="/ssis/:id" element={<SsiEditPage />} />
          <Route path="/reference-data" element={<ReferenceDataListPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}
