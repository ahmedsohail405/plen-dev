"""Send Alex's daily report to Ahmed on WhatsApp.

WHATSAPP_PROVIDER = print (default) | twilio
  twilio: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM ("whatsapp:+1..."),
          WHATSAPP_TO ("whatsapp:+1..."), optional TWILIO_CONTENT_SID for an approved template.
WhatsApp only lets a business start a conversation with an approved template. The template
"alex_daily_report" has one variable ({{1}}) holding the report text; if Ahmed replies to it,
the next 24 hours of messages can be free text.
"""
from __future__ import annotations

import json
import os

import requests

E = os.environ.get


def send(text: str) -> str:
    provider = E("WHATSAPP_PROVIDER", "print")
    to = E("WHATSAPP_TO", "")
    if provider == "twilio":
        sid, tok = E("TWILIO_ACCOUNT_SID", ""), E("TWILIO_AUTH_TOKEN", "")
        data = {"From": E("TWILIO_WHATSAPP_FROM", ""), "To": to}
        if E("TWILIO_CONTENT_SID"):
            data["ContentSid"] = E("TWILIO_CONTENT_SID")
            data["ContentVariables"] = json.dumps({"1": text[:1000]})
        else:
            data["Body"] = text[:1600]
        r = requests.post(f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
                          data=data, auth=(sid, tok), timeout=30)
        r.raise_for_status()
        return r.json().get("sid", "")
    print(f"[whatsapp dry run -> {to or 'WHATSAPP_TO not set'}]\n{text}")
    return "printed"
