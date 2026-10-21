import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { api, ApiError } from '@/api/client'
import type { Activity } from '@/types/trip'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'

type Props = {
    activity: Activity
    tripId: string
    onClose: () => void
}

const TYPES = ['attraction', 'meal', 'stay', 'transport', 'other']
const hhmm = (t: string | null) => (t ? t.slice(0, 5) : '')

export default function ActivityEditDialog({ activity, tripId, onClose }: Props) {
    const queryClient = useQueryClient()
    const [title, setTitle] = useState(activity.title)
    const [type, setType] = useState<string>(activity.type)
    const [startTime, setStartTime] = useState(hhmm(activity.start_time))
    const [endTime, setEndTime] = useState(hhmm(activity.end_time))
    const [cost, setCost] = useState(String(activity.estimated_cost ?? 0))
    const [location, setLocation] = useState(activity.location_name ?? '')
    const [description, setDescription] = useState(activity.description ?? '')
    const [formError, setFormError] = useState<string | null>(null)

    const mutation = useMutation({
        mutationFn: (body: Record<string, unknown>) => api.patch(`/api/activities/${activity.id}`, body),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['trip', tripId] })
            queryClient.invalidateQueries({ queryKey: ['trips'] })
            onClose()
        },
        onError: (err) => {
            setFormError(err instanceof ApiError ? err.message : 'Could not save. Try again.')
        },
    })

    const handleSave = () => {
        setFormError(null)
        if (!title.trim()) {
            setFormError('Title is required.')
            return
        }
        const costNumber = Number(cost)
        if (Number.isNaN(costNumber) || costNumber < 0) {
            setFormError('Cost must be a number, 0 or more.')
            return
        }
        mutation.mutate({
            title: title.trim(),
            type,
            start_time: startTime || null,
            end_time: endTime || null,
            estimated_cost: costNumber,
            location_name: location.trim() || null,
            description: description.trim() || null,
        })
    }

    return (
        <Dialog open onOpenChange={(open) => !open && onClose()}>
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>Edit activity</DialogTitle>
                </DialogHeader>

                <div className="space-y-3">
                    <div>
                        <Label htmlFor="act-title">Title</Label>
                        <Input id="act-title" value={title} onChange={(e) => setTitle(e.target.value)} />
                    </div>

                    <div>
                        <Label htmlFor="act-type">Type</Label>
                        <select
                            id="act-type"
                            className="h-9 w-full rounded-md border bg-transparent px-3 text-sm"
                            value={type}
                            onChange={(e) => setType(e.target.value)}
                        >
                            {TYPES.map((t) => (
                                <option key={t} value={t}>
                                    {t}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                        <div>
                            <Label htmlFor="act-start">Start time</Label>
                            <Input id="act-start" type="time" value={startTime} onChange={(e) => setStartTime(e.target.value)} />
                        </div>
                        <div>
                            <Label htmlFor="act-end">End time</Label>
                            <Input id="act-end" type="time" value={endTime} onChange={(e) => setEndTime(e.target.value)} />
                        </div>
                    </div>

                    <div>
                        <Label htmlFor="act-cost">Estimated cost</Label>
                        <Input id="act-cost" type="number" min="0" value={cost} onChange={(e) => setCost(e.target.value)} />
                    </div>

                    <div>
                        <Label htmlFor="act-location">Location</Label>
                        <Input id="act-location" value={location} onChange={(e) => setLocation(e.target.value)} />
                    </div>

                    <div>
                        <Label htmlFor="act-desc">Description</Label>
                        <Input id="act-desc" value={description} onChange={(e) => setDescription(e.target.value)} />
                    </div>

                    {formError && <p className="text-sm text-red-600">{formError}</p>}
                </div>

                <DialogFooter>
                    <Button variant="outline" onClick={onClose} disabled={mutation.isPending}>
                        Cancel
                    </Button>
                    <Button onClick={handleSave} disabled={mutation.isPending}>
                        {mutation.isPending ? 'Saving...' : 'Save'}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}