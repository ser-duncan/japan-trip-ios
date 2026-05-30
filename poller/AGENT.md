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
5b. **Save attachments** — for any email with PDF or image attachments (QR codes, ticket PDFs, confirmation docs): download each attachment, upload to Supabase Storage bucket `trip-attachments` at path `{booking_ref}/{filename}` (e.g. `BHG063551/adult-1-qr.png`), then insert a row into `trip_attachments` (see schema below). Match `booking_ref` from the email content. Skip if a row with the same `storage_path` already exists.
6. **Edit HTML** — for high-confidence changes to existing bookings, update `www/index.html` directly (see rules below)
7. **Commit & push** — if any HTML edits were made, commit and push to `main`
8. **Done** — report: `Processed N emails · M Supabase records written · K HTML fields updated · A attachments saved`

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

## HTML editing rules

Edit `www/index.html` when confidence ≥ 0.85 **and** the email contains info not already in the file.

### What to edit and where

**Flight update** (gate change, delay, cancellation, new seat assignment):
- Find the matching key in `FLIGHT_DETAILS` (match by flight number or confirmation AYCCBN)
- Add or update a row in the appropriate `rows` array, e.g.:
  ```js
  { label: 'Gate', value: 'B14 (updated Jun 3)' },
  { label: 'Status', value: '⚠️ Delayed — new departure 5:45 PM' },
  ```
- For seat changes, update the value in the `Seat Assignments` section rows

**Hotel update** (PIN code, check-in instructions, lockbox code, host message):
- Find `HOTEL_DETAILS['koala' | 'hakone' | 'kyoto' | 'osaka']` by confirmation number
- Update or add the relevant `label`/`value` row in the correct section, e.g.:
  ```js
  { label: 'PIN Code', value: '<span class="hotel-pin">8821</span>' },
  { label: 'Early check-in', value: 'Confirmed for 1:00 PM — host Miwa approved' },
  ```

**Train update** (platform, time change, new booking):
- Find `TRAIN_DETAILS['romancecar' | 'shinkansen' | 'haruka']` and update the relevant rows

**Activity update** (time change, cancellation, new booking):
- Find the event by id in `DEFAULT_DAYS` (line ~4300)
- Update the `note` field or `time` field on the matching event object
- For new booked activities: set `booked: true` and add the confirmation ref to `note`

**New booking not yet in the app**:
- For a new hotel: add a new key to `HOTEL_DETAILS` following the existing pattern
- For a new activity: add a new event object to `DEFAULT_DAYS` in the correct day array
- For a new flight/train: add to `FLIGHT_DETAILS` / `TRAIN_DETAILS`

### What NOT to edit
- Don't change PIN codes or lock codes unless you're very confident the email is from the property
- Don't edit anything with confidence < 0.85
- Don't remove existing information — only add or update
- Don't change dates, confirmation numbers, or names unless an explicit correction email

---

## Git commit step

After editing `www/index.html`:

```bash
# cd to repo root first if not already there (Mac mini only — cloud runner starts there)
git add www/index.html
git commit -m "Trip inbox: <one-line summary of what changed>

Auto-updated by poller from Gmail. Sources:
<bullet list of email subjects that triggered changes>"
git push origin main
```

Use a descriptive commit message so Jacob can review what changed in the git log.

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
