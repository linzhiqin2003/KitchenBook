# MyWebInterpretation (iOS)

Native iOS client for the MyWeb real-time interpretation feature.

## Prereqs

1. Install Xcode (App Store).
2. Install `xcodegen` (already installed in this repo's setup):
   - `brew install xcodegen`

## Generate Xcode Project

```bash
cd ios/MyWebInterpretation
xcodegen
```

This generates `MyWebInterpretation.xcodeproj` (not committed).

## Run

1. Open `ios/MyWebInterpretation/MyWebInterpretation.xcodeproj` in Xcode.
2. Select your development team in Signing settings.
3. Run on Simulator / device.

## Backend URL

`MYWEB_API_BASE_URL` is configured per build config:

- Debug: `http://127.0.0.1:8000` (ATS relaxed)
- Release: `https://www.lzqqq.org`

You can also override in-app (Settings button).

## Segmentation (Recommended)

This app uses chunk upload + VAD-style early cut:

- Records a segment until it detects speech then sustained silence, or a max duration is reached.
- Silent-only segments are discarded (not uploaded).

Tune in Settings:

- `VAD enabled`
- `Max segment`
- `Silence`
- `Threshold (dB)`
