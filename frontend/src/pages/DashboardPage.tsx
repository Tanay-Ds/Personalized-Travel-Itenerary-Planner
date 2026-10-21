import { useQuery } from '@tanstack/react-query'
import { api, ApiError } from '@/api/client'

type MeResponse = {
  id: string
  email: string
  profile: Record<string, unknown> | null
}

export default function DashboardPage() {
  const { data, error, isLoading } = useQuery({
    queryKey: ['me'],
    queryFn: () => api.get<MeResponse>('/api/me'),
    retry: false,
  })

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Dashboard</h1>
      <p className="text-sm text-muted-foreground">
        Trips will appear here in M5. For now this page checks the API connection.
      </p>

      <div className="rounded-md border p-4">
        <h2 className="mb-2 font-medium">API check: GET /api/me</h2>
        {isLoading && <p className="text-sm">Calling the API...</p>}
        {error && (
          <p className="text-sm text-red-600">
            Failed: {error instanceof ApiError ? `${error.code} (${error.status}): ${error.message}` : 'unknown error'}
          </p>
        )}
        {data && (
          <>
            <p className="mb-2 text-sm text-green-700">Success. The API accepted your token.</p>
            <pre className="overflow-x-auto rounded bg-muted p-3 text-xs">
              {JSON.stringify(data, null, 2)}
            </pre>
          </>
        )}
      </div>
    </div>
  )
}