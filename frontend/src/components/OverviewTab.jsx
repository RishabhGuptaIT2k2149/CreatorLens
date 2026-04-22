export default function OverviewTab({ data, loading }) {
  if (loading) return <LoadingState label="Waiting for ingestion to complete…" />
  if (!data) return <EmptyState label="No overview data available." />

  const stats = [
    { label: 'Subscribers', value: fmt(data.subscriber_count) },
    { label: 'Total Videos', value: fmt(data.video_count) },
    { label: 'Transcribed', value: fmt(data.videos_transcribed) },
    { label: 'Failed / Skipped', value: fmt(data.videos_failed) },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white">{data.title}</h2>
        {data.ingested_at && (
          <p className="text-gray-500 text-sm mt-1">
            Last ingested {new Date(data.ingested_at).toLocaleString()}
          </p>
        )}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {stats.map(s => (
          <div key={s.label} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <p className="text-gray-400 text-xs uppercase tracking-widest mb-1">{s.label}</p>
            <p className="text-2xl font-bold text-white">{s.value}</p>
          </div>
        ))}
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
        <p className="text-gray-400 text-sm">
          <span className="text-white font-medium">{data.videos_total_ingested}</span> videos ingested
          into the vector store ·{' '}
          <span className="text-white font-medium">{data.videos_transcribed}</span> successfully
          transcribed by Gemini
        </p>
      </div>
    </div>
  )
}

function fmt(n) {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M'
  if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K'
  return String(n)
}

function LoadingState({ label }) {
  return (
    <div className="flex flex-col items-center justify-center py-24 text-gray-500">
      <div className="w-8 h-8 border-2 border-violet-500 border-t-transparent rounded-full animate-spin mb-4" />
      <p className="text-sm">{label}</p>
    </div>
  )
}

function EmptyState({ label }) {
  return (
    <div className="flex items-center justify-center py-24 text-gray-500 text-sm">{label}</div>
  )
}
