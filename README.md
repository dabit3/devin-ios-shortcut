# New Devin Cloud Agent Session (iOS/macOS Shortcut)

A shortcut for Apple's built-in [Shortcuts app](https://support.apple.com/guide/shortcuts/welcome/ios)
(preinstalled on iPhone, iPad, and Mac, so there is nothing else to install)
that creates a [Devin](https://devin.ai) session: run it (or share text to
it), type what Devin should work on, and Devin gets to work. A menu then
lets you open the session in your browser, copy its link, or just move on.

## Install

**[Download New Devin Session.shortcut](https://github.com/dabit3/devin-ios-shortcut/raw/main/dist/New%20Devin%20Session.shortcut)**

1. Open the downloaded file (from Safari's downloads or the Files app on
   iOS; double-click on macOS). The Shortcuts app opens a preview of the
   shortcut's actions. Tap **Add Shortcut** at the bottom of that screen
   to add it to your library. The file is signed and notarized by Apple,
   so it imports on any device (iOS 15+ / macOS 12+).
2. Create a personal API key (`apk_user_...`) at
   [app.devin.ai/settings/api-keys](https://app.devin.ai/settings/api-keys).
   No org ID is needed: the shortcut uses the [v1 API](https://docs.devin.ai/api-reference/v1/sessions/create-a-new-devin-session),
   which identifies you (and your org) from the key itself.
3. Edit the shortcut and paste the key into the **Text** action, replacing
   `PASTE_YOUR_DEVIN_API_KEY_HERE`.

Then run it from the Shortcuts app, Siri ("New Devin Session"), the share
sheet, a widget, or the Action Button. Shortcuts sync via iCloud, so
installing on one device makes it available on all of them. Your API key
stays on your device and is only sent to `api.devin.ai`.

## Example prompts

Sessions started from the shortcut are fire-and-forget, so self-contained
prompts that name a repo and end in a PR work best. Swap in your own
`your-org/your-repo`:

- "Fix issue #123 in your-org/your-repo, add a regression test, and open a PR."
- "Add unit tests for the payments module in your-org/your-repo and open a PR."
- "Find outdated dependencies in your-org/your-repo, upgrade the safe ones, run the tests, and open a PR."
- "Investigate the failing CI on PR #42 in your-org/your-repo and push a fix."
- "Trace the checkout flow in your-org/your-repo end to end and write up how it works, with file references."
- "Summarize the PRs merged in your-org/your-repo this week as a categorized changelog."
- "Dockerize your-org/your-repo with a multi-stage Dockerfile and docker-compose, and verify the stack runs."
- "Build a simple web app that tracks my team's PTO, write tests, and verify it end to end."

Tip: on a phone, the share sheet is the fastest path. Share a bug report,
issue link, or spec to the shortcut and the text lands in the prompt,
ready to send. Browse the [Devin use case gallery](https://docs.devin.ai/use-cases/gallery)
for more ideas, including scheduled and webhook-driven sessions.

## How it works

The shortcut calls the [Devin API](https://docs.devin.ai/api-reference/v1/sessions/create-a-new-devin-session):

```
POST https://api.devin.ai/v1/sessions
Authorization: Bearer <your API key>
{"prompt": "<what you typed>"}
```

then offers the `url` from the response. Actions, in order:

1. **Comment**: setup instructions
2. **Text**: placeholder for your Devin API key
3. **Ask for Input**: "What should Devin work on?" (pre-filled when run from the share sheet)
4. **Get Contents of URL**: the POST above
5. **Get Dictionary Value**: extracts `url`
6. **If / Otherwise**: on success shows a menu (**Open in browser** /
   **Copy link** / **Done**) so you are not forced into the browser when
   signed out; on error shows the raw API response

## Build

The shortcut is generated as code: `build_shortcut.py` writes the
`WFWorkflow` plist that Shortcuts.app reads, validates it with `plutil`, and
signs it with Apple's `shortcuts` CLI.

Requires macOS with Xcode Command Line Tools (`python3`) and Shortcuts.app
(macOS 12+). Signing with `--mode anyone` notarizes via Apple and needs
network + an iCloud-signed-in Mac.

```bash
python3 build_shortcut.py              # build + sign -> dist/New Devin Session.shortcut
python3 build_shortcut.py --no-sign    # unsigned plist only -> build/
```

After changing the shortcut, rebuild and commit the updated `dist/` artifact
so the Install link above always serves the latest signed version.

## Publish

The signed file in `dist/` is importable by anyone. Options:

- **This README's Install link**: an absolute `/raw/` URL that redirects
  to the raw file download. If you fork this repo, update the URL to your
  fork. (Prefer linking the in-repo file over release assets: GitHub
  replaces spaces with dots in release asset names, which changes the
  imported shortcut's name.)
- **iCloud link**: import the shortcut into your own Shortcuts app, then
  Share → **Copy iCloud Link**. One tap fewer for users (no file download),
  but you must re-share a new link whenever you update the shortcut.
- **[RoutineHub](https://routinehub.co)**: a community shortcut gallery.
  Create a listing that points at your iCloud link and bump it per release.

Never publish a build containing a real API key: keep the placeholder in
`build_shortcut.py`, and each user pastes their own key after import.
