# Server Room Monitor

A lightweight frontend for monitoring server room telemetry. The app provides a login page and a dashboard that reads recent telemetry from Supabase and displays live status cards for temperature, humidity, gas/smoke, power source, and alarm state.

## Features

- Login screen backed by Supabase Auth
- Dashboard with latest telemetry summary
- Recent telemetry table showing the last 20 rows
- Auto-refresh every 5 seconds
- Responsive layout for desktop and mobile

## Project Structure

- `login.html`: Sign-in page
- `dashboard.html`: Monitoring dashboard
- `app.js`: Shared login and dashboard logic
- `styles.css`: Shared styling for both pages
- `login-bg.jpg`: Background image for the login page
- `dashboard-bg.jpg`: Background image for the dashboard

## Requirements

- A Supabase project
- A Supabase auth user account for login
- A `telemetry` table exposed through the Supabase REST API

## Supabase Configuration

The frontend reads its configuration directly from `app.js`.

Update these values in `app.js` if you need to point the app to a different Supabase project:

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `REFRESH_MS`

The dashboard expects telemetry rows with fields used in the UI, including:

- `created_at`
- `temperature_c`
- `humidity_pct`
- `gas_alert`
- `grid_present`
- `power_source`
- `alarm_active`

## Running Locally

This project is a static frontend, so you can run it with any simple local server.

Example using VS Code Live Server:

1. Open the `server__room_monitor` folder in VS Code.
2. Start Live Server from `login.html`.
3. Sign in with a valid Supabase user account.

If you prefer Python:

```bash
python -m http.server 8080
```

Then open:

- `http://localhost:8080/login.html`

## Notes

- Session data is stored in `localStorage` under `sb_session`.
- `DEV_BYPASS_AUTH` in `app.js` can be set to `true` for local dashboard testing without login.
- This repo currently contains only the frontend subproject.

## Repository

GitHub repo: <https://github.com/ANDREAASTON/server_room_monitor123>

