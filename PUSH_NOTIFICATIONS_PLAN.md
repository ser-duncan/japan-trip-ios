# Push Notifications Plan

## Goal
Send push notifications to installed devices when app events occur:
- Research job completes (AI)
- Poller run finds new info
- New note added
- (future) any server-side event

## Prerequisites
- [ ] Apple Developer account ($99/yr) — needed for APNs auth key (p8 file)
- [ ] APNs key registered for bundle ID `com.jakeroyston.japan2026`
- [ ] VAPID key pair generated (for web push — free, one-time)

## Architecture

### 1. Supabase table: `push_subscriptions`
```sql
create table push_subscriptions (
  id uuid primary key default gen_random_uuid(),
  platform text not null,           -- 'ios' | 'web'
  -- iOS APNs:
  apns_token text,
  -- Web Push:
  endpoint text,
  p256dh text,
  auth text,
  -- meta:
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);
```

### 2. Native iOS — `@capacitor/push-notifications`
- Add to `package.json`: `@capacitor/push-notifications`
- On app launch: request permission → get APNs token → upsert to `push_subscriptions`
- `npx cap sync` then enable Push Notifications capability in Xcode

### 3. Web PWA — Web Push API (VAPID)
- Generate VAPID keys once: `npx web-push generate-vapid-keys`
- Store private key as Supabase secret (`VAPID_PRIVATE_KEY`)
- On first web visit: `Notification.requestPermission()` → `PushManager.subscribe()` → POST endpoint+keys to Supabase
- Add push event handler to `sw.js`:
  ```javascript
  self.addEventListener('push', e => {
    const data = e.data.json();
    e.waitUntil(self.registration.showNotification(data.title, {
      body: data.body, icon: './icons/icon-192.png', badge: './icons/icon-192.png'
    }));
  });
  ```

### 4. Supabase Edge Function: `notify`
Called at the end of research jobs, poller runs, etc.
```typescript
// Reads all push_subscriptions, fans out:
// - platform === 'ios'  → APNs HTTP/2 (using apns_token + p8 key)
// - platform === 'web'  → Web Push (using endpoint/p256dh/auth + VAPID keys)
```

### 5. Trigger points in existing code
- `research` edge function → call `notify` when job status → 'done'
- Poller edge function → call `notify` when new results committed
- Client-side note saves → call a lightweight `/api/notify` or direct edge function

## Notes
- iOS 16.4+ Safari supports Web Push, so a single VAPID flow covers most web users
- APNs is needed only for the native Capacitor iOS build
- Supabase secrets: `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, `APNS_KEY_ID`, `APNS_TEAM_ID`, `APNS_P8_KEY`
- Bundle ID must match exactly: `com.jakeroyston.japan2026`
