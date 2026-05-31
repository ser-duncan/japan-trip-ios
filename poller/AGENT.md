# Japan 2026 Trip Inbox Poller

You are a background agent. Each run: scan Gmail for Japan trip travel emails, extract
any new or changed booking information, write records to Supabase, and — for
high-confidence changes — directly update `www/index.html` in this repo and push
so the app reflects the new info immediately.

---

## Trip at a glance

| | |
|---|---|
| **Dates** | May 25 – June 5, 2026 |
| **Travelers** | Jacob (owner), Diana, Brantley, Daniela, Kaiden |
| **Route** | SLC → Tokyo (4 nights) → Hakone (1 night) → Kyoto (4 nights) → Osaka (2 nights) → KIX → SLC |

---

## Already in the app — known bookings

These are hardcoded in `www/index.html`. Use confirmation numbers to match
incoming emails to the right record. Only write to Supabase / edit HTML if the
email contains **new or changed information** beyond the original confirmation.

| Type | Description | Confirmation | HTML location |
|------|-------------|--------------|---------------|
| ✈️ Flight | UA5408 SLC→LAX · May 24 · 8:00 AM | AYCCBN | `FLIGHT_DETAILS['ua5408']` · line ~5255 |
| ✈️ Flight | UA39 LAX→HND · May 24 · 11:40 AM | AYCCBN | `FLIGHT_DETAILS['ua39']` · line ~5276 |
| ✈️ Flight | UA34 KIX→SFO · Jun 5 · 4:55 PM | AYCCBN | `FLIGHT_DETAILS['ua34']` · line ~5300 |
| ✈️ Flight | UA2017 SFO→SLC · Jun 5 · 1:50 PM | AYCCBN | `FLIGHT_DETAILS['ua2017']` · line ~5322 |
| 🏨 Hotel | KOALA BLDG. SHINJUKU · May 25–29 | HMBQZPZ3QA | `HOTEL_DETAILS['koala']` · line ~3751 |
| 🏨 Hotel | 箱根 Villa (Hakone) · May 29–30 | HMMAPSFSTQ | `HOTEL_DETAILS['hakone']` · line ~3800 |
| 🏨 Hotel | 515 Yamadachō (Kyoto machiya) · May 30–Jun 3 | HMQ2MS55BF | `HOTEL_DETAILS['kyoto']` · line ~3837 |
| 🏨 Hotel | Lien de premier (Osaka) · Jun 3–5 | HMR98ZMTST | `HOTEL_DETAILS['osaka']` · line ~3867 |
| 🚄 Train | Romancecar Hakone 3 · Shinjuku→Hakone-Yumoto · May 29 10:00 AM | EMot (no ref) | `TRAIN_DETAILS['romancecar']` · line ~3909 |
| 🚄 Train | Shinkansen · Odawara→Kyoto · May 30 1:15 PM | BHG063551 (Klook) | `TRAIN_DETAILS['shinkansen']` · line ~3983 |
| 🚄 Train | HARUKA 25 · Tennoji→KIX · Jun 5 12:47 PM | YMB549238 (Klook) | `TRAIN_DETAILS['haruka']` · line ~4060 |
| 🎯 Activity | teamLab Planets TOKYO · May 27 | ABT743615 (Klook) | `DEFAULT_DAYS` itinerary, event `d3e1` · line ~4328 |
| 🎯 Activity | Shibuya Sky · May 27 · 7:40 PM | RBA473737 (Klook) | `DEFAULT_DAYS` itinerary, event `d3e5` · line ~4332 |

---

## Run checklist (execute in order)

1. **Search Gmail** — use the query below with a fixed `after:` date covering the full trip window, limit 50 results. Deduplication via `email_processing_log` prevents re-processing old messages.
2. **Deduplicate** — for each message, check `email_processing_log` in Supabase; skip if `gmail_message_id` already exists
3. **Classify** — read subject + body; determine category and whether it contains new info
4. **Extract** — pull structured data per the schemas below
5. **Write Supabase** — **CRITICAL: insert into `email_processing_log` for EVERY email processed, regardless of category or outcome (including skips and actionable items alike).** This is how deduplication works — if you skip this step, the same email will be re-processed on the next run. Then insert into `travel_updates` for actionable items only (confidence ≥ 0.50).
6. **Write booking_updates** — for high-confidence changes (≥ 0.85), upsert rows into `booking_updates` (see schema below). The app reads this table live — no HTML editing needed.
7. **Write itinerary_events** — for dated reservations/experiences (specific day + time), upsert rows into `itinerary_events`. The app merges these into the day view on load — no HTML editing needed.
7b. **Write trip_activities** — for new activity recommendations or corrections without a specific date (e.g. a newly booked tour with no confirmed slot yet, or an update to an existing activity card), upsert rows into `trip_activities` (see schema below). Appears in the Eat + Do → Activities tab.
8. **Process poller_tasks** — check for pending one-off tasks (see schema below). On each run, query for `status = 'pending'` tasks, process up to 3 per run (to avoid timeout), mark each `done` or `failed`. Common tasks: `upload_food_photos` — download a restaurant photo and upload to Supabase Storage.
9. **Commit & push** — almost never needed now; only if something genuinely can't be expressed via `booking_updates` or `itinerary_events`.
10. **Log the run** — INSERT one row into `poller_runs` (see schema below). This is what drives the Poller tab and "Last checked" timestamp in the app UI. Do this even if nothing actionable was found.
11. **Done** — report: `Processed N emails · M actionable · K booking_updates upserted · J itinerary_events upserted · A attachments saved · P tasks completed`

---

## Gmail search query

```
after:2026/05/23 (japan OR tokyo OR kyoto OR osaka OR hakone OR booking OR reservation OR confirmation OR flight OR hotel OR airbnb OR klook OR viator OR united OR shinkansen OR haruka OR "JR pass" OR from:jacob.royston1@gmail.com OR from:express@airbnb.com OR from:automated@airbnb.com OR from:support-noreply@klook.com OR from:do-not-reply@notification.getyourguide.com OR from:booking@klook.com)
```

**Why `after:` instead of `newer_than:`:** The fixed date (one day before trip start) ensures every trip-related email from the full May 25 – June 5 window is always in scope, regardless of when the poller runs. The limit is 50 results; deduplication via `email_processing_log` keeps re-processing cost at zero.

---

## Categories

| Category | Examples |
|----------|---------|
| `flight` | Gate assignments, delays, cancellations, seat upgrades, check-in reminders with new info |
| `hotel` | Check-in instructions, PIN/lockbox codes, early check-in confirmed, cancellations, host messages |
| `train` | New bookings, platform/time changes, cancellations |
| `activity` | New bookings, venue changes, weather cancellations, time changes |
| `skip` | Newsletters, marketing, re-sends of original confirmations with zero new info |

---

## booking_updates — data-driven modal overlay (NEW)

**Do NOT edit `www/index.html` for booking changes anymore.**
Instead, write to the `booking_updates` Supabase table. The app reads this table every time a
modal is opened and overlays the data on top of the base hardcoded info.

### Table: `booking_updates`

| Column | Type | Description |
|--------|------|-------------|
| `item_key` | text | Key matching the JS object: `koala`, `hakone`, `kyoto`, `osaka`, `romancecar`, `shinkansen`, `kyoto-osaka`, `haruka`, `ua5408`, `ua39`, `ua34`, `ua2017` |
| `category` | text | `hotel`, `train`, `flight`, or `activity` |
| `booking_ref` | text | Confirmation number (optional but useful) |
| `section` | text | Section title exactly as shown in the modal (e.g. `"Key Box Entry"`, `"Seat Assignments"`, `"Journey"`) |
| `section_sort` | int | Order of section within the modal (0 = first). New sections go after base sections. |
| `label` | text | Row label (e.g. `"PIN Code"`, `"Gate"`, `"Jacob"`) |
| `value` | text | Raw value — see `value_type` for formatting |
| `value_type` | text | See types below |
| `row_sort` | int | Order of this row within the section |
| `source` | text | `"poller"` |
| `confidence` | numeric | 0.00–1.00 |
| `notes` | text | Human-readable notes (not shown in app) |
| `source_email_id` | text | gmail_message_id that triggered this update |

**UNIQUE constraint:** `(item_key, section, label)` — use ON CONFLICT DO UPDATE to upsert.

### value_type options

| Type | App rendering | Use for |
|------|--------------|---------|
| `text` | plain string | Most values, descriptions, notes |
| `pin` | large monospace blue badge | Door PINs, lock codes, access codes |
| `wifi_password` | large monospace blue badge | WiFi passwords |
| `conf_code` | small monospace blue badge | Confirmation/booking refs |
| `seat` | small green monospace badge | Seat assignments |
| `status_ok` | green "✓ value" | Confirmed status, good news |
| `status_warn` | amber "⚠ value" | Delays, warnings, tentative info |
| `phone` | clickable tel: link | Phone numbers |
| `link` | clickable hyperlink | URLs — format as `"Label|https://url"` or just `"https://url"` |
| `html` | raw HTML injected | Complex formatting (use sparingly) |

### Upsert SQL template

```sql
INSERT INTO booking_updates
  (item_key, category, booking_ref, section, section_sort, label, value, value_type,
   row_sort, source, confidence, notes, source_email_id)
VALUES
  ($item_key, $category, $booking_ref, $section, $section_sort, $label, $value, $value_type,
   $row_sort, 'poller', $confidence, $notes, $gmail_message_id)
ON CONFLICT (item_key, section, label) DO UPDATE SET
  value           = EXCLUDED.value,
  value_type      = EXCLUDED.value_type,
  confidence      = EXCLUDED.confidence,
  notes           = EXCLUDED.notes,
  source_email_id = EXCLUDED.source_email_id,
  updated_at      = now();
```

### Examples by category

**Hotel — PIN code or access code:**
```sql
-- item_key matches hotel key; section = descriptive name; label = field name
('kyoto', 'hotel', 'HMQ2MS55BF', 'Entrance Door', 0, 'PIN Code', '5847', 'pin', 0, ...)
('hakone','hotel','HMMAPSFSTQ','Key Box Entry', 0, 'Key Box PIN','2493','pin', 0, ...)
```

**Hotel — WiFi:**
```sql
('hakone','hotel','HMMAPSFSTQ','WiFi', 1, 'Network',  'GolfVilla', 'text',         0, ...)
('hakone','hotel','HMMAPSFSTQ','WiFi', 1, 'Password', 'par5eagle', 'wifi_password', 1, ...)
```

**Hotel — early check-in, host message, instructions:**
```sql
('koala','hotel','HMBQZPZ3QA','Check-in', 0, 'Early check-in', 'Confirmed for 1:00 PM — host Miwa approved', 'status_ok', 0, ...)
```

**Flight — gate change:**
```sql
('ua39','flight','AYCCBN','Departure', 0, 'Gate', 'C18 (updated May 24)', 'text', 2, ...)
```

**Flight — delay:**
```sql
('ua39','flight','AYCCBN','Departure', 0, 'Status', 'Delayed — new departure 1:15 PM', 'status_warn', 3, ...)
```

**Train — platform or time update:**
```sql
('shinkansen','train','BHG063551','Journey', 0, 'Departs', '12:07 PM — Odawara (Platform 13*)', 'text', 1, ...)
```

**Train — seat assignments (one row per traveler):**
```sql
('shinkansen','train','BHG063551','Seat Assignments', 2, 'Jacob',   'Car 6 · Seat 14-A', 'seat', 0, ...)
('shinkansen','train','BHG063551','Seat Assignments', 2, 'Diana',   'Car 6 · Seat 14-B', 'seat', 1, ...)
('shinkansen','train','BHG063551','Seat Assignments', 2, 'Brantley','Car 6 · Seat 15-A', 'seat', 2, ...)
('shinkansen','train','BHG063551','Seat Assignments', 2, 'Daniela', 'Car 6 · Seat 15-B', 'seat', 3, ...)
('shinkansen','train','BHG063551','Seat Assignments', 2, 'Kaiden',  'Car 6 · Seat 16-A', 'seat', 4, ...)
```

### Rules for booking_updates writes

- Only write when confidence ≥ 0.85 (same threshold as before, but now it's a DB write, not HTML edit)
- Never delete rows — only upsert (the UNIQUE conflict ensures idempotent updates)
- The `section` title must match an existing section in the modal OR be a new descriptive section name
- For new sections not in the base data, choose a clear title and pick a `section_sort` > 10 so they append after base sections
- `notes` field is for your own audit trail — include the email subject or key fact

### No more HTML edits

**Do not edit `www/index.html` for dynamic data.** The git commit step is almost never needed now — use `booking_updates` for existing booking details and `itinerary_events` for new day-view items.

---

## itinerary_events — data-driven day-view items (NEW)

New activities, reservations, or free-time blocks that aren't already in the hardcoded itinerary should be inserted into `itinerary_events`. The app fetches this table on load and merges the rows into the matching day, so no HTML deploy is required.

### Table: `itinerary_events`

| Column | Type | Description |
|--------|------|-------------|
| `day_date` | date | ISO date of the day this event belongs to (e.g. `2026-05-27`) |
| `event_id` | text UNIQUE | Stable identifier — use pattern `{date}-{slug}`, e.g. `2026-05-27-teamlab` |
| `type` | text | Event type for icon/color: `activity`, `food`, `transport`, `hotel`, `free`, `note` |
| `time` | text | Display time string, e.g. `"10:00 AM"` — null for all-day items |
| `text` | text | Main display text (event name or description) |
| `note` | text | Optional sub-label shown below text (e.g. `"Klook · ABT743615"`) |
| `booked` | boolean | Show booked badge — true when a confirmation exists |
| `highlight` | boolean | Highlight in the UI — true for marquee experiences |
| `sort_order` | integer | Position within the day (0-based). New events should use a high number (e.g. 99) to append after existing ones, or a specific index to insert in order. |
| `source` | text | `"poller"` |
| `confidence` | numeric | 0.00–1.00 |
| `source_email_id` | text | gmail_message_id that triggered this |

**UNIQUE constraint:** `event_id` — use ON CONFLICT DO UPDATE to upsert.

### event_id naming convention

```
{YYYY-MM-DD}-{lowercase-slug}
```

Examples:
- `2026-05-27-teamlab` — teamLab Planets on May 27
- `2026-05-28-tsukiji-breakfast` — Tsukiji market breakfast May 28
- `2026-06-01-nishiki-market` — Nishiki market walk June 1
- `2026-06-03-dotonbori-dinner` — Dotonbori dinner June 3

### Upsert SQL template

```sql
INSERT INTO itinerary_events
  (day_date, event_id, type, time, text, note, booked, highlight, sort_order,
   source, confidence, source_email_id)
VALUES
  ($day_date, $event_id, $type, $time, $text, $note, $booked, $highlight, $sort_order,
   'poller', $confidence, $gmail_message_id)
ON CONFLICT (event_id) DO UPDATE SET
  day_date        = EXCLUDED.day_date,
  type            = EXCLUDED.type,
  time            = EXCLUDED.time,
  text            = EXCLUDED.text,
  note            = EXCLUDED.note,
  booked          = EXCLUDED.booked,
  highlight       = EXCLUDED.highlight,
  sort_order      = EXCLUDED.sort_order,
  confidence      = EXCLUDED.confidence,
  source_email_id = EXCLUDED.source_email_id,
  updated_at      = now();
```

### type values

| type | When to use |
|------|-------------|
| `activity` | Paid experience, attraction, tour, show |
| `food` | Restaurant reservation, market visit, food experience |
| `transport` | Local transit, taxi, bus — not trains (those go in `booking_updates`) |
| `hotel` | Check-in / check-out reminder |
| `free` | Unstructured free time block |
| `note` | Informational note, reminder, or tip |

### Examples

**New activity booking (from Klook/Viator confirmation):**
```sql
('2026-05-28', '2026-05-28-senso-ji-tour', 'activity', '9:00 AM',
 'Senso-ji Temple Morning Tour', 'Klook · KLK123456', true, true, 99,
 'poller', 0.95, 'gmail_msg_id_here')
```

**Restaurant reservation:**
```sql
('2026-05-31', '2026-05-31-nishiki-lunch', 'food', '12:30 PM',
 'Lunch at Nishiki Market', 'Reservation confirmed', true, false, 99,
 'poller', 0.92, 'gmail_msg_id_here')
```

**Informational note (no booking):**
```sql
('2026-06-01', '2026-06-01-arashiyama-tip', 'note', null,
 'Arashiyama: arrive before 8 AM to beat crowds', null, false, false, 99,
 'poller', 0.80, 'gmail_msg_id_here')
```

### Rules for itinerary_events writes

- Only write when confidence ≥ 0.85
- Never create a duplicate of a hardcoded event — check `DEFAULT_DAYS` in `www/index.html` for existing event_ids before inserting
- Use `sort_order: 99` (append) unless the email clearly implies a specific time that places it before another event
- The app preserves the user's `done` checkbox state when updating existing events
- Existing hardcoded events (e.g. `d3e1`, `d3e5`) will be updated in-place if you use their exact `event_id`

---

## trip_activities — dynamic activity list (poller-managed)

Activities in the app's **Eat + Do → Activities** tab come from two sources, merged on load:
1. `DEFAULT_ACTIVITIES` — hardcoded JS array (baseline, always available offline)
2. `trip_activities` table — poller-written rows that **override or supplement** the defaults

Use this table to: add newly booked activities, correct an existing activity's name/note/type, or add a new recommendation discovered in an email (e.g. a restaurant booking that includes an activity add-on).

### Table: `trip_activities`

| Column | Type | Description |
|--------|------|-------------|
| `id` | text PK | Stable ID — use existing IDs to update defaults (e.g. `a4`, `komehyo`) or a new slug for new items (e.g. `2026-05-28-teamlab-extra`) |
| `name` | text | Activity name as shown in the card |
| `note` | text | Sub-label — hours, price, short tip. Null = clear existing note |
| `type` | text | `must`, `optional`, `food`, `shopping`, `cultural`, `included` |
| `city` | text | `tokyo`, `hakone`, `kyoto`, `osaka` |
| `assigned_day` | text | Day ID the user has planned this to (e.g. `d6`). Poller should leave this null — it's user-controlled. |
| `sort_order` | int | Within-city display order. Use 100+ for new items (append after defaults). |
| `source` | text | Always `'poller'` |
| `created_at` | timestamptz | Auto-set |
| `updated_at` | timestamptz | Auto-updated on every UPDATE |

### Merge behaviour in the app

- **Existing ID** (e.g. `a4`, `komehyo`): updates `name`, `note`, `type`. Preserves the user's `assignedDay` planning state.
- **New ID**: appends as a new activity card at the bottom of the city's list (ordered by `sort_order`).

### Upsert SQL template

```sql
INSERT INTO trip_activities (id, name, note, type, city, sort_order, source)
VALUES ($id, $name, $note, $type, $city, $sort_order, 'poller')
ON CONFLICT (id) DO UPDATE SET
  name       = EXCLUDED.name,
  note       = EXCLUDED.note,
  type       = EXCLUDED.type,
  city       = EXCLUDED.city,
  sort_order = EXCLUDED.sort_order,
  updated_at = now();
```

### Examples

**New activity booking from email (Klook/Viator confirmation):**
```sql
-- New Kyoto tea ceremony booked via Viator
INSERT INTO trip_activities (id, name, note, type, city, sort_order, source)
VALUES ('2026-05-31-tea-ceremony', 'Tea Ceremony at Urasenke', 'Booked via Viator · May 31 2:00 PM · 5 persons', 'cultural', 'kyoto', 50, 'poller')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, note = EXCLUDED.note, updated_at = now();
```

**Update an existing default activity:**
```sql
-- Correct the teamLab booking note with confirmed time
INSERT INTO trip_activities (id, name, note, type, city, sort_order, source)
VALUES ('a4', 'teamLab Planets TOKYO', 'Klook ABT743615 · May 28 10:00 AM · 5 persons · Barefoot required', 'optional', 'tokyo', 4, 'poller')
ON CONFLICT (id) DO UPDATE SET note = EXCLUDED.note, updated_at = now();
```

**New food experience (not in food guide):**
```sql
INSERT INTO trip_activities (id, name, note, type, city, sort_order, source)
VALUES ('2026-06-03-kuromon-market', 'Kuromon Ichiba Market', 'Osaka''s kitchen · fresh seafood · open 9 AM–6 PM', 'food', 'osaka', 110, 'poller')
ON CONFLICT (id) DO UPDATE SET note = EXCLUDED.note, updated_at = now();
```

### Rules for trip_activities writes

- Only write when you have a confirmed booking or high-confidence (≥ 0.85) new information
- Never set `assigned_day` — that's user-controlled state
- Use existing DEFAULT_ACTIVITIES IDs (`a0`–`a29`, `komehyo`, `brandoff`, `2ndstreet`, `decouverte`, `naramonocho`) when updating defaults
- Use `{YYYY-MM-DD}-{slug}` IDs for new poller-added activities
- Update the run checklist counter: count trip_activities upserts in `supabase_rows_written`

---

## Supabase write schema

**Project:** `ubtzeulovzfguazmdchp` · `https://ubtzeulovzfguazmdchp.supabase.co`
**Use:** Supabase MCP `execute_sql` tool

### poller_runs (one row per run — REQUIRED, drives the app UI)

Insert this **at the end of every run**, whether or not anything actionable was found. This is what populates the Poller tab run history and the "Last checked" timestamp in the Trip Inbox.

```sql
INSERT INTO poller_runs
  (gmail_query, emails_found, emails_deduped, emails_skipped, emails_actionable,
   supabase_rows_written, booking_updates_upserted, itinerary_events_upserted,
   attachments_saved, committed, commit_sha, summary, notes)
VALUES
  ($gmail_query, $emails_found, $emails_deduped, $emails_skipped, $emails_actionable,
   $supabase_rows_written, $booking_updates_upserted, $itinerary_events_upserted,
   $attachments_saved, $committed, $commit_sha, $summary, $notes);
```

| Column | What to put |
|--------|-------------|
| `gmail_query` | The exact query string used (copy from the Gmail search query section) |
| `emails_found` | Total threads returned by Gmail |
| `emails_deduped` | Threads already in `email_processing_log` (skipped immediately) |
| `emails_skipped` | Threads classified as `skip` after reading |
| `emails_actionable` | Threads that produced a write to `booking_updates` or `itinerary_events` |
| `supabase_rows_written` | Total rows inserted/upserted across all tables (excluding `poller_runs` itself) |
| `booking_updates_upserted` | Rows upserted into `booking_updates` |
| `itinerary_events_upserted` | Rows upserted into `itinerary_events` |
| `attachments_saved` | Files uploaded to Supabase Storage |
| `committed` | `true` only if a git commit was pushed this run |
| `commit_sha` | SHA of that commit, or `null` |
| `summary` | One or two sentences describing what this run found/did — shown in the Poller tab UI |
| `notes` | Optional extra detail (multi-line ok) — shown expanded in the UI |

**`summary` writing guide:** Be specific and scannable. Good examples:
- `"No new travel info — 33 emails already processed."`
- `"Shinkansen seats confirmed (Car 6, all 5 travelers) + Kyoto door PIN 5847 written."`
- `"Hakone key box PIN 2493 + WiFi added. Haruka platform 15 updated."`

---

### email_processing_log (every processed email, including skips)

```sql
INSERT INTO email_processing_log
  (gmail_message_id, subject, from_address, category, confidence, skip_reason, raw_extraction)
VALUES ($1, $2, $3, $4, $5, $6, $7);
```

### travel_updates (actionable items only — not skips)

```sql
INSERT INTO travel_updates
  (category, confidence, title, data, applied, flagged, source_email_id)
VALUES ($1, $2, $3, $4, $applied, $flagged, $source_id);
```

- `applied = true` when confidence ≥ 0.80
- `applied = false, flagged = true` when confidence < 0.80

### trip_attachments (PDF/image attachments from booking emails)

Upload file to Supabase Storage bucket `trip-attachments` first, then insert:

```sql
INSERT INTO trip_attachments
  (booking_ref, category, label, filename, storage_path, mime_type, source_email_id)
VALUES ($1, $2, $3, $4, $5, $6, $7)
ON CONFLICT DO NOTHING;
```

- `booking_ref`: the confirmation number the attachment belongs to (e.g. `BHG063551`)
- `category`: same as the email category (`train`, `flight`, `hotel`, `activity`)
- `label`: human-readable label, e.g. `Adult 1 — Car 6 Seat 14-A`, `Check-in Instructions`
- `filename`: original filename (e.g. `qr-adult-1.png`)
- `storage_path`: path within the bucket — always `{booking_ref}/{filename}` (e.g. `BHG063551/qr-adult-1.png`)
- `mime_type`: `image/png`, `image/jpeg`, `application/pdf`, etc.
- `source_email_id`: the `gmail_message_id`

**Storage upload:** Use Supabase MCP storage tools or the REST API:
`PUT https://ubtzeulovzfguazmdchp.supabase.co/storage/v1/object/trip-attachments/{storage_path}`

---

### poller_tasks — one-off task queue

Check this table on **every run** (step 8 in the run checklist). Process up to 3 pending tasks per run.

```sql
-- Fetch pending tasks
SELECT id, task_type, item_key, payload FROM poller_tasks WHERE status = 'pending' ORDER BY created_at ASC LIMIT 3;
```

| Column | Description |
|--------|-------------|
| `id` | Auto-increment primary key |
| `task_type` | Category of task — e.g. `upload_food_photos` |
| `item_key` | Target item — e.g. `gion-ramen` |
| `status` | `pending` → `in_progress` → `done` \| `failed` |
| `payload` | JSON with task context (restaurant name, booking_ref, notes) |
| `started_at` | Timestamp when processing began |
| `completed_at` | Timestamp when finished |
| `error` | Error message if `failed` |

**Mark in-progress before starting** (prevents duplicate processing across runs):
```sql
UPDATE poller_tasks SET status = 'in_progress', started_at = now() WHERE id = $id;
```

**Mark done after success:**
```sql
UPDATE poller_tasks SET status = 'done', completed_at = now() WHERE id = $id;
```

**Mark failed if an error occurred:**
```sql
UPDATE poller_tasks SET status = 'failed', completed_at = now(), error = $error_message WHERE id = $id;
```

#### Task type: `upload_food_photos`

Download 1–3 representative photos for the restaurant and upload to Supabase Storage. Use the `booking_ref` from `payload` to construct the storage path.

1. Find a publicly accessible photo of the restaurant or a signature dish (restaurant website > Google Maps photos > Instagram)
2. Upload each photo: `PUT https://ubtzeulovzfguazmdchp.supabase.co/storage/v1/object/trip-attachments/{booking_ref}/{timestamp}-{filename}`
3. Insert a row into `trip_attachments` (see `food_photos` section below)
4. After all photos uploaded, mark task `done`

If the restaurant website blocks download, try the restaurant's Google Business listing, their official Instagram, or food blogs — always use directly downloadable public URLs. If no accessible photos can be found after 2-3 attempts, mark the task `failed` with `error = 'No publicly downloadable images found'`.

---

### food_photos — restaurant dish images shown in the food detail modal

The app's food detail cards (e.g. Gion Soy Milk Ramen, Sugarhill Kyoto) have a **Documents / Photos tab** that pulls from `trip_attachments` using `booking_ref = 'food-{key}'`. Uploading photos here is a **one-time enrichment task**, not triggered by emails — run it on any poller run where you have spare context.

#### Key mapping (booking_ref → food item)

| booking_ref | Restaurant |
|-------------|-----------|
| `food-toshoan` | Toshoan (登志庵) |
| `food-waco-crepes` | waco crepes |
| `food-teuchi-soba` | Teuchi Toru Soba |
| `food-gion-ramen` | Gion Soy Milk Ramen |
| `food-choice-kyoto` | CHOICE (チョイス) |
| `food-ikkakuju` | Ikkakuju Karasuma |
| `food-sugarhill` | Sugarhill Kyoto |
| `food-kappa-italian` | Oshokuya Kappa (5Kappa) |
| `food-musubi-sweets` | Musubi Sweets Factory |
| `food-maccha-house` | MACCHA HOUSE |
| `food-gen-kyoto` | Gen (玄gen) Takeout |

#### How to upload a food photo

1. **Download** the image from the restaurant's website, Instagram, or Google Maps (must be publicly accessible)
2. **Upload** to Supabase Storage:
   ```
   PUT https://ubtzeulovzfguazmdchp.supabase.co/storage/v1/object/trip-attachments/food-{key}/{timestamp}-{filename}
   Headers: apikey: {SUPA_ANON}, Authorization: Bearer {SUPA_ANON}, Content-Type: image/jpeg, x-upsert: true
   ```
3. **Insert** into `trip_attachments`:
   ```sql
   INSERT INTO trip_attachments
     (booking_ref, category, label, filename, storage_path, mime_type, source_email_id)
   VALUES
     ('food-gion-ramen', 'food', 'Soy milk ramen', 'ramen.jpg',
      'food-gion-ramen/ramen.jpg', 'image/jpeg', null)
   ON CONFLICT DO NOTHING;
   ```

#### Photo guidelines

- **Label**: short, descriptive — e.g. `"Soy milk ramen"`, `"GF gyoza"`, `"Matcha tofu cheesecake"`, `"Exterior"`, `"Menu"`
- **1–3 photos per restaurant** is plenty — hero dish + maybe exterior or menu
- **Source priority**: restaurant's own website > Google Maps photos > Instagram posts by the restaurant account
- **Only use images you can directly download** — do not hotlink from TripAdvisor/Google (they expire and block)
- **category**: always `'food'` for these entries, `source_email_id`: `null`

---

## data JSON shape per category

**flight**
```json
{
  "flight_number": "UA39",
  "from": "LAX", "to": "HND",
  "date": "2026-05-24",
  "departure": "11:40 AM", "arrival": "3:05 PM+1",
  "confirmation": "AYCCBN",
  "seats": [{"name": "Jacob", "seat": "59D"}],
  "status": "confirmed | cancelled | delayed | gate_change",
  "change_note": "Gate changed from B12 to C4"
}
```

**hotel**
```json
{
  "name": "KOALA BLDG. SHINJUKU",
  "city": "Tokyo",
  "check_in": "2026-05-25", "check_out": "2026-05-29",
  "confirmation": "HMBQZPZ3QA",
  "pin_code": "7634",
  "status": "confirmed | cancelled | modified",
  "change_note": "Host confirmed early check-in at 1:00 PM"
}
```

**train**
```json
{
  "train_name": "HARUKA 25",
  "from": "Tennoji", "to": "KIX",
  "date": "2026-06-05",
  "departure": "12:47 PM", "arrival": "1:20 PM",
  "confirmation": "YMB549238",
  "status": "confirmed | cancelled",
  "change_note": null
}
```

**activity**
```json
{
  "name": "teamLab Planets TOKYO",
  "city": "Tokyo",
  "date": "2026-05-27",
  "time": "10:00 AM",
  "confirmation": "ABT743615",
  "status": "confirmed | cancelled | rescheduled",
  "change_note": null
}
```

---

## Rules

- **Only extract what's in the email** — never infer or hallucinate details
- **Dates must be ISO 8601** (YYYY-MM-DD)
- **Prefer precision over recall** — skip ambiguous emails rather than write bad data
- **One Supabase record per booking event** — one email with two flight updates = two rows
- **HTML edits are additive** — never delete existing data, only add or update values
- **Confidence < 0.85 = Supabase only** — inbox sheet surfaces it for human review, no HTML edit
