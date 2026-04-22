import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import client from '../api/client'

export default function Home() {
  const [url, setUrl] = useState('')
  const [maxVideos, setMaxVideos] = useState(5)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  async function handleSubmit(e) {
    e.preventDefault()
    if (!url.trim()) return
    setLoading(true)
    setError('')
    try {
      const { data } = await client.post('/analyse', { channel_url: url.trim(), max_videos: maxVideos })
      navigate(`/channel/${data.channel_id}`, {
        state: { jobId: data.job_id, title: data.channel_title },
      })
    } catch (err) {
      setError(err.response?.data?.detail || 'Something went wrong. Check the URL and try again.')
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col items-center justify-center px-4">
      <div className="w-full max-w-xl text-center">
        <div className="mb-10">
          <h1 className="text-6xl font-bold text-white tracking-tight">
            Creator<span className="text-violet-400">Lens</span>
          </h1>
          <p className="mt-4 text-gray-400 text-lg">
            YouTube creator intelligence — brands, sponsors, and chat
          </p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="flex gap-3">
            <input
              type="text"
              value={url}
              onChange={e => setUrl(e.target.value)}
              placeholder="https://www.youtube.com/@CreatorName"
              className="flex-1 bg-gray-900 border border-gray-700 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent transition"
              disabled={loading}
            />
            <input
              type="number"
              min={1}
              max={50}
              value={maxVideos}
              onChange={e => setMaxVideos(Number(e.target.value))}
              className="w-20 bg-gray-900 border border-gray-700 rounded-xl px-3 py-3 text-white text-center focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent transition"
              disabled={loading}
              title="Max videos to ingest"
            />
            <button
              type="submit"
              disabled={loading || !url.trim()}
              className="bg-violet-600 hover:bg-violet-500 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold px-6 py-3 rounded-xl transition-colors"
            >
              {loading ? 'Starting…' : 'Analyse'}
            </button>
          </div>
          {error && <p className="mt-3 text-red-400 text-sm text-left">{error}</p>}
        </form>

        <p className="mt-8 text-gray-600 text-sm">
          The number field controls how many videos to ingest · extracts brands &amp; sponsors · enables RAG chat
        </p>
      </div>
    </div>
  )
}
