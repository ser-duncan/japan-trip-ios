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

1. **Search Gmail** — use the query below, `newer_than:3d`, limit 25 results
2. **Deduplicate** — for each message, check `email_processing_log` in Supabase; skip if `gmail_message_id` already exists
3. **Classify** — read subject + body; determine category and whether it contains new info
4. **Extract** — pull structured data per the schemas below
5. **Write Supabase** — **CRITICAL: insert into `email_processing_log` for EVERY email processed, regardless of category or outcome (including skips and actionable items alike).** This is how deduplication works — if you skip this step, the same email will be re-processed on the next run. Then insert into `travel_updates` for actionable items only (confidence ≥ 0.50).
6. **Write booking_updates** — for high-confidence changes (≥ 0.85), upsert rows into `booking_updates` (see schema below). The app reads this table live — no HTML editing needed.
7. **Commit & push** — only if structural HTML changes were made (new hardcoded itinerary items). Skip this step for data-only updates.
8. **Done** — report: `Processed N emails · M Supabase records written · K booking_updates upserted · A attachments saved`

---

## Gmail search query

```
newer_than:3d (japan OR tokyo OR kyoto OR osaka OR hakone OR booking OR reservation OR confirmation OR flight OR hotel OR klook OR viator OR airbnb OR united OR shinkansen OR haruka OR JR pass)
```

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

**Do not edit `www/index.html` for dynamic data.** The git commit step below is only needed for
structural changes (new itinerary items, entirely new bookings not yet in the file at all).

---

## Supabase write schema

**Project:** `ubtzeulovzfguazmdchp` · `https://ubtzeulovzfguazmdchp.supabase.co`
**Use:** Supabase MCP `execute_sql` tool

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
