import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { api, ApiError } from '@/api/client'
import type { TripDetail } from '@/types/trip'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card } from '@/components/ui/card'

const schema = z
  .object({
    destination: z.string().min(1, 'Destination is required').max(120),
    start_date: z.string().min(1, 'Start date is required'),
    end_date: z.string().min(1, 'End date is required'),
    budget: z
      .string()
      .min(1, 'Budget is required')
      .refine((v) => !isNaN(Number(v)) && Number(v) >= 0, 'Enter a valid number'),
    currency: z.string().length(3, 'Use a 3-letter code like INR'),
    group_size: z
      .string()
      .refine((v) => Number.isInteger(Number(v)) && Number(v) >= 1 && Number(v) <= 50, 'Enter 1 to 50'),
    travel_style: z.enum(['relaxed', 'balanced', 'packed']),
    interests: z.string().optional(),
    notes: z.string().max(2000).optional(),
  })
  .refine((d) => !d.start_date || !d.end_date || d.end_date >= d.start_date, {
    message: 'End date must be on or after start date',
    path: ['end_date'],
  })
  .refine(
    (d) =>
      !d.start_date ||
      !d.end_date ||
      (new Date(d.end_date).getTime() - new Date(d.start_date).getTime()) / 86400000 <= 13,
    { message: 'A trip can be at most 14 days', path: ['end_date'] },
  )

type FormValues = z.infer<typeof schema>

const selectClass =
  'flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs outline-none focus-visible:ring-2 focus-visible:ring-ring'

export default function NewTripPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      destination: '',
      start_date: '',
      end_date: '',
      budget: '',
      currency: 'INR',
      group_size: '1',
      travel_style: 'balanced',
      interests: '',
      notes: '',
    },
  })

  const mutation = useMutation({
    mutationFn: (v: FormValues) =>
      api.post<TripDetail>('/api/trips/generate', {
        destination: v.destination,
        start_date: v.start_date,
        end_date: v.end_date,
        budget: Number(v.budget),
        currency: v.currency.toUpperCase(),
        group_size: Number(v.group_size),
        travel_style: v.travel_style,
        interests: (v.interests ?? '')
          .split(',')
          .map((s) => s.trim())
          .filter(Boolean),
        notes: v.notes?.trim() ? v.notes.trim() : null,
      }),
    onSuccess: (trip) => {
      queryClient.invalidateQueries({ queryKey: ['trips'] })
      navigate(`/trips/${trip.id}`)
    },
  })

  if (mutation.isPending) {
    return (
      <Card className="mx-auto mt-10 max-w-md p-8 text-center">
        <div className="mx-auto mb-4 h-10 w-10 animate-spin rounded-full border-4 border-muted border-t-primary" />
        <h2 className="text-xl font-semibold">Generating your itinerary...</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          The AI is planning your trip. This takes about 10 to 30 seconds. Please do not close this page.
        </p>
      </Card>
    )
  }

  const err = mutation.error
  const errorMessage = err instanceof ApiError ? err.message : err ? 'Something went wrong' : null

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="mb-6 text-2xl font-semibold">Plan a new trip</h1>
      <form onSubmit={handleSubmit((v) => mutation.mutate(v))} className="space-y-4">
        <div className="space-y-1">
          <Label htmlFor="destination">Destination</Label>
          <Input id="destination" placeholder="e.g. Jaipur, India" {...register('destination')} />
          {errors.destination && <p className="text-sm text-red-600">{errors.destination.message}</p>}
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <Label htmlFor="start_date">Start date</Label>
            <Input id="start_date" type="date" {...register('start_date')} />
            {errors.start_date && <p className="text-sm text-red-600">{errors.start_date.message}</p>}
          </div>
          <div className="space-y-1">
            <Label htmlFor="end_date">End date</Label>
            <Input id="end_date" type="date" {...register('end_date')} />
            {errors.end_date && <p className="text-sm text-red-600">{errors.end_date.message}</p>}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <Label htmlFor="budget">Total budget</Label>
            <Input id="budget" type="number" min="0" {...register('budget')} />
            {errors.budget && <p className="text-sm text-red-600">{errors.budget.message}</p>}
          </div>
          <div className="space-y-1">
            <Label htmlFor="currency">Currency</Label>
            <Input id="currency" maxLength={3} {...register('currency')} />
            {errors.currency && <p className="text-sm text-red-600">{errors.currency.message}</p>}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <Label htmlFor="group_size">Group size</Label>
            <Input id="group_size" type="number" min="1" max="50" {...register('group_size')} />
            {errors.group_size && <p className="text-sm text-red-600">{errors.group_size.message}</p>}
          </div>
          <div className="space-y-1">
            <Label htmlFor="travel_style">Travel style</Label>
            <select id="travel_style" className={selectClass} {...register('travel_style')}>
              <option value="relaxed">Relaxed</option>
              <option value="balanced">Balanced</option>
              <option value="packed">Packed</option>
            </select>
          </div>
        </div>

        <div className="space-y-1">
          <Label htmlFor="interests">Interests (comma separated)</Label>
          <Input id="interests" placeholder="history, food, shopping" {...register('interests')} />
        </div>

        <div className="space-y-1">
          <Label htmlFor="notes">Notes (optional)</Label>
          <textarea id="notes" rows={3} className={selectClass + ' h-auto py-2'} {...register('notes')} />
          {errors.notes && <p className="text-sm text-red-600">{errors.notes.message}</p>}
        </div>

        {errorMessage && (
          <p className="rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-700">{errorMessage}</p>
        )}

        <Button type="submit">Generate itinerary</Button>
      </form>
    </div>
  )
}