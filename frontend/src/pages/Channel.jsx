import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import client from '../api/client'
import OverviewTab from '../components/OverviewTab'
import BrandsTab from '../components/BrandsTab'
import SponsorsTab from '../components/SponsorsTab'
import ChatPanel from '../components/ChatPanel'

const TABS = ['Overview', 'Brands', 'Sponsors', 'Chat']

export default function Channel() {
  const { channelId } = useParams()
  const navigate = useNavigate()

  const [activeTab, setActiveTab] = useState('Overview')
  const [status, setStatus] = useState(null)
  const [overview, setOverview] = useState(null)
  const [brands, setBrands] = useState(null)
  const [sponsors, setSponsors] = useState(null)
  const [fetchError, setFetchError] = useState('')

  useEffect(() => {
    let timer

    async function poll() {
      try {
        const { data } = await client.get(`/channel/${channelId}/status`)
        setStatus(data)

        if (data.status === 'done') {
          const [ov, br, sp] = await Promise.all([
            client.get(`/channel/${channelId}/overview`).then(r => r.data).catch(() => null),
            client.get(`/channel/${channelId}/brands`).then(r => r.data).catch(() => null),
            client.get(`/channel/${channelId}/sponsors`).then(r => r.data).catch(() => null),
          ])
          setOverview(ov)
          setBrands(br)
          setSponsors(sp)
        } else if (data.status === 'error') {
          setFetchError(data.error || 'Ingestion failed')
        } else {
          timer = setTimeout(poll, 2000)
        }
      } catch {
        timer = setTimeout(poll, 3000)
      }
    }

    poll()
    return () => clearTimeout(timer)
  }, [channelId])

  const isDone = status?.status === 'done'
  const isRunning = status?.status === 'running' || status?.status === 'pending'
  const progress = status?.total > 0 ? Math.round((status.progress / status.total) * 100) : 0

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <header className="border-b border-gray-800 px-6 py-4 flex items-center gap-4">
        <button
          onClick={() => navigate('/')}
          className="text-gray-400 hover:text-white transition text-sm flex items-center gap-1"
        >
          ← Back
        </button>
        <span className="text-xl font-bold">
          Creator<span className="text-violet-400">Lens</span>
        </span>
        {overview && (
          <span className="text-gray-400 text-sm ml-auto">
            {overview.title} · {(overview.subscriber_count / 1_000_000).toFixed(1)}M subscribers
          </span>
        )}
      </header>

      {/* Progress bar */}
      {isRunning && (
        <div className="bg-gray-900 border-b border-gray-800 px-6 py-3">
          <div className="flex justify-between text-sm text-gray-400 mb-2">
            <span>Ingesting videos…</span>
            <span>{status.progress} / {status.total} ({progress}%)</span>
          </div>
          <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-violet-500 rounded-full transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Error */}
      {fetchError && (
        <div className="mx-6 mt-4 p-4 bg-red-950 border border-red-800 rounded-xl text-red-300 text-sm">
          {fetchError}
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-800 px-6">
        <div className="flex">
          {TABS.map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-5 py-3 text-sm font-medium transition-colors border-b-2 ${
                activeTab === tab
                  ? 'border-violet-500 text-white'
                  : 'border-transparent text-gray-500 hover:text-gray-300'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <main className="px-6 py-8 max-w-5xl mx-auto">
        {activeTab === 'Overview' && <OverviewTab data={overview} loading={!isDone} />}
        {activeTab === 'Brands'   && <BrandsTab data={brands} loading={!isDone} />}
        {activeTab === 'Sponsors' && <SponsorsTab data={sponsors} loading={!isDone} />}
        {activeTab === 'Chat'     && <ChatPanel channelId={channelId} />}
      </main>
    </div>
  )
}
