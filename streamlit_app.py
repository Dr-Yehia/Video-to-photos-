"""Streamlit version of the Video-to-Slides converter.

Run locally:
    pip install -r requirements.txt
    streamlit run streamlit_app.py

Flow for URLs: the video is PROBED first (title, duration and the list
of qualities that actually exist in it), the user picks one of the real
qualities, then extraction runs. Nothing is assumed about the video.
"""

import os
import tempfile

import streamlit as st

from slide_extractor import (ExtractorConfig, SlideExtractor, __version__,
                             build_pdf, build_zip, download_video,
                             probe_video)
from slide_extractor.pot_server import ensure_pot_server

# Start the PO-token server (unlocks >360p qualities); runs npm install
# in the background on the very first boot, no-op afterwards.
ensure_pot_server()

st.set_page_config(page_title="فيديو إلى شرائح — Video to Slides",
                   page_icon="🎬", layout="wide")

# Allow configuring a download proxy and custom mirror instances via
# Streamlit Cloud secrets (e.g. your own cobalt/Invidious server).
try:
    for _key in ("YTDLP_PROXY", "V2S_COBALT_INSTANCES",
                 "V2S_INVIDIOUS_INSTANCES", "V2S_PIPED_INSTANCES"):
        if _key in st.secrets:
            os.environ[_key] = st.secrets[_key]
except Exception:
    pass  # no secrets file configured

# RTL support for the Arabic interface
st.markdown(
    """
    <style>
    .stApp { direction: rtl; }
    .stMarkdown, .stText, h1, h2, h3, p { text-align: right; }
    div[data-testid="stSelectbox"] label, div[data-testid="stFileUploader"] label,
    div[data-testid="stTextInput"] label { direction: rtl; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🎬 فيديو إلى شرائح 📄")
st.markdown(
    "حوّل أي فيديو يوتيوب (أو ملف من جهازك) إلى **صور + ملف PDF** بأعلى جودة — "
    "يلتقط كل شريحة في أكمل حالتها بعد انتهاء الكتابة عليها، بدون تكرار."
)

SENSITIVITY_LABELS = {
    "منخفضة — التغييرات الكبيرة فقط": "low",
    "متوسطة — موصى بها": "medium",
    "عالية — يلتقط تغييرات أدق": "high",
}


def show_download_error(exc: Exception, attempt_log=None):
    msg = str(exc)
    low = msg.lower()
    if "drm" in low:
        st.error(
            "🔐 أبلغ يوتيوب أن هذه النسخة محمية (DRM) — غالباً بلاغ خاطئ "
            "يحدث مع بعض الخوادم السحابية رغم أن الفيديو عادي. الحلول:\n\n"
            "1. **ارفع ملف cookies.txt** من \"الخيارات المتقدمة\".\n"
            "2. **شغّل التطبيق على جهازك** — يعمل مباشرة.\n"
            "3. **ارفع ملف الفيديو مباشرة** بدل الرابط."
        )
    elif "403" in low or "forbidden" in low:
        st.error(
            "🚫 يوتيوب يحجب التحميل من عنوان هذا الخادم السحابي (خطأ 403) "
            "رغم تجربة عدة طرق تلقائياً. الحلول:\n\n"
            "1. **شغّل التطبيق على جهازك** — يعمل مباشرة بدون أي مشكلة.\n"
            "2. **ارفع ملف cookies.txt** من \"الخيارات المتقدمة\".\n"
            "3. **ارفع ملف الفيديو مباشرة** بدل الرابط."
        )
    elif any(k in low for k in ("proxy", "unable to connect", "timed out",
                                "getaddrinfo")):
        st.error("تعذر الوصول إلى يوتيوب من هذا الخادم — جرّب من شبكة أخرى "
                 "أو ارفع ملف الفيديو مباشرة.")
    else:
        st.error(f"فشل التنفيذ: {msg}")
        if attempt_log:
            with st.expander("سجل المحاولات"):
                st.code("\n".join(attempt_log))
        return
    with st.expander("التفاصيل التقنية"):
        st.code(msg)
        if attempt_log:
            st.code("\n".join(attempt_log))


def run_pipeline(video_path: str, sensitivity: str, workdir: str,
                 title: str) -> dict:
    """Extract slides then build PDF + ZIP; returns result paths."""
    bar = st.progress(0.0, text="🔍 جارٍ تحليل الفيديو واستخراج الشرائح…")

    def on_progress(p, msg):
        bar.progress(min(p, 1.0), text=f"🔍 جارٍ التحليل… {p * 100:.0f}%")

    extractor = SlideExtractor(ExtractorConfig.from_sensitivity(sensitivity))
    slides_dir = os.path.join(workdir, "slides")
    slides = extractor.extract(video_path, slides_dir, progress=on_progress)
    if not slides:
        raise RuntimeError("لم يتم العثور على شرائح — جرّب دقة استخراج أعلى.")

    bar.progress(1.0, text="📄 جارٍ بناء ملف الـ PDF…")
    paths = [s.path for s in slides]
    pdf = build_pdf(paths, os.path.join(workdir, "slides.pdf"))
    zipf = build_zip(paths, os.path.join(workdir, "slides.zip"))
    bar.empty()
    return {
        "title": title,
        "workdir": workdir,
        "slides": [{"index": s.index, "timestamp": s.timestamp,
                    "path": s.path} for s in slides],
        "pdf": pdf,
        "zip": zipf,
    }


def save_cookies(upload, workdir: str):
    if upload is None:
        return None
    path = os.path.join(workdir, "cookies.txt")
    with open(path, "wb") as f:
        f.write(upload.getbuffer())
    return path


sens_label = st.selectbox("دقة الاستخراج", list(SENSITIVITY_LABELS), index=1)
sensitivity = SENSITIVITY_LABELS[sens_label]

tab_url, tab_file = st.tabs(["🔗 رابط يوتيوب", "📁 رفع ملف من جهازك"])

# ---------------------------------------------------------------- URL tab
with tab_url:
    url = st.text_input("رابط الفيديو",
                        placeholder="https://www.youtube.com/watch?v=...")
    with st.expander("⚙️ خيارات متقدمة — إذا رفض يوتيوب التحميل من الخادم"):
        st.markdown(
            "يوتيوب يحجب التحميل من خوادم السحابة، ويطلب حرفياً تسجيل "
            "الدخول (*Sign in to confirm you're not a bot*). التطبيق يجرّب "
            "تلقائياً عدة عملاء، ثم خدمة **Cobalt** (محرك مواقع التحميل "
            "الكبيرة — يجلب الفيديو بدون صوت بخوادمه هو)، ثم شبكات المرايا "
            "الحية — وإذا استمر الرفض فالحل الحاسم هو ملف `cookies.txt`:\n\n"
            "**خطوات الحصول عليه (من كمبيوتر):**\n"
            "1. ثبّت إضافة **Get cookies.txt LOCALLY** في متصفح كروم.\n"
            "2. افتح `youtube.com` وسجّل دخولك بحسابك.\n"
            "3. اضغط أيقونة الإضافة ← **Export** — سيُحفظ ملف "
            "`cookies.txt`.\n"
            "4. ارفعه هنا، ثم أعد الفحص والاستخراج.\n\n"
            "بديل أقوى للاستخدام الدائم: بروكسي سكني في إعدادات التطبيق "
            "(Secrets): `YTDLP_PROXY = \"http://user:pass@host:port\"`."
        )
        cookies_upload = st.file_uploader("ملف cookies.txt (اختياري)",
                                          type=["txt"])

    if st.button("🔍 فحص الفيديو ومعرفة الجودات المتاحة",
                 use_container_width=True):
        if not url.strip():
            st.error("أدخل رابط الفيديو أولاً.")
        else:
            st.session_state.pop("result", None)
            st.session_state.pop("probe", None)
            try:
                workdir = tempfile.mkdtemp(prefix="v2s_")
                cookies_path = save_cookies(cookies_upload, workdir)
                with st.spinner("جارٍ قراءة معلومات الفيديو وجوداته الحقيقية…"):
                    probe = probe_video(url.strip(),
                                        cookies_file=cookies_path)
                st.session_state["probe"] = probe
                st.session_state["probe_url"] = url.strip()
                st.session_state["probe_workdir"] = workdir
                st.session_state["probe_cookies"] = cookies_path
            except Exception as exc:
                show_download_error(exc)

    probe = st.session_state.get("probe")
    if probe and st.session_state.get("probe_url") == url.strip():
        mins, secs = divmod(int(probe["duration"] or 0), 60)
        dur = f"{mins}:{secs:02d}" if probe["duration"] else "غير معروفة"
        st.success(f"🎥 **{probe['title']}** — المدة: {dur}")

        if probe["heights"]:
            labels = [f"{h}p" for h in probe["heights"]]
            st.markdown("**الجودات المتاحة فعلياً في هذا الفيديو:** "
                        + " · ".join(labels))
            choice = st.selectbox("اختر الجودة", labels, index=0)
            chosen_height = int(choice.rstrip("p"))
            exact = True
        else:
            st.info("تعذرت قراءة قائمة الجودات — سيتم تحميل أفضل جودة "
                    "متاحة تلقائياً.")
            chosen_height = 4320  # i.e. no cap: best the video offers
            exact = False

        if st.button("🚀 استخراج الشرائح", type="primary",
                     use_container_width=True):
            st.session_state.pop("result", None)
            attempt_log = []
            try:
                workdir = st.session_state["probe_workdir"]
                bar = st.progress(0.0, text="⬇️ جارٍ تحميل الفيديو…")

                def dl_progress(p, msg):
                    label = ("⬇️ جارٍ التحميل عبر المرايا… "
                             if "mirror" in msg else "⬇️ جارٍ التحميل… ")
                    detail = f" ({msg})" if "MB" in msg else ""
                    bar.progress(min(p, 1.0),
                                 text=f"{label}{p * 100:.0f}%{detail}")

                info = download_video(
                    url.strip(), workdir, max_height=chosen_height,
                    progress=dl_progress, exact_height=exact,
                    source_hint=probe.get("source"),
                    attempt_log=attempt_log,
                    cookies_file=st.session_state.get("probe_cookies"))
                bar.empty()

                actual = info.get("actual_height") or 0
                if exact and actual and actual != chosen_height:
                    st.warning(
                        f"⚠️ طلبت {chosen_height}p لكن كل القنوات المتاحة "
                        f"رفضت هذه الجودة، فتم التحميل بأفضل جودة ممكنة: "
                        f"**{actual}p** (مقاسة من الملف نفسه).")
                    with st.expander("سجل المحاولات — لماذا لم تنجح "
                                     f"{chosen_height}p؟"):
                        st.code("\n".join(attempt_log) or "(فارغ)")

                title = (probe.get("title")
                         if probe.get("title") not in (None, "", "video")
                         else info["title"])
                result = run_pipeline(
                    info["path"], sensitivity, workdir, title)
                result["actual_height"] = actual
                st.session_state["result"] = result
            except Exception as exc:
                show_download_error(exc, attempt_log)

# --------------------------------------------------------------- File tab
with tab_file:
    uploaded = st.file_uploader(
        "ملف الفيديو (بدون حد عملي للحجم — حتى 4GB)",
        type=["mp4", "webm", "mkv", "avi", "mov"])
    if uploaded is not None and st.button("🚀 استخراج الشرائح من الملف",
                                          type="primary",
                                          use_container_width=True):
        st.session_state.pop("result", None)
        try:
            workdir = tempfile.mkdtemp(prefix="v2s_")
            video_path = os.path.join(workdir, uploaded.name)
            with open(video_path, "wb") as f:
                f.write(uploaded.getbuffer())
            title = os.path.splitext(uploaded.name)[0]
            st.session_state["result"] = run_pipeline(
                video_path, sensitivity, workdir, title)
        except Exception as exc:
            show_download_error(exc)

# ----------------------------------------------------------------- Results
result = st.session_state.get("result")
if result:
    slides = result["slides"]
    quality_note = (f" — الجودة الفعلية: {result['actual_height']}p"
                    if result.get("actual_height") else "")
    st.success(f"✅ تم استخراج {len(slides)} شريحة من: "
               f"{result['title']}{quality_note}")

    st.markdown("### الشرائح المستخرجة — ألغِ تحديد ما لا تريده في الـ PDF")
    cols_per_row = 4
    for row_start in range(0, len(slides), cols_per_row):
        cols = st.columns(cols_per_row)
        for col, s in zip(cols, slides[row_start:row_start + cols_per_row]):
            with col:
                st.image(s["path"], use_container_width=True)
                mins, secs = divmod(int(s["timestamp"]), 60)
                st.checkbox(f"شريحة {s['index'] + 1} — ⏱ {mins}:{secs:02d}",
                            value=True, key=f"keep_{s['index']}")

    selected = [s for s in slides
                if st.session_state.get(f"keep_{s['index']}", True)]

    c1, c2 = st.columns(2)
    with c1:
        if len(selected) == len(slides):
            pdf_path = result["pdf"]
        elif selected:
            pdf_path = os.path.join(result["workdir"], "slides_custom.pdf")
            build_pdf([s["path"] for s in selected], pdf_path)
        else:
            pdf_path = None
        if pdf_path:
            with open(pdf_path, "rb") as f:
                st.download_button(
                    f"⬇️ تحميل PDF ({len(selected)} شريحة)", f,
                    file_name="slides.pdf", mime="application/pdf",
                    use_container_width=True, type="primary")
        else:
            st.warning("اختر شريحة واحدة على الأقل.")
    with c2:
        with open(result["zip"], "rb") as f:
            st.download_button("⬇️ تحميل كل الصور ZIP", f,
                               file_name="slides.zip", mime="application/zip",
                               use_container_width=True)

st.divider()
st.caption(f"الإصدار {__version__} — مبني بمكتبات مفتوحة المصدر: yt-dlp · "
           "OpenCV · ImageHash · img2pdf · Streamlit")
