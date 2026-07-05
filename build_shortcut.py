#!/usr/bin/env python3
"""Generate (and sign) a "New Devin Session" shortcut for iOS/macOS.

Builds the WFWorkflow plist that Shortcuts.app reads, validates it with
plutil, and signs it with /usr/bin/shortcuts so the artifact can be imported
on iOS 15+ / macOS 12+.

Usage:
  python3 build_shortcut.py            # build + sign (mode: anyone)
  python3 build_shortcut.py --no-sign  # just write the unsigned plist
"""

import argparse
import plistlib
import subprocess
import sys
import uuid
from pathlib import Path

NAME = "New Devin Session"
API_URL = "https://api.devin.ai/v1/sessions"
KEY_PLACEHOLDER = "PASTE_YOUR_DEVIN_API_KEY_HERE"

ROOT = Path(__file__).resolve().parent
BUILD_DIR = ROOT / "build"
DIST_DIR = ROOT / "dist"


def new_uuid() -> str:
    return str(uuid.uuid4()).upper()


# --- WFSerialization helpers -------------------------------------------------

SHORTCUT_INPUT = {"Type": "ExtensionInput"}


def action_output(output_uuid: str, name: str) -> dict:
    """Reference to a previous action's output (a "magic variable")."""
    return {"Type": "ActionOutput", "OutputUUID": output_uuid, "OutputName": name}


def attachment(att: dict) -> dict:
    """A parameter holding a single variable."""
    return {"Value": att, "WFSerializationType": "WFTextTokenAttachment"}


def text(*parts) -> dict:
    """Interpolated text: a mix of literal strings and attachment dicts.

    Attachments are embedded as U+FFFC placeholders with their positions
    recorded in attachmentsByRange, exactly like Shortcuts.app serializes them.
    """
    string, ranges = "", {}
    for part in parts:
        if isinstance(part, str):
            string += part
        else:
            ranges[f"{{{len(string)}, 1}}"] = part
            string += "\ufffc"
    return {
        "Value": {"string": string, "attachmentsByRange": ranges},
        "WFSerializationType": "WFTextTokenString",
    }


def dictionary(items: dict) -> dict:
    """Dictionary parameter (headers, JSON body). Values are text tokens."""
    return {
        "Value": {
            "WFDictionaryFieldValueItems": [
                {"WFItemType": 0, "WFKey": text(key), "WFValue": value}
                for key, value in items.items()
            ]
        },
        "WFSerializationType": "WFDictionaryFieldValue",
    }


def action(identifier: str, params: dict) -> dict:
    return {
        "WFWorkflowActionIdentifier": f"is.workflow.actions.{identifier}",
        "WFWorkflowActionParameters": params,
    }


# --- The shortcut ------------------------------------------------------------

def build_workflow() -> dict:
    api_key_uuid = new_uuid()
    prompt_uuid = new_uuid()
    response_uuid = new_uuid()
    url_uuid = new_uuid()
    if_group = new_uuid()
    menu_group = new_uuid()

    api_key = action_output(api_key_uuid, "Devin API Key")
    prompt = action_output(prompt_uuid, "Provided Input")
    response = action_output(response_uuid, "Contents of URL")
    session_url = action_output(url_uuid, "Dictionary Value")

    actions = [
        # 1. Setup instructions shown at the top of the editor.
        action("comment", {
            "WFCommentActionText": (
                "SETUP (one time): create an API key at app.devin.ai "
                "(Settings > API Keys) and paste it into the Text action "
                f"below, replacing {KEY_PLACEHOLDER}."
            ),
        }),
        # 2. The user's API key lives here after import.
        action("gettext", {
            "UUID": api_key_uuid,
            "CustomOutputName": "Devin API Key",
            "WFTextActionText": KEY_PLACEHOLDER,
        }),
        # 3. Ask what Devin should do. Pre-filled when run from the share
        #    sheet (Shortcut Input is the default answer).
        action("ask", {
            "UUID": prompt_uuid,
            "WFAskActionPrompt": "What should Devin work on?",
            "WFInputType": "Text",
            "WFAskActionDefaultAnswer": text(SHORTCUT_INPUT),
        }),
        # 4. POST /v1/sessions
        action("downloadurl", {
            "UUID": response_uuid,
            "WFURL": API_URL,
            "WFHTTPMethod": "POST",
            "ShowHeaders": True,
            "WFHTTPHeaders": dictionary({
                "Authorization": text("Bearer ", api_key),
            }),
            "WFHTTPBodyType": "JSON",
            "WFJSONValues": dictionary({
                "prompt": text(prompt),
            }),
        }),
        # 5. Pull the session URL out of the response.
        action("getvalueforkey", {
            "UUID": url_uuid,
            "WFGetDictionaryValueType": "Value",
            "WFDictionaryKey": "url",
            "WFInput": attachment(response),
        }),
        # 6. On success, offer choices (auto-opening the browser is annoying
        #    when you're signed out); on failure surface the API response.
        action("conditional", {
            "UUID": new_uuid(),
            "GroupingIdentifier": if_group,
            "WFControlFlowMode": 0,
            "WFCondition": 100,  # "has any value"
            "WFInput": {"Type": "Variable", "Variable": attachment(session_url)},
        }),
        action("choosefrommenu", {
            "UUID": new_uuid(),
            "GroupingIdentifier": menu_group,
            "WFControlFlowMode": 0,
            "WFMenuPrompt": "Devin session created",
            "WFMenuItems": ["Open in browser", "Copy link", "Done"],
        }),
        action("choosefrommenu", {
            "UUID": new_uuid(),
            "GroupingIdentifier": menu_group,
            "WFControlFlowMode": 1,
            "WFMenuItemTitle": "Open in browser",
        }),
        action("openurl", {"WFInput": attachment(session_url)}),
        action("choosefrommenu", {
            "UUID": new_uuid(),
            "GroupingIdentifier": menu_group,
            "WFControlFlowMode": 1,
            "WFMenuItemTitle": "Copy link",
        }),
        action("setclipboard", {"WFInput": attachment(session_url)}),
        action("notification", {
            "WFNotificationActionTitle": "Devin",
            "WFNotificationActionBody": text("Session link copied:\n", session_url),
        }),
        action("choosefrommenu", {
            "UUID": new_uuid(),
            "GroupingIdentifier": menu_group,
            "WFControlFlowMode": 1,
            "WFMenuItemTitle": "Done",
        }),
        action("choosefrommenu", {
            "UUID": new_uuid(),
            "GroupingIdentifier": menu_group,
            "WFControlFlowMode": 2,  # End Menu
        }),
        action("conditional", {
            "UUID": new_uuid(),
            "GroupingIdentifier": if_group,
            "WFControlFlowMode": 1,  # Otherwise
        }),
        action("showresult", {"Text": text("Devin API error:\n", response)}),
        action("conditional", {
            "UUID": new_uuid(),
            "GroupingIdentifier": if_group,
            "WFControlFlowMode": 2,  # End If
        }),
    ]

    return {
        "WFWorkflowClientVersion": "1146.14",
        "WFWorkflowMinimumClientVersion": 900,
        "WFWorkflowMinimumClientVersionString": "900",
        "WFWorkflowIcon": {
            "WFWorkflowIconStartColor": 463140863,  # blue
            "WFWorkflowIconGlyphNumber": 59511,
        },
        "WFWorkflowImportQuestions": [],
        # Show in share sheet (accepts text/URLs), widgets, Apple Watch.
        "WFWorkflowTypes": ["NCWidget", "WatchKit", "ActionExtension"],
        "WFWorkflowInputContentItemClasses": ["WFStringContentItem", "WFURLContentItem"],
        "WFWorkflowHasShortcutInputVariables": True,
        "WFWorkflowActions": actions,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-sign", action="store_true", help="skip `shortcuts sign`")
    parser.add_argument("--mode", default="anyone", choices=["anyone", "people-who-know-me"],
                        help="signing mode (default: anyone)")
    args = parser.parse_args()

    BUILD_DIR.mkdir(exist_ok=True)
    unsigned = BUILD_DIR / f"{NAME}.shortcut"
    with open(unsigned, "wb") as f:
        plistlib.dump(build_workflow(), f, fmt=plistlib.FMT_XML)
    subprocess.run(["plutil", "-lint", str(unsigned)], check=True)
    print(f"wrote {unsigned} (unsigned)")

    if args.no_sign:
        return 0

    DIST_DIR.mkdir(exist_ok=True)
    signed = DIST_DIR / f"{NAME}.shortcut"
    signed.unlink(missing_ok=True)
    subprocess.run(
        ["shortcuts", "sign", "--mode", args.mode,
         "--input", str(unsigned), "--output", str(signed)],
        check=True,
    )
    print(f"wrote {signed} (signed, importable on iOS/macOS)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
