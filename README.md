# Japan 2026 — iOS App

A fully offline native iOS wrapper around the Japan 2026 trip planner.

## Project structure

```
www/index.html        ← the trip planner (edit this to update content)
capacitor.config.ts   ← app name, bundle ID, Capacitor settings
ios/App/              ← Xcode project (generated, don't edit manually)
```

## To update web content

Edit `www/index.html`, then run:
```bash
npx cap sync
```
Then rebuild in Xcode.

---

## First-time build (requires Xcode)

### 1. Install Xcode
Download from the Mac App Store (~15GB). After install:
```bash
sudo xcode-select -s /Applications/Xcode.app/Contents/Developer
```

### 2. Run pod install
```bash
cd ~/documents/github/japan-trip-ios/ios/App
pod install
```

### 3. Open in Xcode
```bash
cd ~/documents/github/japan-trip-ios
npx cap open ios
```
This opens `ios/App/App.xcworkspace` in Xcode.

### 4. Set your Apple ID / Team in Xcode
- Select the `App` target in the left sidebar
- Go to **Signing & Capabilities**
- Under Team, select your Apple ID (add it via Xcode → Settings → Accounts if needed)
- Xcode will auto-generate a free provisioning profile

### 5. Connect your iPhone and run
- Plug in iPhone via USB and trust the Mac
- Select your iPhone from the device picker at the top
- Press **⌘R** to build and install
- On iPhone: Settings → General → VPN & Device Management → trust your developer certificate

That's it. The app is now fully on-device with no internet or PC required to run.

---

## Bundle ID
`com.jakeroyston.japan2026`

## To install without a cable (after first install)
Once Xcode has installed it once via USB, TestFlight or AltStore can re-sign and distribute it. For personal use, the free Apple developer account works fine — the provisioning profile lasts 7 days before needing a USB reconnect to re-sign.
