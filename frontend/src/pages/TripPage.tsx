import { useParams } from 'react-router-dom'

export default function TripPage() {
  const { tripId } = useParams()
  return <h1 className="text-2xl font-semibold">Trip {tripId} (built in M7)</h1>
}