import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { supabase } from '@/lib/supabase'
import { useAuth } from '@/auth/useAuth'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

const scene = `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1600 900' preserveAspectRatio='xMidYMid slice'%3E%3Cdefs%3E%3ClinearGradient id='s' x1='0' y1='0' x2='0' y2='1'%3E%3Cstop offset='0' stop-color='%232b8fd9'/%3E%3Cstop offset='0.55' stop-color='%23ffc98a'/%3E%3Cstop offset='1' stop-color='%23ff9a5c'/%3E%3C/linearGradient%3E%3C/defs%3E%3Crect width='1600' height='900' fill='url(%23s)'/%3E%3Ccircle cx='1180' cy='520' r='110' fill='%23fff3c4' opacity='0.95'/%3E%3Cpath d='M0 640 L220 420 L380 560 L600 340 L840 600 L1040 470 L1300 640 L1600 480 V900 H0Z' fill='%236b8fb5' opacity='0.8'/%3E%3Cpath d='M0 720 L260 560 L480 680 L760 520 L1020 700 L1320 580 L1600 700 V900 H0Z' fill='%23356a8c'/%3E%3Crect y='780' width='1600' height='120' fill='%231f5d7a'/%3E%3C/svg%3E")`

const fieldClass = 'border-sky-300 bg-white'

const schema = z.object({
    email: z.string().email('Enter a valid email'),
    password: z.string().min(1, 'Enter your password'),
})
type FormValues = z.infer<typeof schema>

export default function LoginPage() {
    const { session } = useAuth()
    const navigate = useNavigate()
    const [serverError, setServerError] = useState<string | null>(null)
    const {
        register,
        handleSubmit,
        formState: { errors, isSubmitting },
    } = useForm<FormValues>({ resolver: zodResolver(schema) })

    if (session) return <Navigate to="/dashboard" replace />

    async function onSubmit(values: FormValues) {
        setServerError(null)
        const { error } = await supabase.auth.signInWithPassword(values)
        if (error) {
            setServerError(error.message)
            return
        }
        navigate('/dashboard', { replace: true })
    }

    return (
        <div
            className="flex min-h-screen flex-col items-center justify-center gap-6 p-4"
            style={{
                backgroundColor: '#2b8fd9',
                backgroundImage: scene,
                backgroundSize: 'cover',
                backgroundPosition: 'center',
                backgroundAttachment: 'fixed',
            }}
        >
            <div className="text-center text-white drop-shadow-lg">
                <h1 className="text-3xl font-bold tracking-wide">✈ Travel Planner</h1>
                <p className="mt-1 text-sm text-white/90">Plan your perfect trip, day by day.</p>
            </div>
            <Card className="w-full max-w-sm border-t-4 border-orange-400 bg-sky-100/60 text-sky-950 shadow-2xl ring-1 ring-white/70 backdrop-blur-sm">
                <CardHeader>
                    <CardTitle className="text-sky-900">Log in</CardTitle>
                    <CardDescription className="text-sky-800">Welcome back, traveller.</CardDescription>
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                        <div className="space-y-2">
                            <Label htmlFor="email" className="text-sky-900">Email</Label>
                            <Input id="email" type="email" autoComplete="email" className={fieldClass} {...register('email')} />
                            {errors.email && <p className="text-sm text-red-600">{errors.email.message}</p>}
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="password" className="text-sky-900">Password</Label>
                            <Input
                                id="password"
                                type="password"
                                autoComplete="current-password"
                                className={fieldClass}
                                {...register('password')}
                            />
                            {errors.password && <p className="text-sm text-red-600">{errors.password.message}</p>}
                        </div>
                        {serverError && <p className="text-sm text-red-600">{serverError}</p>}
                        <Button
                            type="submit"
                            className="w-full bg-orange-500 text-white hover:bg-orange-600"
                            disabled={isSubmitting}
                        >
                            {isSubmitting ? 'Logging in...' : 'Log in'}
                        </Button>
                        <p className="text-center text-sm text-sky-900">
                            No account?{' '}
                            <Link to="/signup" className="font-semibold text-orange-700 underline">
                                Sign up
                            </Link>
                        </p>
                    </form>
                </CardContent>
            </Card>
        </div>
    )
}