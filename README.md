# New Devin Session — iOS/macOS Shortcut

An Apple Shortcut that creates a [Devin](https://devin.ai) session from your
iPhone, iPad, or Mac: run it (or share text to it), type what Devin should
work on, and it opens the new session in your browser.

The shortcut is generated as code (`build_shortcut.py` writes the
`WFWorkflow` plist that Shortcuts.app reads) and signed with Apple's
`shortcuts` CLI so anyone can import it.

## How it works

The shortcut calls the [Devin API](https://docs.devin.ai/api-reference/v1/sessions/create-a-new-devin-session):

```
POST https://api.devin.ai/v1/sessions
Authorization: Bearer <your API key>
{"prompt": "<what you typed>"}
```

then opens the `url` from the response. Actions, in order:

1. **Comment** — setup instructions
2. **Text** — placeholder for your Devin API key
3. **Ask for Input** — "What should Devin work on?" (pre-filled when run from the share sheet)
4. **Get Contents of URL** — the POST above
5. **Get Dictionary Value** — extracts `url`
6. **If / Otherwise** — opens the session URL, or shows the raw API response on error

## Build

Requires macOS with Xcode Command Line Tools (`python3`) and Shortcuts.app
(macOS 12+). Signing with `--mode anyone` notarizes via Apple and needs
network + an iCloud-signed-in Mac.

```bash
python3 build_shortcut.py              # build + sign -> dist/New Devin Session.shortcut
python3 build_shortcut.py --no-sign    # unsigned plist only -> build/
```

## Install & setup

1. Open `dist/New Devin Session.shortcut` (double-click on macOS, or AirDrop /
   download it on iPhone) and tap **Add Shortcut**.
2. Create an API key at [app.devin.ai](https://app.devin.ai) → Settings → API Keys.
3. Edit the shortcut and paste the key into the **Text** action, replacing
   `PASTE_YOUR_DEVIN_API_KEY_HERE`.

Then run it from the Shortcuts app, Siri ("New Devin Session"), the share
sheet, a widget, or the Action Button. Your API key stays on your device —
it is only sent to `api.devin.ai`.

## Publish

The signed file in `dist/` is importable by anyone. Options:

- **GitHub**: commit `dist/New Devin Session.shortcut` (or attach it to a
  release). Users download it in Safari on iOS and open it to import.
- **iCloud link**: import the shortcut into your own Shortcuts app, then
  Share → **Copy iCloud Link**. Post the link anywhere; note you must re-share
  a new link whenever you update the shortcut.
- **[RoutineHub](https://routinehub.co)**: community shortcut gallery —
  create a listing that points at your iCloud link and bump it per release.

Never publish a build containing a real API key: keep the placeholder in
`build_shortcut.py`, and each user pastes their own key after import.
