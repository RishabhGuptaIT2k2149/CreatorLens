export default function SponsorsTab({ data, loading }) {
  if (loading) return <LoadingState />
  if (!data || data.sponsors.length === 0) {
    return (
      <EmptyState label="No sponsorships detected yet. Sponsor detection runs during ingestion." />
    )
  }

  return (
    <div className="space-y-4">
      <p className="text-gray-400 text-sm">
        {data.sponsors.length} sponsorship segment{data.sponsors.length !== 1 ? 's' : ''} detected
      </p>

      <div className="space-y-3">
        {data.sponsors.map((s, i) => (
          <div key={i} className="bg-gray-900 border border-gray-800 rounded-xl p-4 space-y-3">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="font-semibold text-white text-lg">{s.sponsor_name}</p>
                <p className="text-gray-500 text-xs mt-0.5">
                  Video: {s.video_id} · detected via {s.detection_method}
                </p>
              </div>
              <ConfidenceBadge value={s.confidence} />
            </div>

            {s.evidence && (
              <blockquote className="border-l-2 border-violet-600 pl-3 text-gray-400 text-sm italic">
                "{s.evidence}"
              </blockquote>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

function ConfidenceBadge({ value }) {
  const pct = Math.round(value * 100)
  const color =
    pct >= 80 ? 'text-green-400 border-green-700' :
    pct >= 50 ? 'text-yellow-400 border-yellow-700' :
                'text-red-400 border-red-700'

  return (
    <span className={`border rounded-full px-3 py-1 text-xs font-semibold shrink-0 ${color}`}>
      {pct}% confidence
    </span>
  )
}

function LoadingState() {
  return (
    <div className="flex flex-col items-center justify-center py-24 text-gray-500">
      <div className="w-8 h-8 border-2 border-violet-500 border-t-transparent rounded-full animate-spin mb-4" />
      <p className="text-sm">Waiting for ingestion to complete…</p>
    </div>
  )
}

function EmptyState({ label }) {
  return (
    <div className="flex items-center justify-center py-24 text-gray-500 text-sm">{label}</div>
  )
}
