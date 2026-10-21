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
const fieldClass = 'bg-white'
const labelClass = 'mb-1 block text-sky-900'

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
                    <DialogTitle>✈ Edit activity</DialogTitle>
                </DialogHeader>

                <div className="space-y-3">
                    <div>
                        <Label htmlFor="act-title" className={labelClass}>Title</Label>
                        <Input id="act-title" className={fieldClass} value={title} onChange={(e) => setTitle(e.target.value)} />
                    </div>

                    <div>
                        <Label htmlFor="act-type" className={labelClass}>Type</Label>
                        <select
                            id="act-type"
                            className="h-9 w-full rounded-md border border-input bg-white px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
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
                            <Label htmlFor="act-start" className={labelClass}>Start time</Label>
                            <Input id="act-start" className={fieldClass} type="time" value={startTime} onChange={(e) => setStartTime(e.target.value)} />
                        </div>
                        <div>
                            <Label htmlFor="act-end" className={labelClass}>End time</Label>
                            <Input id="act-end" className={fieldClass} type="time" value={endTime} onChange={(e) => setEndTime(e.target.value)} />
                        </div>
                    </div>

                    <div>
                        <Label htmlFor="act-cost" className={labelClass}>Estimated cost</Label>
                        <Input id="act-cost" className={fieldClass} type="number" min="0" value={cost} onChange={(e) => setCost(e.target.value)} />
                    </div>

                    <div>
                        <Label htmlFor="act-location" className={labelClass}>Location</Label>
                        <Input id="act-location" className={fieldClass} value={location} onChange={(e) => setLocation(e.target.value)} />
                    </div>

                    <div>
                        <Label htmlFor="act-desc" className={labelClass}>Description</Label>
                        <Input id="act-desc" className={fieldClass} value={description} onChange={(e) => setDescription(e.target.value)} />
                    </div>

                    {formError && (
                        <p className="rounded-md border border-red-300 bg-red-50 p-2 text-sm text-red-700">{formError}</p>
                    )}
                </div>

                <DialogFooter>
                    <Button variant="outline" onClick={onClose} disabled={mutation.isPending}>
                        Cancel
                    </Button>
                    <Button
                        className="bg-orange-500 text-white hover:bg-orange-600"
                        onClick={handleSave}
                        disabled={mutation.isPending}
                    >
                        {mutation.isPending ? 'Saving...' : 'Save'}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}