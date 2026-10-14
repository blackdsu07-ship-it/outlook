import streamlit as st
import base64, random, uuid, html as htmlmod
from email.utils import formatdate

st.set_page_config(page_title="Template Generator", page_icon="📧", layout="wide")

MERGE_TAGS = ["{name}", "{domain}", "{rurl}", "{ourl}", "{uurl}", "{iurl}"]

LAYOUTS = {
    "Newsletter": """<tr><td style="padding:24px 28px 8px;font:700 22px/1.3 Arial,sans-serif;color:#111">{headline}</td></tr>
<tr><td style="padding:0 28px 16px;font:400 15px/1.6 Arial,sans-serif;color:#333">{body}</td></tr>
<tr><td style="padding:0 28px 28px"><a href="{rurl}" style="display:inline-block;background:#2457c5;color:#fff;text-decoration:none;font:700 14px Arial,sans-serif;padding:12px 22px;border-radius:4px">{cta}</a></td></tr>""",
    "Promo": """<tr><td style="padding:32px 24px 12px;text-align:center;font:800 26px/1.2 Arial,sans-serif;color:#111">{headline}</td></tr>
<tr><td style="padding:0 24px 20px;text-align:center;font:400 15px/1.6 Arial,sans-serif;color:#444">{body}</td></tr>
<tr><td style="padding:0 0 32px;text-align:center"><a href="{rurl}" style="display:inline-block;background:#d8342a;color:#fff;text-decoration:none;font:700 15px Arial,sans-serif;padding:14px 30px;border-radius:30px">{cta}</a></td></tr>""",
    "Plain": """<tr><td style="padding:20px;font:400 15px/1.7 Arial,sans-serif;color:#222">{body}</td></tr>
<tr><td style="padding:0 20px 20px"><a href="{rurl}">{cta}</a></td></tr>""",
}

ZALGO_MARKS = [chr(c) for c in list(range(0x0300, 0x0310)) + list(range(0x0320, 0x0330))]
CP1252 = {'€':0x80,'‚':0x82,'ƒ':0x83,'„':0x84,'…':0x85,'†':0x86,'‡':0x87,'ˆ':0x88,'‰':0x89,'Š':0x8a,
          '‹':0x8b,'Œ':0x8c,'Ž':0x8e,'‘':0x91,'’':0x92,'“':0x93,'”':0x94,'•':0x95,'–':0x96,'—':0x97,
          '˜':0x98,'™':0x99,'š':0x9a,'›':0x9b,'œ':0x9c,'ž':0x9e,'Ÿ':0x9f}

def to_mojibake(text):
    """Encode UTF-8 text then misread the bytes as cp1252, mimicking the classic bug."""
    out = []
    for b in text.encode("utf-8"):
        if b < 0x80:
            out.append(chr(b))
        else:
            out.append(next((k for k, v in CP1252.items() if v == b), chr(b)))
    return "".join(out)

def zalgo(text, intensity=3):
    out = []
    for ch in text:
        out.append(ch)
        if ch.strip():
            out.extend(random.choice(ZALGO_MARKS) for _ in range(intensity))
    return "".join(out)

def to_numeric_entities(text, rate=1.0):
    return "".join(f"&#{ord(c)};" if (c.strip() and random.random() < rate) else c for c in text)

def rfc2047_encode(subject):
    b64 = base64.b64encode(subject.encode("utf-8")).decode()
    return f"=?UTF-8?B?{b64}?="

def hidden_preheader(text):
    return (f'<div style="display:none;max-height:0;max-width:0;opacity:0.011;overflow:hidden;'
            f'mso-hide:all;font-size:1px;line-height:1px;color:#ffffff">{htmlmod.escape(text)}'
            f'&zwnj;&nbsp;' * 1 + '</div>')

def build_html(headline, body, cta, preheader, layout_name, add_hidden, zalgo_on, zalgo_n):
    body_html = htmlmod.escape(body).replace("\n", "<br>")
    if zalgo_on:
        headline = zalgo(headline, zalgo_n)
    block = LAYOUTS[layout_name].format(headline=htmlmod.escape(headline), body=body_html, cta=htmlmod.escape(cta), rurl="{rurl}")
    pre = hidden_preheader(preheader) if (add_hidden and preheader) else ""
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{htmlmod.escape(headline)}</title></head>
<body style="margin:0;background:#f2f2f2">
{pre}<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f2f2f2">
<tr><td align="center">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;max-width:600px">
{block}
<tr><td style="padding:16px 24px;font:400 11px/1.5 Arial,sans-serif;color:#999;border-top:1px solid #eee">
{{domain}} · <a href="{{uurl}}" style="color:#999">Unsubscribe</a></td></tr>
</table></td></tr></table>
<img src="{{iurl}}" width="1" height="1" alt="" style="display:none">
</body></html>"""

def build_eml(from_addr, to_addr, subject, html_body, encode_subject, base64_body):
    boundary = "b" + uuid.uuid4().hex[:16]
    subj = rfc2047_encode(subject) if encode_subject else subject
    if base64_body:
        enc = "base64"
        payload = "\n".join(
            base64.b64encode(html_body.encode("utf-8"))[i:i+76].decode()
            for i in range(0, len(base64.b64encode(html_body.encode("utf-8"))), 76)
        )
    else:
        enc = "quoted-printable"
        payload = html_body
    text_part = html_body.replace("<br>", "\n")
    import re
    text_part = re.sub("<[^>]+>", "", text_part)
    return f"""From: {from_addr}
To: {to_addr}
Subject: {subj}
Date: {formatdate(localtime=True)}
MIME-Version: 1.0
Content-Type: multipart/alternative; boundary="{boundary}"

--{boundary}
Content-Type: text/plain; charset=utf-8
Content-Transfer-Encoding: 7bit

{text_part.strip()}

--{boundary}
Content-Type: text/html; charset=utf-8
Content-Transfer-Encoding: {enc}

{payload}

--{boundary}--
"""

st.title("Template Generator")

with st.sidebar:
    st.subheader("Content")
    from_addr = st.text_input("From", "news@{domain}")
    to_addr = st.text_input("To", "{name} <you@example.com>")
    subject = st.text_input("Subject", "This week's update")
    preheader = st.text_input("Preheader (hidden preview text)", "You don't want to miss this.")
    layout_name = st.selectbox("Layout", list(LAYOUTS.keys()))
    headline = st.text_input("Headline", "Hello {name}")
    body = st.text_area("Body", "Here's what's new this week from {domain}.\n\nTap below to see more.", height=140)
    cta = st.text_input("Button text", "View now")

    st.subheader("Merge tags")
    st.caption(" ".join(MERGE_TAGS) + "  — click to copy, paste into any field above")

    st.subheader("Obfuscation / encoding")
    add_hidden = st.checkbox("Hidden preheader div (opacity 0.011 + mso-hide)", True)
    zalgo_on = st.checkbox("Zalgo-mangle headline", False)
    zalgo_n = st.slider("Zalgo intensity", 1, 8, 3, disabled=not zalgo_on)
    moji_on = st.checkbox("Mojibake-corrupt body (UTF-8 read as cp1252)", False)
    ent_on = st.checkbox("Numeric-entity-encode body text", False)
    ent_rate = st.slider("Entity rate", 0.1, 1.0, 0.5, disabled=not ent_on)
    encode_subject = st.checkbox("RFC 2047 encode Subject header", False)
    base64_body = st.checkbox("Base64-encode HTML MIME part", False)

if moji_on:
    body = to_mojibake(body)
if ent_on:
    body = to_numeric_entities(body, ent_rate)

html_out = build_html(headline, body, cta, preheader, layout_name, add_hidden, zalgo_on, zalgo_n)
eml_out = build_eml(from_addr, to_addr, subject, html_out, encode_subject, base64_body)

tab1, tab2, tab3 = st.tabs(["Preview", "HTML source", "Raw .eml"])
with tab1:
    st.components.v1.html(html_out.replace("{name}", "Alex").replace("{domain}", "example.com")
                           .replace("{rurl}", "#").replace("{uurl}", "#").replace("{iurl}", ""),
                           height=520, scrolling=True)
with tab2:
    st.code(html_out, language="html")
    st.download_button("Download .html", html_out, file_name="template.html", mime="text/html")
with tab3:
    st.code(eml_out, language="text")
    st.download_button("Download .eml", eml_out, file_name="template.eml", mime="message/rfc822")
