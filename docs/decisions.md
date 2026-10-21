- JWT verification: Supabase signing keys (ES256) verified via JWKS endpoint; legacy JWT secret not used.
## M4: frontend setup
- shadcn/ui uses the Radix UI library with the Nova preset.
- `frontend\.npmrc` sets `legacy-peer-deps=true` because `@hookform/resolvers` has a conflicting optional peer dependency (effect).
- Path alias `@` points to `frontend\src`.