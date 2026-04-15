import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { NavBar } from './components/NavBar'
import { CounterpartyEditPage } from './pages/CounterpartyEditPage'
import { CounterpartyListPage } from './pages/CounterpartyListPage'
import { StpExceptionCreatePage } from './pages/StpExceptionCreatePage'
import { StpExceptionListPage } from './pages/StpExceptionListPage'
import { TradeListPage } from './pages/TradeListPage'
import { TriagePage } from './pages/TriagePage'

export default function App() {
  return (
    <BrowserRouter>
      <div style={{ minHeight: '100vh', backgroundColor: '#f1f5f9' }}>
        <NavBar />
        <Routes>
          <Route path="/" element={<TriagePage />} />
          <Route path="/trades" element={<TradeListPage />} />
          <Route path="/stp-exceptions" element={<StpExceptionListPage />} />
          <Route path="/stp-exceptions/new" element={<StpExceptionCreatePage />} />
          <Route path="/counterparties" element={<CounterpartyListPage />} />
          <Route path="/counterparties/:lei" element={<CounterpartyEditPage />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}
