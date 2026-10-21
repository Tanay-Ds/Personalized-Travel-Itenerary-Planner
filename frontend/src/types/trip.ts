export type Activity = {
  id: string
  day_id: string
  position: number
  type: 'attraction' | 'meal' | 'stay' | 'transport' | 'other'
  title: string
  description: string | null
  location_name: string | null
  start_time: string | null
  end_time: string | null
  estimated_cost: number
  notes: string | null
}

export type Day = {
  id: string
  trip_id: string
  day_number: number
  date: string | null
  summary: string | null
  estimated_cost: number
  activities: Activity[]
}

export type Trip = {
  id: string
  title: string | null
  destination: string
  start_date: string
  end_date: string
  budget: number | null
  currency: string
  group_size: number
  travel_style: 'relaxed' | 'balanced' | 'packed'
  interests: string[]
  notes: string | null
  status: 'generating' | 'ready' | 'failed'
  total_estimated_cost: number
}

export type TripDetail = Trip & { days: Day[] }