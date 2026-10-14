import streamlit as st
import base64, random, uuid, re, quopri, html as htmlmod, string
from email.utils import formatdate

st.set_page_config(page_title="Email Utility Toolkit", page_icon="🧰", layout="wide")

# ============================================================================
# Constants
# ============================================================================
MERGE_TAGS = ["{name}", "{domain}", "{rurl}", "{ourl}", "{uurl}", "{iurl}"]

ACCENTS = {
    "Blue":   "#2457c5", "Red":  "#d8342a", "Green": "#1f8a4c",
    "Amber":  "#c47f00", "Dark": "#111111", "Purple": "#6b3fa0",
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

UNICODE_ESCAPE_STYLES = [
    "JS \\uXXXX (surrogate pairs for >U+FFFF)",
    "ES6 \\u{XXXXX}",
    "HTML hex entity &#xXXXX;",
    "HTML decimal entity &#DDDD;",
    "U+XXXX notation",
    "Python \\xXX / \\uXXXX / \\UXXXXXXXX",
    "JSON \\uXXXX (lowercase)",
]

MOJIBAKE_PRESETS = {
    "Western — UTF-8 read as Latin-1":       ("utf-8", "latin-1"),
    "Western — UTF-8 read as cp1252":        ("utf-8", "cp1252"),
    "Arabic — UTF-8 read as Latin-1":        ("utf-8", "latin-1"),
    "Arabic — UTF-8 read as cp1252":         ("utf-8", "cp1252"),
    "Arabic — UTF-8 read as cp1256":         ("utf-8", "cp1256"),
    "Chinese — UTF-8 read as Latin-1":       ("utf-8", "latin-1"),
    "Chinese — GBK read as Latin-1":         ("gbk", "latin-1"),
    "Chinese — Big5 read as Latin-1":        ("big5", "latin-1"),
    "Japanese — UTF-8 read as Latin-1":      ("utf-8", "latin-1"),
    "Japanese — Shift-JIS read as Latin-1":  ("shift_jis", "latin-1"),
    "Korean — UTF-8 read as Latin-1":        ("utf-8", "latin-1"),
    "Korean — EUC-KR read as Latin-1":       ("euc-kr", "latin-1"),
    "Russian — UTF-8 read as Latin-1":       ("utf-8", "latin-1"),
    "Russian — UTF-8 read as cp1251":        ("utf-8", "cp1251"),
    "Hebrew — UTF-8 read as Latin-1":        ("utf-8", "latin-1"),
    "Hebrew — UTF-8 read as cp1255":         ("utf-8", "cp1255"),
    "Greek — UTF-8 read as Latin-1":         ("utf-8", "latin-1"),
    "Greek — UTF-8 read as cp1253":          ("utf-8", "cp1253"),
    "Thai — UTF-8 read as Latin-1":          ("utf-8", "latin-1"),
    "Hindi — UTF-8 read as Latin-1":         ("utf-8", "latin-1"),
    "Turkish — UTF-8 read as Latin-1":       ("utf-8", "latin-1"),
    "Persian — UTF-8 read as Latin-1":       ("utf-8", "latin-1"),
    "Double mojibake (UTF-8→L1→UTF-8→L1)":   ("__double__", "latin-1"),
    "Triple mojibake":                       ("__triple__", "latin-1"),
}

SCRIPT_SAMPLES = {
    "Arabic":               "العربية نص تجريبي للاختبار مرحبا بالعالم أهلا وسهلا",
    "Persian (Farsi)":      "سلام دنیا این یک متن آزمایشی است خوش آمدید",
    "Urdu":                 "ہیلو دنیا یہ ایک ٹیسٹ متن ہے خوش آمدید",
    "Hebrew":               "שלום עולם זהו טקסט בדיקה למילוי תוכן ברוכים הבאים",
    "Chinese (Simplified)": "你好世界这是一个测试文本用于填充内容欢迎光临",
    "Chinese (Traditional)":"你好世界這是一個測試文本用於填充內容歡迎光臨",
    "Japanese":             "こんにちは世界これはテストテキストですようこそ",
    "Korean":               "안녕하세요 세계 이것은 테스트 텍스트입니다 환영합니다",
    "Russian":              "Привет мир это тестовый текст для заполнения добро пожаловать",
    "Ukrainian":            "Привіт світе це тестовий текст для заповнення ласкаво просимо",
    "Greek":                "Γεια σου κόσμε αυτό είναι ένα δοκιμαστικό κείμενο καλώς ήρθες",
    "Turkish":              "Merhaba dünya bu bir test metnidir hoş geldiniz",
    "Thai":                 "สวัสดีชาวโลกนี่คือข้อความทดสอบยินดีต้อนรับ",
    "Hindi (Devanagari)":   "नमस्ते दुनिया यह एक परीक्षण पाठ है स्वागत है",
    "Tamil":                "வணக்கம் உலகம் இது ஒரு சோதனை உரை வரவேற்கிறோம்",
    "Bengali":              "হ্যালো বিশ্ব এটি একটি পরীক্ষা পাঠ্য স্বাগতম",
    "Armenian":             "Բարև աշխարհ սա փորձնական տեքստ է բարի գալուստ",
    "Georgian":             "გამარჯობა მსოფლიო ეს არის ტესტის ტექსტი მოგესალმებით",
    "Amharic":              "ሰላም ዓለም ይህ የሙከራ ጽሑፍ ነው እንኳን ደህና መጡ",
    "Vietnamese":           "Xin chào thế giới đây là văn bản thử nghiệm chào mừng",
    "Kurdish":              "سڵاو جیهان ئەمە دەقێکی تاقیکارییە بەخێربێن",
}

MACRO_SEPARATORS = {
    "(none)": "", "space": " ", "&nbsp;": "&nbsp;", "<wbr>": "<wbr>",
    "&#8203;": "&#8203;", "newline": "\n", "<!-- -->": "<!-- -->", "comma": ",",
}

SPACER_CHARS = {
    "&nbsp; (non-breaking space)":      "&nbsp;",
    "&zwnj;&nbsp; (preheader classic)": "&zwnj;&nbsp;",
    "&#8203; (zero-width space)":       "&#8203;",
    "&zwj; (zero-width joiner)":        "&zwj;",
    "&emsp; (em space)":                "&emsp;",
    "&ensp; (en space)":                "&ensp;",
    "· (middle dot)":                    "·",
    ". (period)":                        ".",
    "• (bullet)":                        "•",
    "– (en dash)":                       "–",
    "— (em dash)":                       "—",
    "_ (underscore)":                    "_",
}

HIDDEN_CLASS = "mc-hidden"

# ============================================================================
# Core transform functions (pure, reusable)
# ============================================================================
def to_mojibake(text):
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

def to_script_mojibake(text, preset):
    if preset not in MOJIBAKE_PRESETS:
        return text
    src, dst = MOJIBAKE_PRESETS[preset]
    try:
        if src == "__double__":
            x = text.encode("utf-8").decode(dst, errors="replace")
            return x.encode("utf-8").decode(dst, errors="replace")
        if src == "__triple__":
            x = text
            for _ in range(3):
                x = x.encode("utf-8").decode(dst, errors="replace")
            return x
        return text.encode(src, errors="replace").decode(dst, errors="replace")
    except (LookupError, UnicodeError):
        return text

def to_unicode_escape(text, style, rate=1.0, skip_ascii=True):
    out = []
    for ch in text:
        cp = ord(ch)
        if skip_ascii and ch.isascii() and (ch.isalnum() or ch in " .,!?-:;()[]{}'\"/\\\n"):
            out.append(ch); continue
        if rate < 1.0 and random.random() > rate:
            out.append(ch); continue

        if style.startswith("JS"):
            if cp > 0xFFFF:
                cp2 = cp - 0x10000
                hi, lo = 0xD800 + (cp2 >> 10), 0xDC00 + (cp2 & 0x3FF)
                out.append(f"\\u{hi:04X}\\u{lo:04X}")
            else:
                out.append(f"\\u{cp:04X}")
        elif style.startswith("JSON"):
            if cp > 0xFFFF:
                cp2 = cp - 0x10000
                hi, lo = 0xD800 + (cp2 >> 10), 0xDC00 + (cp2 & 0x3FF)
                out.append(f"\\u{hi:04x}\\u{lo:04x}")
            else:
                out.append(f"\\u{cp:04x}")
        elif style.startswith("ES6"):
            out.append(f"\\u{{{cp:X}}}")
        elif style.startswith("HTML hex"):
            out.append(f"&#x{cp:X};")
        elif style.startswith("HTML decimal"):
            out.append(f"&#{cp};")
        elif style.startswith("U+"):
            out.append(f"U+{cp:04X}")
        elif style.startswith("Python"):
            if cp < 0x100: out.append(f"\\x{cp:02x}")
            elif cp < 0x10000: out.append(f"\\u{cp:04x}")
            else: out.append(f"\\U{cp:08x}")
        else:
            out.append(ch)
    return "".join(out)

def rfc2047_encode(subject):
    b64 = base64.b64encode(subject.encode("utf-8")).decode()
    return f"=?UTF-8?B?{b64}?="

def rand_alpha(n, pool=string.ascii_letters + string.digits):
    return "".join(random.choice(pool) for _ in range(n))

def rand_script_string(script, min_len=8, max_len=24):
    sample = SCRIPT_SAMPLES.get(script)
    if not sample:
        return rand_alpha(random.randint(min_len, max_len))
    n = random.randint(min(6, len(sample)), min(len(sample), max_len))
    start = random.randint(0, max(0, len(sample) - n))
    return sample[start:start + n].replace("--", "\u2010\u2010")

def build_spacer_run(unit, count):
    if not unit or count <= 0:
        return ""
    return unit * int(count)

def build_macro_run(macros, reps_per, separator, interleave=False):
    if not macros or reps_per <= 0:
        return ""
    if interleave:
        pool = macros * int(reps_per)
        random.shuffle(pool)
        return separator.join(pool)
    parts = []
    for m in macros:
        parts.extend([m] * int(reps_per))
    return separator.join(parts)

# ============================================================================
# UI — one tab per generator
# ============================================================================
st.title("🧰 Email Utility Toolkit")
st.caption("Each tab is a standalone generator. Pick a tool, put input in, take output out.")

tabs = st.tabs([
    "🔤 Mojibake",
    "🌍 Script Mojibake",
    "🔢 Unicode Escapes",
    "🌀 Zalgo",
    "📜 Numeric Entities",
    "🎲 Random Strings",
    "✍️ Script Content",
    "🔁 Repeated Macros",
    "⬛ Spacers",
    "📧 Email Builder",
])

# ---------------------------------------------------------------------------
# TAB 1 — Mojibake
# ---------------------------------------------------------------------------
with tabs[0]:
    st.header("Mojibake Generator")
    st.caption("UTF-8 text read back as cp1252 — produces the classic `Ã©`-style garble.")

    src = st.text_area(
        "Input text",
        value="Café — naïve résumé · 你好 · مرحبا",
        height=140,
        key="mj_in",
    )
    out = to_mojibake(src)
    st.text_area("Mojibake output", value=out, height=140, key="mj_out")
    st.download_button("⬇ Download .txt", out, file_name="mojibake.txt",
                       mime="text/plain", use_container_width=False)

# ---------------------------------------------------------------------------
# TAB 2 — Script Mojibake
# ---------------------------------------------------------------------------
with tabs[1]:
    st.header("Script Mojibake Generator")
    st.caption("Round-trip text through a source charset, decode as a different one.")

    c1, c2 = st.columns([1, 2])
    with c1:
        preset = st.selectbox("Preset", list(MOJIBAKE_PRESETS.keys()),
                              index=0, key="sm_preset")
    with c2:
        src = st.text_area("Input text",
                           value="Café — naïve · 你好 · مرحبا · Привет · Γειά",
                           height=140, key="sm_in")

    out = to_script_mojibake(src, preset)
    st.text_area("Output", value=out, height=180, key="sm_out")
    st.download_button("⬇ Download .txt", out, file_name="script_mojibake.txt",
                       mime="text/plain")

# ---------------------------------------------------------------------------
# TAB 3 — Unicode Escapes
# ---------------------------------------------------------------------------
with tabs[2]:
    st.header("Unicode Escape Generator")
    st.caption("Escape characters as `\\uXXXX`, `\\u{…}`, HTML entities, `U+…`, Python, or JSON.")

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        style = st.selectbox("Escape style", UNICODE_ESCAPE_STYLES, index=0, key="ue_style")
    with c2:
        rate = st.slider("Escape rate", 0.1, 1.0, 1.0, step=0.1, key="ue_rate")
    with c3:
        skip_ascii = st.checkbox("Leave ASCII words", True, key="ue_skip")

    src = st.text_area("Input text",
                       value="Hello 世界 — Café — مرحبا — Γειά",
                       height=140, key="ue_in")
    out = to_unicode_escape(src, style, rate, skip_ascii)
    st.text_area("Output", value=out, height=180, key="ue_out")
    st.download_button("⬇ Download .txt", out, file_name="unicode_escaped.txt",
                       mime="text/plain")

# ---------------------------------------------------------------------------
# TAB 4 — Zalgo
# ---------------------------------------------------------------------------
with tabs[3]:
    st.header("Zalgo Generator")
    st.caption("Piles combining diacritics on each character.")

    c1, c2 = st.columns([3, 1])
    with c1:
        src = st.text_area("Input text", value="Hello World", height=140, key="zg_in")
    with c2:
        intensity = st.slider("Intensity", 1, 20, 5, key="zg_int")

    out = zalgo(src, intensity)
    st.text_area("Output", value=out, height=180, key="zg_out")
    st.download_button("⬇ Download .txt", out, file_name="zalgo.txt", mime="text/plain")

# ---------------------------------------------------------------------------
# TAB 5 — Numeric Entities
# ---------------------------------------------------------------------------
with tabs[4]:
    st.header("Numeric Entity Generator")
    st.caption("Encodes characters as `&#NNNN;` HTML entities. These render as the original characters.")

    c1, c2 = st.columns([3, 1])
    with c1:
        src = st.text_area("Input text", value="Hello World — café 你好", height=140, key="ne_in")
    with c2:
        rate = st.slider("Encode rate", 0.1, 1.0, 1.0, step=0.1, key="ne_rate")

    out = to_numeric_entities(src, rate)
    st.text_area("Output", value=out, height=180, key="ne_out")
    st.download_button("⬇ Download .txt", out, file_name="entities.txt", mime="text/plain")

# ---------------------------------------------------------------------------
# TAB 6 — Random Strings
# ---------------------------------------------------------------------------
with tabs[5]:
    st.header("Random Alphanumeric String Generator")
    st.caption("Generates random strings. Choose one-per-line or joined.")

    c1, c2, c3 = st.columns(3)
    with c1:
        count = st.number_input("How many strings", 1, 5000, 40, step=1, key="rs_count")
    with c2:
        min_len, max_len = st.slider("Length range", 4, 64, (8, 16), key="rs_len")
    with c3:
        pool_label = st.selectbox(
            "Character pool",
            ["letters + digits", "letters only", "digits only",
             "lowercase + digits", "uppercase + digits", "hex"],
            key="rs_pool",
        )

    pools = {
        "letters + digits":   string.ascii_letters + string.digits,
        "letters only":       string.ascii_letters,
        "digits only":        string.digits,
        "lowercase + digits": string.ascii_lowercase + string.digits,
        "uppercase + digits": string.ascii_uppercase + string.digits,
        "hex":                "0123456789abcdef",
    }

    if st.button("🎲 Generate", key="rs_go"):
        strings = [rand_alpha(random.randint(min_len, max_len), pools[pool_label])
                   for _ in range(int(count))]
        st.session_state["rs_output"] = strings

    strings = st.session_state.get("rs_output", [])
    as_lines = "\n".join(strings)
    st.text_area("Output (one per line)", value=as_lines, height=220, key="rs_out")
    if strings:
        st.download_button("⬇ Download .txt", as_lines, file_name="random_strings.txt",
                           mime="text/plain")
        st.caption(f"{len(strings):,} strings · {sum(len(s) for s in strings):,} chars total")

# ---------------------------------------------------------------------------
# TAB 7 — Script Content
# ---------------------------------------------------------------------------
with tabs[6]:
    st.header("Real Script Content Generator")
    st.caption("Outputs real text in Arabic, Chinese, Japanese, etc. Good for filling templates.")

    c1, c2 = st.columns([2, 1])
    with c1:
        script = st.selectbox("Script", list(SCRIPT_SAMPLES.keys()), key="sc_script")
    with c2:
        n = st.number_input("How many strings", 1, 1000, 20, step=1, key="sc_count")

    if st.button("✍️ Generate", key="sc_go"):
        st.session_state["sc_output"] = [rand_script_string(script) for _ in range(int(n))]

    strings = st.session_state.get("sc_output", [])
    as_lines = "\n".join(strings)
    st.text_area("Output (one per line)", value=as_lines, height=220, key="sc_out")
    if strings:
        st.download_button("⬇ Download .txt", as_lines, file_name="script_content.txt",
                           mime="text/plain")

# ---------------------------------------------------------------------------
# TAB 8 — Repeated Macros
# ---------------------------------------------------------------------------
with tabs[7]:
    st.header("Repeated Macro Generator")
    st.caption("Repeats merge tags. Output is just the run — no wrapper, no HTML.")

    c1, c2 = st.columns([2, 1])
    with c1:
        selected = st.multiselect(
            "Macros to repeat",
            options=MERGE_TAGS + ["(custom)"],
            default=["{name}"], key="rm_sel",
        )
    with c2:
        reps = st.number_input("Reps per macro", 1, 2000, 20, step=1, key="rm_reps")

    custom = st.text_input("Custom macro (used if '(custom)' is selected)",
                           "", key="rm_custom",
                           disabled="(custom)" not in selected)

    macros = [m for m in selected if m != "(custom)"]
    if "(custom)" in selected and custom.strip():
        macros.append(custom.strip())

    c1, c2 = st.columns(2)
    with c1:
        sep_label = st.selectbox("Separator", list(MACRO_SEPARATORS.keys()),
                                 index=0, key="rm_sep")
    with c2:
        interleave = st.checkbox("Interleave (shuffle)", False, key="rm_int")

    if st.button("🔁 Generate", key="rm_go"):
        st.session_state["rm_output"] = build_macro_run(
            macros, int(reps), MACRO_SEPARATORS[sep_label], interleave)

    out = st.session_state.get("rm_output", "")
    st.text_area("Output", value=out, height=200, key="rm_out")
    if out:
        st.download_button("⬇ Download .txt", out, file_name="macros.txt", mime="text/plain")
        st.caption(f"{len(out):,} chars · {out.count(chr(10))+1:,} lines")

# ---------------------------------------------------------------------------
# TAB 9 — Spacers
# ---------------------------------------------------------------------------
with tabs[8]:
    st.header("Spacer Generator")
    st.caption("Repeating spacer characters — for preheader tail padding or content push.")

    c1, c2 = st.columns([2, 1])
    with c1:
        char_label = st.selectbox("Spacer character", list(SPACER_CHARS.keys()),
                                  index=1, key="sp_char")
    with c2:
        n = st.number_input("How many", 1, 10000, 60, step=1, key="sp_count")

    out = build_spacer_run(SPACER_CHARS[char_label], int(n))
    st.text_area("Output", value=out, height=200, key="sp_out")
    st.download_button("⬇ Download .txt", out, file_name="spacers.txt", mime="text/plain")
    st.caption(f"{len(out):,} chars")

# ---------------------------------------------------------------------------
# TAB 10 — Email Builder (the combined one, on demand)
# ---------------------------------------------------------------------------
# (compact re-implementation of the earlier combined tool — same features,
#  but now opt-in rather than the default output)

def esc(s):
    return htmlmod.escape(str(s))

def nl2br(s):
    return esc(s).replace("\n", "<br>")

def html_to_text(h):
    t = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', h, flags=re.S | re.I)
    t = re.sub(r'<br\s*/?>', '\n', t, flags=re.I)
    t = re.sub(r'</(p|div|tr|h[1-6]|li|td)>', '\n', t, flags=re.I)
    t = re.sub(r'<[^>]+>', '', t)
    t = htmlmod.unescape(t)
    t = re.sub(r'[ \t]+\n', '\n', t)
    t = re.sub(r'\n{3,}', '\n\n', t)
    return t.strip()

@st.cache_data(show_spinner=False)
def parse_blocks(text):
    blocks, cur, started = [], {"headline": "", "body": [], "cta": "", "url": ""}, False
    def flush():
        nonlocal cur, started
        if started and (cur["headline"] or cur["body"]):
            blocks.append({"headline": cur["headline"],
                           "body": "\n".join(cur["body"]).strip(),
                           "cta": cur["cta"], "url": cur["url"]})
        cur = {"headline": "", "body": [], "cta": "", "url": ""}
        started = False
    for raw in text.splitlines():
        s = raw.strip()
        if re.fullmatch(r'-{3,}', s):
            flush(); continue
        if not s: continue
        if s.startswith("#"):
            if started and (cur["headline"] or cur["body"]): flush()
            cur["headline"] = s.lstrip("#").strip(); started = True
        elif s.startswith(">"):
            cur["cta"] = s.lstrip(">").strip(); started = True
        elif s.startswith("@"):
            cur["url"] = s.lstrip("@").strip(); started = True
        elif "|" in s and not cur["headline"] and not cur["body"]:
            parts = [p.strip() for p in s.split("|")]
            cur["headline"] = parts[0]
            if len(parts) > 1: cur["body"].append(parts[1])
            if len(parts) > 2: cur["cta"] = parts[2]
            if len(parts) > 3: cur["url"] = parts[3]
            started = True
        else:
            cur["body"].append(s); started = True
    flush()
    return blocks

@st.cache_data(show_spinner=False)
def demo_content(n):
    out = []
    for i in range(1, n + 1):
        out.append(f"# {random.choice(TOPICS)} — vol. {i}")
        out.append(" ".join(random.sample(LOREM, k=random.randint(2, 4))))
        out.append(""); out.append("> Read the full story")
        out.append("@ {rurl}"); out.append("---")
    return "\n".join(out)

def preheader_block(text):
    pad = ("&zwnj;&nbsp;" * 18)
    return (f'<div style="display:none;font-size:1px;color:#ffffff;line-height:1px;'
            f'max-height:0;max-width:0;opacity:0;overflow:hidden;mso-hide:all;">'
            f'{esc(text)}{pad}</div>')

def build_html(C):
    L, A = [], C["accent"]
    L.append('<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">')
    L.append('<meta name="viewport" content="width=device-width,initial-scale=1">')
    L.append('<meta name="color-scheme" content="light only">')
    L.append(f'<title>{esc(C["subject"])}</title>')
    L.append('<style type="text/css">')
    L.append('  html,body{margin:0!important;padding:0!important;}')
    L.append('  table{border-collapse:collapse!important;table-layout:fixed!important;margin:0 auto!important;}')
    L.append(f'  .{HIDDEN_CLASS}{{opacity:0!important;display:none!important;'
             'visibility:hidden!important;width:0!important;height:0!important;'
             'max-height:0!important;max-width:0!important;font-size:0!important;'
             'line-height:0!important;color:transparent!important;overflow:hidden!important;'
             'mso-hide:all!important;}')
    L.append('</style></head>')
    L.append(f'<body style="margin:0;padding:0;background:{C["page_bg"]};'
             'font-family:Arial,Helvetica,sans-serif;">')
    if C["preheader"]:
        L.append(preheader_block(C["preheader"]))
    L.append(f'<table role="presentation" width="100%" style="background:{C["page_bg"]};"><tr>'
             '<td align="center" style="padding:24px 12px;">')
    L.append('<table role="presentation" width="600" style="width:600px;max-width:600px;'
             'background:#ffffff;border-radius:8px;overflow:hidden;">')
    # header
    L.append(f'<tr><td style="background:{C["header_bg"]};padding:22px 28px 18px;">'
             f'<div style="font:800 22px/1.2 Arial,Helvetica,sans-serif;color:{C["header_fg"]};">'
             f'{esc(C["brand"])}</div>'
             f'<div style="font:400 12px/1.5 Arial,Helvetica,sans-serif;color:{C["header_fg"]};'
             f'opacity:.65;margin-top:5px;">{esc(C["tagline"])}</div></td></tr>')
    # hero
    if C["hero_headline"]:
        L.append(f'<tr><td style="background:{C["hero_bg"]};padding:44px 28px 40px;" align="center">'
                 f'<div style="font:800 30px/1.2 Arial,Helvetica,sans-serif;color:#ffffff;max-width:480px;">'
                 f'{esc(C["hero_headline"])}</div>'
                 f'<div style="font:400 15px/1.6 Arial,Helvetica,sans-serif;color:#ffffff;'
                 f'opacity:.78;margin-top:14px;">{esc(C["hero_sub"])}</div></td></tr>')
    # intro
    if C["intro"]:
        L.append(f'<tr><td style="padding:26px 28px 4px;font:400 15px/1.7 Arial,Helvetica,sans-serif;'
                 f'color:#3a3a3a;">{nl2br(C["intro"])}</td></tr>')
    # articles
    for i, b in enumerate(C["blocks"], start=1):
        hl = b["headline"] or f"Update #{i}"
        if C["zalgo_on"]:
            hl = zalgo(hl, C["zalgo_n"])
        L.append(f'<tr><td style="padding:24px 28px 6px;font:700 19px/1.35 Arial,Helvetica,sans-serif;'
                 f'color:#111111;">{esc(hl)}</td></tr>')
        if b["body"]:
            L.append(f'<tr><td style="padding:0 28px 16px;font:400 15px/1.68 Arial,Helvetica,sans-serif;'
                     f'color:#3a3a3a;">{nl2br(b["body"])}</td></tr>')
        cta = b["cta"] or C["default_cta"]
        url = b["url"] or C["default_url"]
        if cta:
            L.append(f'<tr><td style="padding:0 28px 24px;">'
                     f'<a href="{url}" style="display:inline-block;background:{A};color:#fff;'
                     f'text-decoration:none;font:700 13px Arial,Helvetica,sans-serif;'
                     f'padding:11px 22px;border-radius:4px;">{esc(cta)}</a></td></tr>')
    # banner
    if C["banner_headline"]:
        L.append(f'<tr><td style="background:#f5f7fb;padding:34px 28px;" align="center">'
                 f'<div style="font:800 21px/1.3 Arial,Helvetica,sans-serif;color:#111;">'
                 f'{esc(C["banner_headline"])}</div></td></tr>')
    # footer
    L.append('<tr><td style="padding:30px 28px 8px;border-top:1px solid #ececec;" align="center">'
             f'<div style="font:400 12px/1.7 Arial,Helvetica,sans-serif;color:#9a9a9a;">'
             f'{esc(C["address"])}</div>'
             f'<div style="margin-top:8px;font:400 12px Arial,Helvetica,sans-serif;">'
             f'<a href="{{{{uurl}}}}" style="color:{A};">Unsubscribe</a></div></td></tr>')
    L.append('</table></td></tr></table></body></html>')
    doc = "\n".join(L)

    if C["pad_to"] and doc.count("\n") + 1 < C["pad_to"]:
        need = C["pad_to"] - (doc.count("\n") + 1)
        doc = doc.replace('</body>',
                          "\n".join(f'<!-- filler {i+1} -->' for i in range(need)) + "\n</body>")
    return doc

def build_eml(from_addr, to_addr, subject, html_body, encode_subject, base64_body, extra_headers=""):
    boundary = "b" + uuid.uuid4().hex[:16]
    subj = rfc2047_encode(subject) if encode_subject else subject
    if base64_body:
        enc = "base64"
        payload = "\n".join(base64.b64encode(html_body.encode("utf-8")).decode("ascii")[i:i+76]
                            for i in range(0, len(base64.b64encode(html_body.encode("utf-8")).decode("ascii")), 76))
    else:
        enc = "quoted-printable"
        payload = quopri.encodestring(html_body.encode("utf-8")).decode("ascii")
    text_body = html_to_text(html_body)
    headers = [
        f"From: {from_addr}", f"To: {to_addr}", f"Subject: {subj}",
        f"Date: {formatdate(localtime=True)}", "MIME-Version: 1.0",
    ]
    if extra_headers.strip():
        headers.append(extra_headers.strip())
    headers.append(f'Content-Type: multipart/alternative; boundary="{boundary}"')
    return "\n".join([
        "\n".join(headers), "",
        f"--{boundary}", "Content-Type: text/plain; charset=utf-8",
        "Content-Transfer-Encoding: quoted-printable", "",
        quopri.encodestring(text_body.encode("utf-8")).decode("ascii"), "",
        f"--{boundary}", "Content-Type: text/html; charset=utf-8",
        f"Content-Transfer-Encoding: {enc}", "", payload, "",
        f"--{boundary}--", "",
    ])

with tabs[9]:
    st.header("Email Builder")
    st.caption("Combines everything into a single .html / .eml. This is the only tab that mixes features.")

    if "bulk" not in st.session_state:
        st.session_state.bulk = demo_content(12)

    with st.expander("📦 Bulk content", expanded=True):
        cc1, cc2 = st.columns([1, 1])
        with cc1:
            if st.button("Fill demo", key="eb_demo"):
                st.session_state.bulk = demo_content(200)
                st.rerun()
        with cc2:
            if st.button("Clear", key="eb_clear"):
                st.session_state.bulk = ""
                st.rerun()
        bulk_text = st.text_area(
            "Article blocks (`# Headline` · body · `> CTA` · `@ link` · `---` between blocks)",
            key="bulk", height=200,
        )
        intro = st.text_area("Intro paragraph", "Here's what's new this week from {domain}.",
                             height=60, key="eb_intro")

    with st.expander("🎨 Brand & hero"):
        b1, b2, b3 = st.columns(3)
        with b1:
            brand = st.text_input("Brand", "ACME Co.", key="eb_brand")
            subject = st.text_input("Subject", "This week's update", key="eb_subj")
        with b2:
            tagline = st.text_input("Tagline", "Weekly digest", key="eb_tag")
            accent_name = st.selectbox("Accent", list(ACCENTS.keys()), key="eb_acc")
        with b3:
            preheader = st.text_input("Preheader", "You don't want to miss this.", key="eb_pre")
        hero_headline = st.text_input("Hero headline", "Everything new, in one place", key="eb_hh")
        hero_sub = st.text_input("Hero subline", "Hand-picked stories from the team.", key="eb_hs")

    with st.expander("⚙️ Encoding / obfuscation"):
        c1, c2 = st.columns(2)
        with c1:
            moji_on = st.checkbox("cp1252 mojibake", False, key="eb_moji")
            ent_on = st.checkbox("Numeric entities", False, key="eb_ent")
            ent_rate = st.slider("Entity rate", 0.1, 1.0, 0.5, 0.1, key="eb_entr")
            zalgo_on = st.checkbox("Zalgo headlines", False, key="eb_zg")
            zalgo_n = st.slider("Zalgo intensity", 1, 8, 3, key="eb_zgn", disabled=not zalgo_on)
        with c2:
            ue_on = st.checkbox("Unicode-escape", False, key="eb_ue")
            ue_style = st.selectbox("Style", UNICODE_ESCAPE_STYLES, key="eb_uest", disabled=not ue_on)
            sm_on = st.checkbox("Script mojibake", False, key="eb_sm")
            sm_preset = st.selectbox("Preset", list(MOJIBAKE_PRESETS.keys()),
                                     key="eb_smp", disabled=not sm_on)
            base64_body = st.checkbox("Base64 HTML part", False, key="eb_b64")

    with st.expander("📏 Length"):
        pad_to = st.number_input("Pad to at least N lines", 0, 20000, 1000, step=100, key="eb_pad")

    blocks = parse_blocks(bulk_text)

    if moji_on:
        blocks = [{**b, "body": to_mojibake(b["body"]), "headline": to_mojibake(b["headline"])}
                  for b in blocks]
        intro = to_mojibake(intro)
    if ent_on:
        blocks = [{**b, "body": to_numeric_entities(b["body"], ent_rate)} for b in blocks]
        intro = to_numeric_entities(intro, ent_rate)
    if sm_on:
        blocks = [{**b,
                   "headline": to_script_mojibake(b["headline"], sm_preset),
                   "body": to_script_mojibake(b["body"], sm_preset)}
                  for b in blocks]
        intro = to_script_mojibake(intro, sm_preset)
    if ue_on:
        blocks = [{**b,
                   "headline": to_unicode_escape(b["headline"], ue_style),
                   "body": to_unicode_escape(b["body"], ue_style)} for b in blocks]
        intro = to_unicode_escape(intro, ue_style)

    C = dict(
        subject=subject, accent=ACCENTS[accent_name], page_bg="#f2f2f2",
        brand=brand, tagline=tagline,
        header_bg="#111111", header_fg="#ffffff",
        hero_headline=hero_headline, hero_sub=hero_sub,
        hero_bg="#0f172a",
        preheader=preheader, intro=intro, blocks=blocks,
        default_cta="Read more", default_url="{rurl}",
        banner_headline="Ready to get started?",
        domain="{domain}", address="ACME Co. · 1 Main St, Springfield · © 2025",
        zalgo_on=zalgo_on, zalgo_n=zalgo_n, pad_to=int(pad_to),
    )

    html_out = build_html(C)
    eml_out = build_eml("news@{domain}", "{name} <you@example.com>", subject, html_out,
                        False, base64_body)

    m1, m2, m3 = st.columns(3)
    m1.metric("HTML lines", f"{html_out.count(chr(10))+1:,}")
    m2.metric("HTML size", f"{len(html_out.encode('utf-8'))/1024:.1f} KB")
    m3.metric("Blocks", f"{len(blocks):,}")

    d1, d2 = st.columns(2)
    d1.download_button("⬇ .html", html_out, file_name="template.html",
                       mime="text/html", use_container_width=True)
    d2.download_button("⬇ .eml", eml_out, file_name="template.eml",
                       mime="message/rfc822", use_container_width=True)

    with st.expander("👁 Preview"):
        preview = (html_out.replace("{name}", "Alex").replace("{domain}", "example.com")
                   .replace("{ourl}", "#").replace("{rurl}", "#")
                   .replace("{uurl}", "#").replace("{iurl}", ""))
        st.components.v1.html(preview, height=600, scrolling=True)

    with st.expander("📄 HTML source"):
        st.code(html_out[:50000], language="html")
