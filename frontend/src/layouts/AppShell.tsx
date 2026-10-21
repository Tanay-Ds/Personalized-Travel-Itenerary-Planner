import type { CSSProperties } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '@/auth/useAuth'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

const links = [
    { to: '/dashboard', label: 'My Trips' },
    { to: '/trips/new', label: 'Plan a Trip' },
]

const scene = `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1600 900' preserveAspectRatio='xMidYMid slice'%3E%3Cdefs%3E%3ClinearGradient id='s' x1='0' y1='0' x2='0' y2='1'%3E%3Cstop offset='0' stop-color='%232b8fd9'/%3E%3Cstop offset='0.55' stop-color='%23ffc98a'/%3E%3Cstop offset='1' stop-color='%23ff9a5c'/%3E%3C/linearGradient%3E%3C/defs%3E%3Crect width='1600' height='900' fill='url(%23s)'/%3E%3Ccircle cx='1180' cy='520' r='110' fill='%23fff3c4' opacity='0.95'/%3E%3Cpath d='M0 640 L220 420 L380 560 L600 340 L840 600 L1040 470 L1300 640 L1600 480 V900 H0Z' fill='%236b8fb5' opacity='0.8'/%3E%3Cpath d='M0 720 L260 560 L480 680 L760 520 L1020 700 L1320 580 L1600 700 V900 H0Z' fill='%23356a8c'/%3E%3Crect y='780' width='1600' height='120' fill='%231f5d7a'/%3E%3C/svg%3E")`

const themeVars = {
    '--primary': '#f97316',
    '--primary-foreground': '#ffffff',
    '--input': '#7db7e0',
} as CSSProperties

export function AppShell() {
    const { user, signOut } = useAuth()
    const navigate = useNavigate()

    async function handleSignOut() {
        await signOut()
        navigate('/login', { replace: true })
    }

    return (
        <div
            className="min-h-screen"
            style={{
                backgroundColor: '#2b8fd9',
                backgroundImage: scene,
                backgroundSize: 'cover',
                backgroundPosition: 'center',
                backgroundAttachment: 'fixed',
            }}
        >
            <header className="sticky top-0 z-10 border-b border-white/30 bg-sky-700/90 text-white shadow-md backdrop-blur">
                <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-3 px-4 py-3">
                    <div className="flex items-center gap-6">
                        <div className="text-lg font-bold tracking-wide">✈ Travel Planner</div>
                        <nav className="flex gap-2">
                            {links.map((link) => (
                                <NavLink
                                    key={link.to}
                                    to={link.to}
                                    className={({ isActive }) =>
                                        cn(
                                            'rounded-full px-4 py-1.5 text-sm transition-colors',
                                            isActive
                                                ? 'bg-orange-400 font-semibold text-white'
                                                : 'text-white/90 hover:bg-white/20',
                                        )
                                    }
                                >
                                    {link.label}
                                </NavLink>
                            ))}
                        </nav>
                    </div>
                    <div className="flex items-center gap-3">
                        <span className="hidden truncate text-sm text-white/90 sm:inline">{user?.email}</span>
                        <Button
                            size="sm"
                            className="bg-white text-sky-800 hover:bg-orange-100"
                            onClick={handleSignOut}
                        >
                            Sign out
                        </Button>
                    </div>
                </div>
            </header>

            <main className="mx-auto max-w-5xl px-4 py-6">
                <div
                    style={themeVars}
                    className="rounded-2xl border border-white/70 bg-sky-50/60 p-5 text-sky-950 shadow-xl backdrop-blur-sm md:p-8 [&_input]:border-sky-300 [&_input]:bg-white [&_select]:border-sky-300 [&_select]:bg-white [&_textarea]:border-sky-300 [&_textarea]:bg-white"
                >
                    <Outlet />
                </div>
            </main>
        </div>
    )
}