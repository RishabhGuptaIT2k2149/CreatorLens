const SENTIMENT_COLOR = {
  positive: 'text-green-400',
  neutral: 'text-gray-400',
  negative: 'text-red-400',
}

const CATEGORY_COLOR = {
  tech: 'bg-blue-900 text-blue-300',
  software: 'bg-indigo-900 text-indigo-300',
  food: 'bg-orange-900 text-orange-300',
  clothing: 'bg-pink-900 text-pink-300',
  automotive: 'bg-yellow-900 text-yellow-300',
  finance: 'bg-emerald-900 text-emerald-300',
  health: 'bg-teal-900 text-teal-300',
  entertainment: 'bg-purple-900 text-purple-300',
  other: 'bg-gray-800 text-gray-400',
}

export default function BrandsTab({ data, loading }) {
  if (loading) return <LoadingState />
  if (!data || data.brands.length === 0) {
    return (
      <EmptyState label="No brand mentions found yet. Brand extraction runs during ingestion." />
    )
  }

  return (
    <div className="space-y-4">
      <p className="text-gray-400 text-sm">
        {data.brands.length} unique brands detected across all transcribed videos
      </p>

      <div className="overflow-x-auto rounded-xl border border-gray-800">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-800 bg-gray-900 text-gray-400 text-xs uppercase tracking-wide">
              <th className="px-4 py-3 text-left">Brand</th>
              <th className="px-4 py-3 text-left">Category</th>
              <th className="px-4 py-3 text-center">Mentions</th>
              <th className="px-4 py-3 text-left">Sentiment</th>
              <th className="px-4 py-3 text-left">Types</th>
              <th className="px-4 py-3 text-center">Videos</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {data.brands.map(brand => {
              const dominantSentiment = Object.entries(brand.sentiment_breakdown).sort(
                (a, b) => b[1] - a[1]
              )[0]?.[0] || 'neutral'

              return (
                <tr key={brand.name} className="hover:bg-gray-900 transition-colors">
                  <td className="px-4 py-3 font-medium text-white">{brand.name}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                        CATEGORY_COLOR[brand.category] || CATEGORY_COLOR.other
                      }`}
                    >
                      {brand.category}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center font-bold text-white">
                    {brand.total_mentions}
                  </td>
                  <td className={`px-4 py-3 capitalize ${SENTIMENT_COLOR[dominantSentiment]}`}>
                    {dominantSentiment}
                  </td>
                  <td className="px-4 py-3 text-gray-400 text-xs">
                    {Object.entries(brand.mention_types)
                      .filter(([, v]) => v > 0)
                      .map(([k, v]) => `${k} (${v})`)
                      .join(', ') || '—'}
                  </td>
                  <td className="px-4 py-3 text-center text-gray-400">
                    {brand.video_ids.length}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
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
