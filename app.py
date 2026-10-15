import streamlit as st
from email.utils import formatdate

st.set_page_config(page_title="Notification Email Template", layout="wide")
st.title("Notification Email Template")
st.caption("Brand-agnostic alert/notification email. No impersonation, no obfuscation.")

with st.sidebar:
    brand       = st.text_input("Brand name", "Acme Corp")
    logo_url    = st.text_input("Logo URL (leave blank for none)", "")
    accent      = st.color_picker("Accent color", "#0f6cbd")
    headline    = st.text_input("Headline", "New sign-in to your account")
    body        = st.text_area("Body text",
        "We noticed a sign-in from a new device.\n\n"
        "If this was you, no action is needed. If you don't recognise it, "
        "secure your account by changing your password.", height=140)
    cta_label   = st.text_input("Button label", "Review activity")
    cta_url     = st.text_input("Button URL", "https://example.com/activity")
    footer_note = st.text_input("Footer note",
        "Acme Corp · 123 Main St · You're receiving this because you have an Acme account.")
    unsub_url   = st.text_input("Unsubscribe URL", "https://example.com/unsubscribe")

def build(brand, logo_url, accent, headline, body, cta_label, cta_url,
          footer_note, unsub_url):
    body_html = "".join(
        f'<p style="margin:0 0 14px;font:400 15px/1.6 Arial,sans-serif;color:#2a2a2a;">{line}</p>'
        for line in body.split("\n\n")
    )
    logo = (f'<img src="{logo_url}" alt="{brand}" width="120" '
            f'style="display:block;margin:0 0 24px;border:0;">') if logo_url else ""
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{headline}</title></head>
<body style="margin:0;padding:0;background:#f3f3f3;font-family:Arial,sans-serif;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0">
<tr><td align="center" style="padding:32px 12px;">
<table role="presentation" width="560" cellpadding="0" cellspacing="0"
       style="width:560px;max-width:560px;background:#ffffff;border-radius:8px;">
  <tr><td style="padding:32px 40px;">
    {logo}
    <h1 style="margin:0 0 16px;font:600 22px/1.3 Arial,sans-serif;color:#111;">{headline}</h1>
    {body_html}
    <p style="margin:28px 0 0;">
      <a href="{cta_url}"
         style="display:inline-block;background:{accent};color:#fff;text-decoration:none;
                font:600 14px Arial,sans-serif;padding:12px 24px;border-radius:4px;">
        {cta_label}
      </a>
    </p>
  </td></tr>
  <tr><td style="padding:20px 40px 32px;border-top:1px solid #ececec;
                 font:400 12px/1.7 Arial,sans-serif;color:#888;">
    {footer_note}<br>
    <a href="{unsub_url}" style="color:#888;">Unsubscribe</a>
  </td></tr>
</table>
</td></tr></table>
</body></html>"""

html = build(brand, logo_url, accent, headline, body, cta_label, cta_url,
             footer_note, unsub_url)

st.download_button("⬇ Download .html", html, file_name="notification.html",
                   mime="text/html")
with st.expander("Preview"):
    st.components.v1.html(html, height=500, scrolling=True)
with st.expander("Source"):
    st.code(html, language="html")
