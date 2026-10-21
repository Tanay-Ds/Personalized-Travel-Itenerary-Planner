import { useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, ApiError } from '@/api/client'
import type { Activity, TripDetail } from '@/types/trip'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import ActivityEditDialog from '@/components/ActivityEditDialog'
import { DndContext, closestCenter, PointerSensor, useSensor, useSensors, type DragEndEvent } from '@dnd-kit/core'
import { SortableContext, verticalListSortingStrategy, useSortable, arrayMove } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import type { ReactNode } from 'react'

const hhmm = (t: string | null) => (t ? t.slice(0, 5) : '')
const DOT = ' \u00B7 '

function SortableCard({
    id,
    children,
}: {
    id: string
    children: (handleProps: Record<string, any>) => ReactNode
}) {
    const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id })
    const style = {
        transform: CSS.Transform.toString(transform),
        transition,
        opacity: isDragging ? 0.6 : 1,
    }
    return (
        <div ref={setNodeRef} style={style}>
            {children({ ...attributes, ...listeners })}
        </div>
    )
}

export default function TripPage() {
    const { tripId } = useParams()
    const [searchParams, setSearchParams] = useSearchParams()
    const queryClient = useQueryClient()
    const [editing, setEditing] = useState<Activity | null>(null)

    const { data: trip, isLoading, error } = useQuery({
        queryKey: ['trip', tripId],
        queryFn: () => api.get<TripDetail>(`/api/trips/${tripId}`),
        enabled: !!tripId,
    })

    const deleteMutation = useMutation({
        mutationFn: (activityId: string) => api.delete(`/api/activities/${activityId}`),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['trip', tripId] })
            queryClient.invalidateQueries({ queryKey: ['trips'] })
        },
        onError: (err) => {
            window.alert(err instanceof ApiError ? err.message : 'Could not delete the activity.')
        },
    })

    const regenMutation = useMutation({
        mutationFn: (dayNumber: number) =>
            api.post<TripDetail>(`/api/trips/${tripId}/days/${dayNumber}/regenerate`, {}),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['trip', tripId] })
            queryClient.invalidateQueries({ queryKey: ['trips'] })
        },
        onError: (err) => {
            window.alert(err instanceof ApiError ? err.message : 'Could not regenerate the day.')
        },
    })

    const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 5 } }))

    const reorderMutation = useMutation({
        mutationFn: (v: { dayNumber: number; ids: string[] }) =>
            api.post<TripDetail>(`/api/trips/${tripId}/days/${v.dayNumber}/reorder`, { activity_ids: v.ids }),
        onSuccess: (data) => {
            queryClient.setQueryData(['trip', tripId], data)
        },
        onError: (err) => {
            window.alert(err instanceof ApiError ? err.message : 'Could not save the new order.')
            queryClient.invalidateQueries({ queryKey: ['trip', tripId] })
        },
    })

    const handleDelete = (a: Activity) => {
        if (window.confirm(`Delete "${a.title}"?`)) deleteMutation.mutate(a.id)
    }

    if (isLoading) return <p className="text-muted-foreground">Loading trip...</p>
    if (error || !trip)
        return (
            <div>
                <p className="text-red-600">{error instanceof ApiError ? error.message : 'Trip not found'}</p>
                <Link to="/dashboard" className="underline">
                    Back to dashboard
                </Link>
            </div>
        )

    const requested = Number(searchParams.get('day') ?? '1')
    const day = trip.days.find((d) => d.day_number === requested) ?? trip.days[0]
    const sortedActs = day ? [...day.activities].sort((a, b) => a.position - b.position) : []

    const handleDragEnd = (event: DragEndEvent) => {
        const { active, over } = event
        if (!day || !over || active.id === over.id) return
        const oldIndex = sortedActs.findIndex((a) => a.id === active.id)
        const newIndex = sortedActs.findIndex((a) => a.id === over.id)
        if (oldIndex < 0 || newIndex < 0) return
        const ids = arrayMove(sortedActs, oldIndex, newIndex).map((a) => a.id)
        // Show the new order immediately, then save it.
        queryClient.setQueryData<TripDetail>(['trip', tripId], (old) =>
            old
                ? {
                    ...old,
                    days: old.days.map((d) =>
                        d.id === day.id
                            ? { ...d, activities: d.activities.map((a) => ({ ...a, position: ids.indexOf(a.id) })) }
                            : d,
                    ),
                }
                : old,
        )
        reorderMutation.mutate({ dayNumber: day.day_number, ids })
    }

    return (
        <div className="mx-auto max-w-3xl">
            <Link to="/dashboard" className="text-sm underline">
                Back to dashboard
            </Link>
            <h1 className="mt-2 text-2xl font-semibold">{trip.title || trip.destination}</h1>
            <p className="text-sm text-muted-foreground">
                {trip.destination}
                {DOT}
                {trip.start_date} to {trip.end_date}
                {DOT}
                {trip.group_size} traveller(s)
            </p>
            <p className="mb-4 mt-1 text-sm">
                Estimated total: {Math.round(trip.total_estimated_cost)} of {trip.budget ?? '-'} {trip.currency}
            </p>

            <div className="mb-4 flex flex-wrap gap-2">
                {trip.days.map((d) => (
                    <Button
                        key={d.id}
                        size="sm"
                        variant={day?.id === d.id ? 'default' : 'outline'}
                        onClick={() => setSearchParams({ day: String(d.day_number) })}
                    >
                        Day {d.day_number}
                    </Button>
                ))}
            </div>

            {!day && <p className="text-muted-foreground">This trip has no days yet.</p>}

            {day && (
                <div>
                    <div className="mb-3">
                        <h2 className="text-lg font-semibold">
                            Day {day.day_number}
                            {day.date ? `${DOT}${day.date}` : ''}
                        </h2>
                        {day.summary && <p className="text-sm text-muted-foreground">{day.summary}</p>}
                        <p className="text-sm">
                            Day cost: {Math.round(day.estimated_cost)} {trip.currency}
                        </p>
                        <Button
                            size="sm"
                            variant="outline"
                            className="mt-2"
                            disabled={regenMutation.isPending}
                            onClick={() => {
                                if (window.confirm(`Replace all activities on Day ${day.day_number} with a new plan?`))
                                    regenMutation.mutate(day.day_number)
                            }}
                        >
                            {regenMutation.isPending ? 'Regenerating... (10-20 sec)' : 'Regenerate day'}
                        </Button>
                    </div>

                    <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
                        <SortableContext items={sortedActs.map((a) => a.id)} strategy={verticalListSortingStrategy}>
                            <div className="space-y-3">
                                {sortedActs.map((a) => (
                                    <SortableCard key={a.id} id={a.id}>
                                        {(handle) => (
                                            <Card className="p-4">
                                                <div className="flex items-start justify-between gap-3">
                                                    <div>
                                                        <p className="text-xs uppercase text-muted-foreground">
                                                            {a.type}
                                                            {a.start_time ? `${DOT}${hhmm(a.start_time)}` : ''}
                                                            {a.end_time ? ` - ${hhmm(a.end_time)}` : ''}
                                                        </p>
                                                        <h3 className="font-semibold">{a.title}</h3>
                                                        {a.location_name && (
                                                            <p className="text-sm text-muted-foreground">{a.location_name}</p>
                                                        )}
                                                        {a.description && <p className="mt-1 text-sm">{a.description}</p>}
                                                    </div>
                                                    <div className="flex flex-col items-end gap-2">
                                                        <p className="whitespace-nowrap text-sm font-medium">
                                                            {Math.round(a.estimated_cost)} {trip.currency}
                                                        </p>
                                                        <div className="flex gap-2">
                                                            <Button
                                                                size="sm"
                                                                variant="outline"
                                                                className="cursor-grab touch-none"
                                                                {...handle}
                                                            >
                                                                Drag
                                                            </Button>
                                                            <Button size="sm" variant="outline" onClick={() => setEditing(a)}>
                                                                Edit
                                                            </Button>
                                                            <Button
                                                                size="sm"
                                                                variant="outline"
                                                                onClick={() => handleDelete(a)}
                                                                disabled={deleteMutation.isPending}
                                                            >
                                                                Delete
                                                            </Button>
                                                        </div>
                                                    </div>
                                                </div>
                                            </Card>
                                        )}
                                    </SortableCard>
                                ))}
                            </div>
                        </SortableContext>
                    </DndContext>
                </div>
            )}

            {editing && tripId && (
                <ActivityEditDialog key={editing.id} activity={editing} tripId={tripId} onClose={() => setEditing(null)} />
            )}
        </div>
    )
}