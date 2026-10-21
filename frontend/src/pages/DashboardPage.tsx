import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, ApiError } from '@/api/client'
import type { Trip } from '@/types/trip'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

export default function DashboardPage() {
    const queryClient = useQueryClient()

    const { data, isLoading, error } = useQuery({
        queryKey: ['trips'],
        queryFn: () => api.get<Trip[]>('/api/trips'),
    })

    const del = useMutation({
        mutationFn: (id: string) => api.delete(`/api/trips/${id}`),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['trips'] }),
    })

    return (
        <div>
            <div className="mb-6 flex items-center justify-between">
                <h1 className="text-2xl font-semibold">My trips</h1>
                <Button asChild>
                    <Link to="/trips/new">New trip</Link>
                </Button>
            </div>

            {isLoading && <p className="text-muted-foreground">Loading trips...</p>}
            {error && (
                <p className="text-red-600">{error instanceof ApiError ? error.message : 'Could not load trips'}</p>
            )}
            {data && data.length === 0 && (
                <p className="text-muted-foreground">No trips yet. Click "New trip" to create one.</p>
            )}

            <div className="grid gap-4 sm:grid-cols-2">
                {data?.map((trip) => (
                    <Card key={trip.id} className="p-4">
                        <Link to={`/trips/${trip.id}`} className="block">
                            <h2 className="text-lg font-semibold">{trip.title || trip.destination}</h2>
                            <p className="text-sm text-muted-foreground">{trip.destination}</p>
                            <p className="mt-1 text-sm">
                                {trip.start_date} to {trip.end_date}
                            </p>
                            <p className="mt-1 text-sm">
                                Estimated: {Math.round(trip.total_estimated_cost)} / {trip.budget ?? '-'} {trip.currency}
                            </p>
                        </Link>
                        <Button
                            variant="outline"
                            size="sm"
                            className="mt-3"
                            disabled={del.isPending}
                            onClick={() => {
                                if (window.confirm('Delete this trip?')) del.mutate(trip.id)
                            }}
                        >
                            Delete
                        </Button>
                    </Card>
                ))}
            </div>
        </div>
    )
}