# IDE Changes: 006 - Admin Costs Total Spent Display

## Summary
- Updated `frontend/src/pages/Costs.tsx` to prominently display the **Total Spend Till Now** KPI card in the Admin Costs dashboard (`/admin/costs`).
- The metric directly renders `c.total_cost_usd` with 4-decimal precision (`$0.1463 USD` / `~15 cents`), highlighting live OpenAI token spend to date alongside average cost per candidate, enterprise projections, token volume, and total executed calls.
- Validated TypeScript types and production build (`tsc && vite build`), exiting code 0 with zero errors.
