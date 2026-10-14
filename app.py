import streamlit as st
import base64, random, uuid, re, quopri, html as htmlmod
from email.utils import formatdate

st.set_page_config(page_title="Bulk Email Template Generator", page_icon="📧", layout="wide")

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------
MERGE_TAGS = ["{name}", "{domain}", "{rurl}", "{ourl}", "{uurl}", "{iurl}"]

ACCENTS = {
    "Blue":   "#2457c5",
    "Red":    "#d8342a",
    "Green":  "#1f8a4c",
    "Amber":  "#c47f00",
    "Dark":   "#111111",
    "Purple": "#6b3fa0",
}

ZALGO_MARKS = [chr(c) for c in list(range(0x0300, 0x0310)) + list(range(0x0320, 0x0330))]

CP1252 = {'€':0x80,'‚':0x82,'ƒ':0x83,'„':0x84,'…':0x85,'†':0x86,'‡':0x87,'ˆ':0x88,'‰':0x89,'Š':0x8a,
          '‹':0x8b,'Œ':0x8c,'Ž':0x8e,'‘':0x91,'’':0x92,'“':0x93,'”':0x94,'•':0x95,'–':0x96,'—':0x97,
          '˜':0x98,'™':0x99,'š':0x9a,'›':0x9b,'œ':0x9c,'ž':0x9e,'Ÿ':0x9f}

LOREM = [
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
    "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
    "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris.",
    "Duis aute irure dolor in reprehenderit in voluptate velit esse cillum.",
    "Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia.",
    "Deserunt mollit anim id est laborum, sed ut perspiciatis unde omnis.",
    "Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit.",
    "Neque porro quisquam est qui dolorem ipsum quia dolor sit amet.",
]

TOPICS = [
    "Product update", "Customer story", "Engineering deep-dive", "What's new",
    "Behind the scenes", "Tips & tricks", "From the blog", "Release notes",
    "Community spotlight", "Case study", "Feature highlight", "Announcement",
]

# ----------------------------------------------------------------------------
# Text transforms
# ----------------------------------------------------------------------------
def esc(s):
    return htmlmod.escape(str(s))

def nl2br(s):
    return esc(s).replace("\n", "<br>")

def to_mojibake(text):
    """Encode UTF-8 then misread the bytes as cp1252 (classic mojibake bug)."""
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
            out.extend(random.choice(ZALGO_MARKS) for _ in range(int(intensity)))
    return "".join(out)

def to_numeric_entities(text, rate=1.0):
    return "".join(f"&#{ord(c)};" if (c.strip() and random.random() < rate) else c for c in text)

def rfc2047_encode(subject):
    b64 = base64.b64encode(subject.encode("utf-8")).decode()
    return f"=?UTF-8?B?{b64}?="

def html_to_text(h):
    t = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', h, flags=re.S | re.I)
    t = re.sub(r'<br\s*/?>', '\n', t, flags=re.I)
    t = re.sub(r'</(p|div|tr|h[1-6]|li|td)>', '\n', t, flags=re.I)
    t = re.sub(r'<[^>]+>', '', t)
    t = htmlmod.unescape(t)
    t = re.sub(r'[ \t]+\n', '\n', t)
    t = re.sub(r'\n{3,}', '\n\n', t)
    return t.strip()

# ----------------------------------------------------------------------------
# HTML block builders
# ----------------------------------------------------------------------------
def preheader_block(text):
    pad = ("&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;"
           "&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;"
           "&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;")
    return (f'<div style="display:none;font-size:1px;color:#ffffff;line-height:1px;'
            f'max-height:0;max-width:0;opacity:0;overflow:hidden;mso-hide:all;">'
            f'{esc(text)}{pad}</div>')

def header_block(brand, tagline, nav, bg, fg):
    L = []
    L.append(f'<tr><td style="background:{bg};padding:22px 28px 18px;">')
    L.append(f'  <div style="font:800 22px/1.2 Arial,Helvetica,sans-serif;color:{fg};letter-spacing:.4px;">{esc(brand)}</div>')
    if tagline:
        L.append(f'  <div style="font:400 12px/1.5 Arial,Helvetica,sans-serif;color:{fg};opacity:.65;margin-top:5px;">{esc(tagline)}</div>')
    L.append('</td></tr>')
    if nav:
        cells = "".join(
            f'<td style="padding:0 9px;font:600 12px Arial,Helvetica,sans-serif;">'
            f'<a href="{u}" style="color:{fg};text-decoration:none;opacity:.85;">{esc(l)}</a></td>'
            for l, u in nav
        )
        L.append(f'<tr><td style="background:{bg};padding:0 19px 16px;">'
                 f'<table role="presentation" cellpadding="0" cellspacing="0"><tr>{cells}</tr></table>'
                 f'</td></tr>')
    return "\n".join(L)

def hero_block(headline, sub, cta, url, accent, bg="#0f172a", fg="#ffffff"):
    L = []
    L.append(f'<tr><td style="background:{bg};padding:44px 28px 40px;" align="center">')
    L.append(f'  <div style="font:800 30px/1.2 Arial,Helvetica,sans-serif;color:{fg};max-width:480px;">{esc(headline)}</div>')
    if sub:
        L.append(f'  <div style="font:400 15px/1.6 Arial,Helvetica,sans-serif;color:{fg};opacity:.78;margin-top:14px;max-width:440px;">{esc(sub)}</div>')
    if cta:
        L.append(f'  <div style="margin-top:26px;"><a href="{url or "{rurl}"}" '
                 f'style="display:inline-block;background:{accent};color:#ffffff;text-decoration:none;'
                 f'font:700 14px Arial,Helvetica,sans-serif;padding:13px 30px;border-radius:4px;">{esc(cta)}</a></div>')
    L.append('</td></tr>')
    return "\n".join(L)

def divider_block(pad="0 28px", color="#ececec"):
    return (f'<tr><td style="padding:{pad};">'
            f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>'
            f'<td style="border-top:1px solid {color};font-size:0;line-height:0;height:1px;">&nbsp;</td>'
            f'</tr></table></td></tr>')

def article_block(idx, headline, body, cta, url, accent, rule=True):
    L = []
    if rule:
        L.append(divider_block())
    L.append(f'<tr><td style="padding:24px 28px 6px;font:700 19px/1.35 Arial,Helvetica,sans-serif;color:#111111;">'
             f'{esc(headline)}</td></tr>')
    if body:
        L.append(f'<tr><td style="padding:0 28px 16px;font:400 15px/1.68 Arial,Helvetica,sans-serif;color:#3a3a3a;">'
                 f'{nl2br(body)}</td></tr>')
    if cta:
        L.append(f'<tr><td style="padding:0 28px 24px;">'
                 f'<a href="{url or "{rurl}"}" style="display:inline-block;background:{accent};color:#ffffff;'
                 f'text-decoration:none;font:700 13px Arial,Helvetica,sans-serif;padding:11px 22px;'
                 f'border-radius:4px;">{esc(cta)}</a></td></tr>')
    return "\n".join(L)

def grid_block(items, accent, cols=2, title=None):
    L = []
    if title:
        L.append(f'<tr><td style="padding:26px 28px 4px;font:700 17px/1.3 Arial,Helvetica,sans-serif;color:#111111;">'
                 f'{esc(title)}</td></tr>')
    L.append('<tr><td style="padding:8px 20px 20px;">')
    L.append('<table role="presentation" width="100%" cellpadding="0" cellspacing="0">')
    for r in range(0, len(items), cols):
        L.append('<tr>')
        for c in range(cols):
            i = r + c
            if i < len(items):
                t, p, u = items[i]
                L.append(f'<td width="{100 // cols}%" valign="top" style="padding:8px;">')
                L.append('<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
                         'style="border:1px solid #ececec;border-radius:6px;">')
                L.append(f'<tr><td style="padding:16px;">')
                L.append(f'<div style="font:700 15px/1.35 Arial,Helvetica,sans-serif;color:#111111;">{esc(t)}</div>')
                L.append(f'<div style="font:700 14px/1.4 Arial,Helvetica,sans-serif;color:{accent};margin-top:7px;">{esc(p)}</div>')
                L.append(f'<div style="margin-top:11px;"><a href="{u}" style="color:{accent};'
                         f'font:600 12px Arial,Helvetica,sans-serif;text-decoration:none;">Shop &rarr;</a></div>')
                L.append('</td></tr></table></td>')
            else:
                L.append(f'<td width="{100 // cols}%">&nbsp;</td>')
        L.append('</tr>')
    L.append('</table>')
    L.append('</td></tr>')
    return "\n".join(L)

def banner_block(headline, cta, url, accent, bg="#f5f7fb"):
    L = []
    L.append(f'<tr><td style="background:{bg};padding:34px 28px;" align="center">')
    L.append(f'<div style="font:800 21px/1.3 Arial,Helvetica,sans-serif;color:#111111;">{esc(headline)}</div>')
    L.append(f'<div style="margin-top:18px;"><a href="{url or "{rurl}"}" '
             f'style="display:inline-block;background:{accent};color:#ffffff;text-decoration:none;'
             f'font:700 14px Arial,Helvetica,sans-serif;padding:13px 30px;border-radius:30px;">{esc(cta)}</a></div>')
    L.append('</td></tr>')
    return "\n".join(L)

def footer_block(domain, address, socials, unsub, accent):
    L = []
    L.append('<tr><td style="padding:30px 28px 8px;border-top:1px solid #ececec;" align="center">')
    L.append('<table role="presentation" cellpadding="0" cellspacing="0"><tr>')
    for label, u in socials:
        L.append(f'<td style="padding:0 7px;"><a href="{u}" style="font:600 12px Arial,Helvetica,sans-serif;'
                 f'color:#8a8a8a;text-decoration:none;">{esc(label)}</a></td>')
    L.append('</tr></table>')
    L.append('</td></tr>')
    L.append(f'<tr><td style="padding:14px 28px 6px;font:400 12px/1.7 Arial,Helvetica,sans-serif;'
             f'color:#9a9a9a;text-align:center;">{esc(address)}</td></tr>')
    L.append(f'<tr><td style="padding:0 28px 30px;font:400 12px/1.7 Arial,Helvetica,sans-serif;'
             f'color:#9a9a9a;text-align:center;">'
             f'<a href="{{{{uurl}}}}" style="color:{accent};text-decoration:underline;">{esc(unsub)}</a>'
             f' &nbsp;·&nbsp; <a href="{{{{ourl}}}}" style="color:{accent};text-decoration:underline;">View in browser</a>'
             f'</td></tr>')
    return "\n".join(L)

# ----------------------------------------------------------------------------
# Bulk content parser
# ----------------------------------------------------------------------------
def parse_blocks(text):
    blocks, cur, started = [], {"headline": "", "body": [], "cta": "", "url": ""}, False

    def flush():
        nonlocal cur, started
        if started and (cur["headline"] or cur["body"]):
            blocks.append({"headline": cur["headline"],
                           "body": "\n".join(cur["body"]).strip(),
                           "cta": cur["cta"],
                           "url": cur["url"]})
        cur = {"headline": "", "body": [], "cta": "", "url": ""}
        started = False

    for raw in text.splitlines():
        s = raw.strip()
        if re.fullmatch(r'-{3,}', s):
            flush()
            continue
        if not s:
            continue
        if s.startswith("#"):
            if started and (cur["headline"] or cur["body"]):
                flush()
            cur["headline"] = s.lstrip("#").strip()
            started = True
        elif s.startswith(">"):
            cur["cta"] = s.lstrip(">").strip()
            started = True
        elif s.startswith("@"):
            cur["url"] = s.lstrip("@").strip()
            started = True
        elif "|" in s and not cur["headline"] and not cur["body"]:
            parts = [p.strip() for p in s.split("|")]
            cur["headline"] = parts[0]
            if len(parts) > 1: cur["body"].append(parts[1])
            if len(parts) > 2: cur["cta"] = parts[2]
            if len(parts) > 3: cur["url"] = parts[3]
            started = True
        else:
            cur["body"].append(s)
            started = True

    flush()
    return blocks

def demo_content(n):
    out = []
    for i in range(1, n + 1):
        out.append(f"# {random.choice(TOPICS)} — vol. {i}")
        out.append(" ".join(random.sample(LOREM, k=random.randint(2, 4))))
        out.append("")
        out.append("> Read the full story")
        out.append("@ {rurl}")
        out.append("---")
    return "\n".join(out)

def demo_products(n):
    out = []
    for i in range(1, n + 1):
        out.append(f"Product {i} | ${random.randint(9, 199)}.00 | {{ourl}}")
    return "\n".join(out)

# ----------------------------------------------------------------------------
# Full document assembly
# ----------------------------------------------------------------------------
def build_html(C):
    L = []
    A = C["accent"]

    L.append('<!DOCTYPE html>')
    L.append('<html lang="en" xmlns:v="urn:schemas-microsoft-com:vml" '
             'xmlns:o="urn:schemas-microsoft-com:office:office">')
    L.append('<head>')
    L.append('<meta charset="utf-8">')
    L.append('<meta name="viewport" content="width=device-width,initial-scale=1">')
    L.append('<meta name="x-apple-disable-message-reformatting">')
    L.append('<meta name="format-detection" content="telephone=no,address=no,email=no,date=no">')
    L.append('<meta name="color-scheme" content="light only">')
    L.append('<meta name="supported-color-schemes" content="light only">')
    L.append(f'<title>{esc(C["subject"])}</title>')
    L.append('<!--[if mso]>')
    L.append('<xml><o:OfficeDocumentSettings>')
    L.append('<o:AllowPNG/><o:PixelsPerInch>96</o:PixelsPerInch>')
    L.append('</o:OfficeDocumentSettings></xml>')
    L.append('<![endif]-->')
    L.append('<style type="text/css">')
    L.append('  html,body{margin:0!important;padding:0!important;height:100%!important;width:100%!important;}')
    L.append('  *{-ms-text-size-adjust:100%;-webkit-text-size-adjust:100%;}')
    L.append('  table,td{mso-table-lspace:0pt!important;mso-table-rspace:0pt!important;}')
    L.append('  table{border-spacing:0!important;border-collapse:collapse!important;table-layout:fixed!important;margin:0 auto!important;}')
    L.append('  img{-ms-interpolation-mode:bicubic;border:0;height:auto;line-height:100%;outline:none;text-decoration:none;}')
    L.append('  a{text-decoration:none;}')
    L.append('  a[x-apple-data-detectors]{color:inherit!important;text-decoration:none!important;font-size:inherit!important;font-family:inherit!important;font-weight:inherit!important;line-height:inherit!important;}')
    L.append('  .ExternalClass{width:100%;}')
    L.append('  .ExternalClass,.ExternalClass p,.ExternalClass span,.ExternalClass font,.ExternalClass td,.ExternalClass div{line-height:100%;}')
    L.append('  @media only screen and (max-width:620px){')
    L.append('    .wrap{width:100%!important;max-width:100%!important;}')
    L.append('    .px{padding-left:18px!important;padding-right:18px!important;}')
    L.append('    .h1{font-size:24px!important;line-height:1.25!important;}')
    L.append('    .stack{display:block!important;width:100%!important;}')
    L.append('  }')
    L.append('  @media (prefers-color-scheme:dark){')
    L.append('    .dm-bg{background:#111111!important;}')
    L.append('    .dm-fg{color:#f2f2f2!important;}')
    L.append('  }')
    L.append('</style>')
    L.append('</head>')
    L.append(f'<body style="margin:0;padding:0;background:{C["page_bg"]};'
             f'font-family:Arial,Helvetica,sans-serif;">')

    if C["preheader"]:
        L.append(preheader_block(C["preheader"]))

    L.append(f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
             f'style="background:{C["page_bg"]};">')
    L.append('<tr><td align="center" style="padding:24px 12px;">')
    L.append('<!--[if mso]><table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0"><tr><td><![endif]-->')
    L.append('<table role="presentation" class="wrap" width="600" cellpadding="0" cellspacing="0" border="0" '
             'style="width:600px;max-width:600px;background:#ffffff;border-radius:8px;overflow:hidden;">')

    L.append(header_block(C["brand"], C["tagline"], C["nav"], C["header_bg"], C["header_fg"]))

    if C["hero_headline"]:
        L.append(hero_block(C["hero_headline"], C["hero_sub"], C["hero_cta"],
                            C["hero_url"], A, C["hero_bg"]))

    if C["intro"]:
        L.append(f'<tr><td class="px" style="padding:26px 28px 4px;font:400 15px/1.7 '
                 f'Arial,Helvetica,sans-serif;color:#3a3a3a;">{nl2br(C["intro"])}</td></tr>')

    L.append(f'<!-- ===== {len(C["blocks"])} article block(s) ===== -->')
    for i, b in enumerate(C["blocks"], start=1):
        L.append(f'<!-- article {i} of {len(C["blocks"])} -->')
        headline = b["headline"] or f"Update #{i}"
        if C["zalgo_on"]:
            headline = zalgo(headline, C["zalgo_n"])
        L.append(article_block(i, headline, b["body"], b["cta"] or C["default_cta"],
                               b["url"] or C["default_url"], A))

    if C["products"]:
        L.append(grid_block(C["products"], A, cols=C["grid_cols"], title=C["grid_title"]))

    if C["banner_headline"]:
        L.append(banner_block(C["banner_headline"], C["banner_cta"],
                              C["banner_url"], A))

    L.append(footer_block(C["domain"], C["address"], C["socials"],
                          C["unsub_text"], A))

    L.append('</table>')
    L.append('<!--[if mso]></td></tr></table><![endif]-->')
    L.append('</td></tr>')
    L.append('</table>')

    if C["tracker"]:
        L.append(f'<img src="{{{{iurl}}}}" width="1" height="1" alt="" '
                 f'style="display:none;width:1px;height:1px;border:0;">')

    L.append('</body>')
    L.append('</html>')

    doc = "\n".join(L)

    if C["pad_to"] and doc.count("\n") + 1 < C["pad_to"]:
        need = C["pad_to"] - (doc.count("\n") + 1)
        pad_lines = [f'<!-- filler line {i + 1} -->' for i in range(need)]
        doc = doc.replace('</body>', "\n".join(pad_lines) + "\n</body>")

    return doc

# ----------------------------------------------------------------------------
# EML assembly
# ----------------------------------------------------------------------------
def wrap_b64(data: bytes, width=76):
    b = base64.b64encode(data).decode("ascii")
    return "\n".join(b[i:i + width] for i in range(0, len(b), width))

def build_eml(from_addr, to_addr, subject, html_body, encode_subject,
              base64_body, extra_headers=""):
    boundary = "b" + uuid.uuid4().hex[:16]
    subj = rfc2047_encode(subject) if encode_subject else subject

    if base64_body:
        enc = "base64"
        payload = wrap_b64(html_body.encode("utf-8"))
    else:
        enc = "quoted-printable"
        payload = quopri.encodestring(html_body.encode("utf-8")).decode("ascii")

    text_body = html_to_text(html_body)
    headers = [
        f"From: {from_addr}",
        f"To: {to_addr}",
        f"Subject: {subj}",
        f"Date: {formatdate(localtime=True)}",
        "MIME-Version: 1.0",
    ]
    if extra_headers.strip():
        headers.append(extra_headers.strip())
    headers.append(f'Content-Type: multipart/alternative; boundary="{boundary}"')

    parts = [
        "\n".join(headers),
        "",
        f"--{boundary}",
        "Content-Type: text/plain; charset=utf-8",
        "Content-Transfer-Encoding: quoted-printable",
        "",
        quopri.encodestring(text_body.encode("utf-8")).decode("ascii"),
        "",
        f"--{boundary}",
        "Content-Type: text/html; charset=utf-8",
        f"Content-Transfer-Encoding: {enc}",
        "",
        payload,
        "",
        f"--{boundary}--",
        "",
    ]
    return "\n".join(parts)

# ----------------------------------------------------------------------------
# UI
# ----------------------------------------------------------------------------
st.title("📧 Bulk Email Template Generator")
st.caption("Generate long-form (1000+ line) HTML emails from a bulk content list.")

if "bulk" not in st.session_state:
    st.session_state.bulk = demo_content(12)
if "prods" not in st.session_state:
    st.session_state.prods = demo_products(4)

with st.sidebar:
    st.subheader("Sender")
    from_addr = st.text_input("From", "news@{domain}")
    to_addr = st.text_input("To", "{name} <you@example.com>")
    subject = st.text_input("Subject", "This week's update")
    preheader = st.text_input("Preheader (hidden preview text)", "You don't want to miss this.")

    st.subheader("Brand & theme")
    brand = st.text_input("Brand name", "ACME Co.")
    tagline = st.text_input("Tagline", "Weekly digest")
    accent_name = st.selectbox("Accent", list(ACCENTS.keys()), index=0)
    accent = ACCENTS[accent_name]
    page_bg = st.color_picker("Page background", "#f2f2f2")
    header_bg = st.color_picker("Header background", "#111111")
    header_fg = st.color_picker("Header text", "#ffffff")
    hero_bg = st.color_picker("Hero background", "#0f172a")

    st.subheader("Hero")
    hero_headline = st.text_input("Hero headline", "Everything new, in one place")
    hero_sub = st.text_input("Hero subline", "Hand-picked stories from the team.")
    hero_cta = st.text_input("Hero button", "Open the digest")
    hero_url = st.text_input("Hero link", "{rurl}")

    st.subheader("Bulk content")
    st.caption(
        "One block per story. Separate blocks with `---` (or a blank line).\n\n"
        "`# Headline` · body lines · `> CTA text` · `@ link`\n\n"
        "One-liner form: `Headline | Body | CTA | link`"
    )
    n_demo = st.number_input("Demo blocks to generate", 10, 500, 250, step=10)
    c1, c2 = st.columns(2)
    if c1.button("Fill demo", use_container_width=True):
        st.session_state.bulk = demo_content(int(n_demo))
        st.rerun()
    if c2.button("Clear", use_container_width=True):
        st.session_state.bulk = ""
        st.rerun()

    bulk_text = st.text_area("Article blocks", key="bulk", height=260)
    intro = st.text_area("Intro paragraph", "Here's what's new this week from {domain}.", height=80)

    st.subheader("Defaults for blocks")
    default_cta = st.text_input("Default CTA", "Read more")
    default_url = st.text_input("Default link", "{rurl}")

    st.subheader("Product grid")
    prods_text = st.text_area("Products (Title | Price | link, one per line)", key="prods", height=120)
    grid_title = st.text_input("Grid title", "Popular this week")
    grid_cols = st.select_slider("Columns", [1, 2, 3], value=2)

    st.subheader("Banner")
    banner_headline = st.text_input("Banner headline", "Ready to get started?")
    banner_cta = st.text_input("Banner button", "Create an account")
    banner_url = st.text_input("Banner link", "{rurl}")

    st.subheader("Footer")
    nav_raw = st.text_input("Header nav (Label|url, comma separated)",
                            "Home|{domain}, Blog|{ourl}, Contact|{rurl}")
    domain = st.text_input("Footer domain", "{domain}")
    address = st.text_input("Address line", "ACME Co. · 1 Main St, Springfield · © 2025")
    socials_raw = st.text_input("Socials (Label|url, comma separated)",
                                "Twitter|{ourl}, LinkedIn|{ourl}, Web|{domain}")
    unsub_text = st.text_input("Unsubscribe label", "Unsubscribe")
    tracker = st.checkbox("Include 1x1 open-tracking pixel", True)

    st.subheader("Obfuscation / encoding")
    add_hidden = st.checkbox("Hidden preheader div", True)
    zalgo_on = st.checkbox("Zalgo-mangle headlines", False)
    zalgo_n = st.slider("Zalgo intensity", 1, 8, 3, disabled=not zalgo_on)
    moji_on = st.checkbox("Mojibake-corrupt body (UTF-8 read as cp1252)", False)
    ent_on = st.checkbox("Numeric-entity-encode body text", False)
    ent_rate = st.slider("Entity rate", 0.1, 1.0, 0.5, disabled=not ent_on)
    encode_subject = st.checkbox("RFC 2047 encode Subject header", False)
    base64_body = st.checkbox("Base64-encode HTML MIME part", False)
    extra_headers = st.text_area(
        "Extra headers (one per line)",
        "List-Unsubscribe: <mailto:unsub@{domain}?subject=unsubscribe>\n"
        "List-Unsubscribe-Post: List-Unsubscribe=One-Click",
        height=80,
    )

    st.subheader("Length")
    pad_to = st.number_input("Pad output to at least N lines (0 = off)", 0, 20000, 1000, step=100)

# ----------------------------------------------------------------------------
# Build the data
# ----------------------------------------------------------------------------
blocks = parse_blocks(bulk_text)

if moji_on:
    for b in blocks:
        b["body"] = to_mojibake(b["body"])
        b["headline"] = to_mojibake(b["headline"])
    intro = to_mojibake(intro)
    hero_headline = to_mojibake(hero_headline)

if ent_on:
    for b in blocks:
        b["body"] = to_numeric_entities(b["body"], ent_rate)
    intro = to_numeric_entities(intro, ent_rate)

def parse_pairs(raw, default=None):
    out = []
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "|" in chunk:
            l, u = chunk.split("|", 1)
            out.append((l.strip(), u.strip()))
        elif default:
            out.append((chunk, default))
    return out

nav = parse_pairs(nav_raw)
socials = parse_pairs(socials_raw, default="{domain}")

products = []
for line in prods_text.splitlines():
    line = line.strip()
    if not line:
        continue
    parts = [p.strip() for p in line.split("|")]
    if len(parts) >= 3:
        products.append((parts[0], parts[1], parts[2]))
    elif len(parts) == 2:
        products.append((parts[0], parts[1], "{ourl}"))

C = dict(
    subject=subject, accent=accent, page_bg=page_bg,
    brand=brand, tagline=tagline, nav=nav,
    header_bg=header_bg, header_fg=header_fg,
    hero_headline=hero_headline, hero_sub=hero_sub, hero_cta=hero_cta,
    hero_url=hero_url, hero_bg=hero_bg,
    preheader=preheader if add_hidden else "",
    intro=intro, blocks=blocks,
    default_cta=default_cta, default_url=default_url,
    products=products, grid_title=grid_title, grid_cols=int(grid_cols),
    banner_headline=banner_headline, banner_cta=banner_cta, banner_url=banner_url,
    domain=domain, address=address, socials=socials, unsub_text=unsub_text,
    tracker=tracker, zalgo_on=zalgo_on, zalgo_n=zalgo_n, pad_to=int(pad_to),
)

html_out = build_html(C)
eml_out = build_eml(from_addr, to_addr, subject, html_out,
                    encode_subject, base64_body, extra_headers)

# ----------------------------------------------------------------------------
# Metrics + tabs
# ----------------------------------------------------------------------------
lines = html_out.count("\n") + 1
m1, m2, m3, m4 = st.columns(4)
m1.metric("HTML lines", f"{lines:,}")
m2.metric("HTML size", f"{len(html_out.encode('utf-8')) / 1024:.1f} KB")
m3.metric("Article blocks", f"{len(blocks):,}")
m4.metric("EML size", f"{len(eml_out.encode('utf-8')) / 1024:.1f} KB")

if lines < 1000:
    st.info(f"Output is {lines:,} lines. Add more blocks (or set 'Pad to at least N lines' to 1000) "
            f"to reach the 1000+ line target.")

tab1, tab2, tab3, tab4 = st.tabs(["Preview", "HTML source", "Raw .eml", "Merge tags"])

with tab1:
    preview = (html_out
               .replace("{name}", "Alex")
               .replace("{domain}", "example.com")
               .replace("{ourl}", "#")
               .replace("{rurl}", "#")
               .replace("{uurl}", "#")
               .replace("{iurl}", ""))
    st.components.v1.html(preview, height=760, scrolling=True)

with tab2:
    st.code(html_out, language="html")
    st.download_button("⬇ Download .html", html_out,
                       file_name="template.html", mime="text/html")

with tab3:
    st.code(eml_out, language="text")
    st.download_button("⬇ Download .eml", eml_out,
                       file_name="template.eml", mime="message/rfc822")

with tab4:
    st.write("Paste these into any field. They survive into the final HTML/EML.")
    for tag in MERGE_TAGS:
        st.code(tag, language="text")
