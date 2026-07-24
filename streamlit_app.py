"""Streamlit version of the Video-to-Slides converter.

Run locally:
    pip install -r requirements.txt
    streamlit run streamlit_app.py

Architecture note: conversions run as BACKGROUND JOBS on the server
(slide_extractor.jobs.JobManager), decoupled from the browser session.
The job id is stored in the page URL (?job=...), so a dropped
websocket, a phone screen turning off, or even closing the tab does NOT
lose the work — reopening the same URL shows live progress or the
finished results. This is essential for hours-long videos.
"""

import os

import streamlit as st

from slide_extractor import __version__, build_pdf, probe_video
from slide_extractor.downloader import js_runtime_status
from slide_extractor.jobs import JobManager
from slide_extractor.pot_server import ensure_pot_server

st.set_page_config(page_title="فيديو إلى شرائح — Video to Slides",
                   page_icon="🎬", layout="wide")

# Start the PO-token server (unlocks >360p qualities); runs npm install
# in the background on the very first boot, no-op afterwards.
ensure_pot_server()

# Allow configuring a download proxy and custom mirror instances via
# Streamlit Cloud secrets (e.g. your own cobalt/Invidious server).
try:
    for _key in ("YTDLP_PROXY", "V2S_COBALT_INSTANCES",
                 "V2S_INVIDIOUS_INSTANCES", "V2S_PIPED_INSTANCES"):
        if _key in st.secrets:
            os.environ[_key] = st.secrets[_key]
except Exception:
    pass  # no secrets file configured


@st.cache_resource
def get_manager() -> JobManager:
    return JobManager(root=os.environ.get("OUTPUT_DIR", "output"))


manager = get_manager()

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

STATUS_AR = {
    "queued": "في الانتظار…",
    "downloading": "⬇️ جارٍ تحميل الفيديو…",
    "extracting": "🔍 جارٍ التحليل واستخراج الشرائح…",
}


def show_download_error(msg: str, attempt_log=None):
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


AUTH_COOKIES = {"SID", "__Secure-1PSID", "__Secure-3PSID", "LOGIN_INFO",
                "SAPISID"}


def save_cookies(upload) -> str:
    """Persist the uploaded cookies.txt and report what it contains.

    Called on EVERY rerun while a file is attached — not only when a
    button is pressed — so cookies count no matter when they were
    uploaded relative to the probe. The file lives under the job root
    (not a temp dir) so it stays valid for the whole conversion.
    """
    if upload is None:
        return ""
    if "session_tag" not in st.session_state:
        st.session_state["session_tag"] = os.urandom(6).hex()
    dest_dir = os.path.join(manager.root, "cookies")
    os.makedirs(dest_dir, exist_ok=True)
    path = os.path.join(dest_dir,
                        f"{st.session_state['session_tag']}_cookies.txt")
    data = upload.getvalue()
    with open(path, "wb") as f:
        f.write(data)

    # Immediate feedback: a silently-ignored cookie file was exactly the
    # failure mode this replaces.
    try:
        from yt_dlp.cookies import load_cookies
        jar = load_cookies(path, None, None)
        names = {c.name for c in jar if "youtube.com" in c.domain}
        missing = AUTH_COOKIES - names
        if missing:
            st.warning(
                f"⚠️ الملف مقروء ({len(names)} كوكي ليوتيوب) لكن تنقصه "
                f"كوكيز تسجيل الدخول: {', '.join(sorted(missing))} — "
                "تأكد أنك سجّلت دخولك في يوتيوب قبل التصدير.")
        else:
            st.success(f"✅ ملف الكوكيز جاهز وسيُستخدم في التحميل "
                       f"({len(names)} كوكي ليوتيوب، كوكيز تسجيل الدخول "
                       f"موجودة).")
    except Exception as exc:
        st.error(f"⚠️ تعذّرت قراءة ملف الكوكيز — تأكد أنه بصيغة Netscape "
                 f"من إضافة *Get cookies.txt LOCALLY*. ({exc})")
        return ""
    return path


def start_job_and_go(job):
    st.query_params["job"] = job.id
    st.rerun()


# ======================================================================
# JOB VIEW — rendered when the URL carries ?job=...; survives reconnects
# ======================================================================
def render_job(job):
    top = st.container()
    with top:
        if st.button("🆕 بدء تحويل جديد", use_container_width=False):
            st.query_params.clear()
            st.rerun()

    if job.status in ("queued", "downloading", "extracting"):
        st.info("⏳ التحويل يعمل على الخادم في الخلفية — **يمكنك إغلاق "
                "الصفحة والعودة لاحقاً بنفس الرابط**، لن يضيع عملك.")

        @st.fragment(run_every="2s")
        def poll():
            j = manager.get(job.id)
            if j is None:
                st.error("المهمة لم تعد موجودة (أعيد تشغيل الخادم؟)")
                return
            if j.status in ("done", "error"):
                st.rerun(scope="app")
            label = STATUS_AR.get(j.status, j.status)
            detail = f" ({j.message})" if j.message and "MB" in j.message \
                else (f" — {j.message}" if j.message else "")
            st.progress(min(max(j.progress, 0.0), 1.0),
                        text=f"{label} {j.progress * 100:.0f}%{detail}")
            if j.title:
                st.caption(f"🎥 {j.title}")

        poll()
        return

    if job.status == "error":
        show_download_error(job.error, job.attempt_log)
        return

    # ----- done -----
    quality_note = (f" — الجودة الفعلية: {job.actual_height}p"
                    if job.actual_height else "")
    st.success(f"✅ تم استخراج {len(job.slides)} شريحة من: "
               f"{job.title or 'الفيديو'}{quality_note}")
    if (job.exact_height and job.actual_height
            and job.actual_height != job.max_height):
        st.warning(
            f"⚠️ طلبت {job.max_height}p لكن كل القنوات المتاحة رفضت هذه "
            f"الجودة، فتم التحميل بأفضل جودة ممكنة: **{job.actual_height}p** "
            f"(مقاسة من الملف نفسه).")
        with st.expander("سجل المحاولات"):
            st.code("\n".join(job.attempt_log) or "(فارغ)")

    slides_dir = os.path.join(job.workdir, "slides")
    st.markdown("### الشرائح المستخرجة — ألغِ تحديد ما لا تريده في الـ PDF")
    cols_per_row = 4
    for row_start in range(0, len(job.slides), cols_per_row):
        cols = st.columns(cols_per_row)
        for col, s in zip(cols, job.slides[row_start:row_start + cols_per_row]):
            with col:
                img_path = os.path.join(slides_dir, s["file"])
                if os.path.isfile(img_path):
                    st.image(img_path, use_container_width=True)
                mins, secs = divmod(int(s["timestamp"]), 60)
                st.checkbox(f"شريحة {s['index'] + 1} — ⏱ {mins}:{secs:02d}",
                            value=True, key=f"keep_{job.id}_{s['index']}")

    selected = [s for s in job.slides
                if st.session_state.get(f"keep_{job.id}_{s['index']}", True)]

    c1, c2 = st.columns(2)
    with c1:
        pdf_path = None
        if len(selected) == len(job.slides):
            pdf_path = os.path.join(job.workdir, "slides.pdf")
        elif selected:
            pdf_path = os.path.join(job.workdir, "slides_custom.pdf")
            build_pdf([os.path.join(slides_dir, s["file"]) for s in selected],
                      pdf_path)
        if pdf_path and os.path.isfile(pdf_path):
            with open(pdf_path, "rb") as f:
                st.download_button(
                    f"⬇️ تحميل PDF ({len(selected)} شريحة)", f,
                    file_name="slides.pdf", mime="application/pdf",
                    use_container_width=True, type="primary")
        else:
            st.warning("اختر شريحة واحدة على الأقل.")
    with c2:
        zip_path = os.path.join(job.workdir, "slides.zip")
        if os.path.isfile(zip_path):
            with open(zip_path, "rb") as f:
                st.download_button("⬇️ تحميل كل الصور ZIP", f,
                                   file_name="slides.zip",
                                   mime="application/zip",
                                   use_container_width=True)


# ======================================================================
# INPUT VIEW — no active job in the URL
# ======================================================================
def render_inputs():
    sens_label = st.selectbox("دقة الاستخراج", list(SENSITIVITY_LABELS),
                              index=1)
    sensitivity = SENSITIVITY_LABELS[sens_label]

    tab_url, tab_file = st.tabs(["🔗 رابط يوتيوب", "📁 رفع ملف من جهازك"])

    # ---------------------------------------------------------- URL tab
    with tab_url:
        url = st.text_input("رابط الفيديو",
                            placeholder="https://www.youtube.com/watch?v=...")
        with st.expander("⚙️ خيارات متقدمة — إذا رفض يوتيوب التحميل من الخادم"):
            st.markdown(
                "يوتيوب يحجب التحميل من خوادم السحابة، ويطلب حرفياً تسجيل "
                "الدخول (*Sign in to confirm you're not a bot*). التطبيق "
                "يجرّب تلقائياً عدة عملاء، ثم خدمة **Cobalt**، ثم شبكات "
                "المرايا الحية — وإذا استمر الرفض فالحل الحاسم هو ملف "
                "`cookies.txt`:\n\n"
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
            # Saved on every rerun, so cookies apply whether they were
            # attached before or after the probe.
            cookies_path = save_cookies(cookies_upload)

        if st.button("🔍 فحص الفيديو ومعرفة الجودات المتاحة",
                     use_container_width=True):
            if not url.strip():
                st.error("أدخل رابط الفيديو أولاً.")
            else:
                st.session_state.pop("probe", None)
                try:
                    with st.spinner("جارٍ قراءة معلومات الفيديو وجوداته "
                                    "الحقيقية…"):
                        probe = probe_video(url.strip(),
                                            cookies_file=cookies_path or None)
                    st.session_state["probe"] = probe
                    st.session_state["probe_url"] = url.strip()
                except Exception as exc:
                    show_download_error(str(exc))

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
                diag = probe.get("diagnostics") or []
                fmts = probe.get("formats_count")
                with st.expander("لماذا لم تظهر الجودات؟ (تفاصيل تقنية)"):
                    st.write(f"محرك جافاسكربت: **{js_runtime_status()}**")
                    if fmts is not None:
                        st.write(f"عدد الصيغ التي أعادها يوتيوب: "
                                 f"**{fmts}** — صالحة للفيديو: **0**")
                    if diag:
                        st.code("\n".join(diag[-25:]))
                chosen_height = 4320
                exact = False

            if cookies_path:
                st.caption("🍪 سيتم استخدام ملف الكوكيز في هذا التحويل.")
            if st.button("🚀 استخراج الشرائح", type="primary",
                         use_container_width=True):
                job = manager.create(
                    url.strip(), sensitivity=sensitivity,
                    max_height=chosen_height, exact_height=exact,
                    source_hint=probe.get("source") or "",
                    cookies_file=cookies_path)
                job.title = probe.get("title") or ""
                start_job_and_go(job)

    # --------------------------------------------------------- File tab
    with tab_file:
        uploaded = st.file_uploader(
            "ملف الفيديو (بدون حد عملي للحجم — حتى 4GB)",
            type=["mp4", "webm", "mkv", "avi", "mov"])
        if uploaded is not None and st.button("🚀 استخراج الشرائح من الملف",
                                              type="primary",
                                              use_container_width=True):
            uploads = os.path.join(manager.root, "uploads")
            os.makedirs(uploads, exist_ok=True)
            video_path = os.path.join(
                uploads, f"{os.urandom(6).hex()}_{uploaded.name}")
            # Chunked copy: a movie-sized upload must not be duplicated
            # in RAM on small cloud containers.
            import shutil as _shutil
            uploaded.seek(0)
            with open(video_path, "wb") as f:
                _shutil.copyfileobj(uploaded, f, length=4 << 20)
            title = os.path.splitext(uploaded.name)[0]
            job = manager.create_from_file(video_path, title=title,
                                           sensitivity=sensitivity)
            start_job_and_go(job)


# ======================================================================
job_id = st.query_params.get("job")
active_job = manager.get(job_id) if job_id else None
if job_id and active_job is None:
    st.warning("انتهت صلاحية هذه المهمة (أعيد تشغيل الخادم أو حُذفت لقدمها). "
               "ابدأ تحويلاً جديداً.")
    if st.button("موافق"):
        st.query_params.clear()
        st.rerun()
elif active_job is not None:
    render_job(active_job)
else:
    render_inputs()

st.divider()
st.caption(f"الإصدار {__version__} — مبني بمكتبات مفتوحة المصدر: yt-dlp · "
           "OpenCV · ImageHash · img2pdf · Streamlit")
