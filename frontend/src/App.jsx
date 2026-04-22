import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import Channel from './pages/Channel'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/channel/:channelId" element={<Channel />} />
      </Routes>
    </BrowserRouter>
  )
}