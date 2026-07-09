"""Streamlit version of the Video-to-Slides converter.

Run locally:
    pip install -r requirements.txt
    streamlit run streamlit_app.py

Can also be deployed for free on Streamlit Community Cloud. Note that
YouTube frequently blocks downloads coming from cloud datacenter IPs,
so on a hosted deployment the "upload a video file" mode is the
reliable path; on your own machine YouTube links work normally.
"""

import os
import tempfile

import streamlit as st

from slide_extractor import (ExtractorConfig, SlideExtractor, build_pdf,
                             build_zip, download_video)

st.set_page_config(page_title="فيديو إلى شرائح — Video to Slides",
                   page_icon="🎬", layout="wide")

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

with st.form("input_form"):
    url = st.text_input("🔗 رابط الفيديو",
                        placeholder="https://www.youtube.com/watch?v=...")
    uploaded = st.file_uploader("📁 أو ارفع ملف فيديو من جهازك",
                                type=["mp4", "webm", "mkv", "avi", "mov"])
    col1, col2 = st.columns(2)
    with col1:
        sens_label = st.selectbox("دقة الاستخراج",
                                  list(SENSITIVITY_LABELS), index=1)
    with col2:
        quality = st.selectbox("جودة تحميل الفيديو", [720, 1080], index=1,
                               format_func=lambda q: f"{q}p")
    with st.expander("⚙️ خيارات متقدمة — إذا رفض يوتيوب التحميل من الخادم"):
        st.markdown(
            "يوتيوب يحجب أحياناً التحميل من خوادم السحابة (خطأ 403). "
            "التطبيق يجرّب تلقائياً عدة طرق، وإذا استمر الرفض يمكنك رفع ملف "
            "`cookies.txt` من متصفحك (عبر إضافة مثل *Get cookies.txt LOCALLY*) "
            "ليتم التحميل بحسابك."
        )
        cookies_upload = st.file_uploader("ملف cookies.txt (اختياري)",
                                          type=["txt"])
    submitted = st.form_submit_button("🚀 استخراج الشرائح",
                                      use_container_width=True)


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


if submitted:
    st.session_state.pop("result", None)
    try:
        workdir = tempfile.mkdtemp(prefix="v2s_")
        if uploaded is not None:
            video_path = os.path.join(workdir, uploaded.name)
            with open(video_path, "wb") as f:
                f.write(uploaded.getbuffer())
            title = os.path.splitext(uploaded.name)[0]
        elif url.strip():
            bar = st.progress(0.0, text="⬇️ جارٍ تحميل الفيديو من يوتيوب…")

            def dl_progress(p, msg):
                bar.progress(min(p, 1.0),
                             text=f"⬇️ جارٍ التحميل… {p * 100:.0f}%")

            cookies_path = None
            if cookies_upload is not None:
                cookies_path = os.path.join(workdir, "cookies.txt")
                with open(cookies_path, "wb") as f:
                    f.write(cookies_upload.getbuffer())

            info = download_video(url.strip(), workdir,
                                  max_height=int(quality),
                                  progress=dl_progress,
                                  cookies_file=cookies_path)
            bar.empty()
            video_path, title = info["path"], info["title"]
        else:
            st.error("أدخل رابط فيديو أو ارفع ملفاً أولاً.")
            st.stop()

        st.session_state["result"] = run_pipeline(
            video_path, SENSITIVITY_LABELS[sens_label], workdir, title)
    except Exception as exc:
        msg = str(exc)
        low = msg.lower()
        if "403" in low or "forbidden" in low:
            st.error(
                "🚫 يوتيوب يحجب التحميل من عنوان هذا الخادم السحابي (خطأ 403) "
                "رغم تجربة عدة طرق تلقائياً. الحلول:\n\n"
                "1. **شغّل التطبيق على جهازك** — يعمل مباشرة بدون أي مشكلة.\n"
                "2. **ارفع ملف cookies.txt** من \"الخيارات المتقدمة\" أعلاه.\n"
                "3. **ارفع ملف الفيديو مباشرة** بدل الرابط (حمّله على جهازك "
                "أولاً ثم ارفعه هنا)."
            )
            with st.expander("التفاصيل التقنية"):
                st.code(msg)
        elif any(k in low for k in ("proxy", "unable to connect",
                                    "timed out", "getaddrinfo")):
            st.error("تعذر الوصول إلى يوتيوب من هذا الخادم — جرّب من شبكة "
                     "أخرى أو ارفع ملف الفيديو مباشرة.")
            with st.expander("التفاصيل التقنية"):
                st.code(msg)
        else:
            st.error(f"فشل الاستخراج: {msg}")

result = st.session_state.get("result")
if result:
    slides = result["slides"]
    st.success(f"✅ تم استخراج {len(slides)} شريحة من: {result['title']}")

    # Selection state survives reruns via the checkbox keys
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
st.caption("مبني بمكتبات مفتوحة المصدر: yt-dlp · OpenCV · ImageHash · "
           "img2pdf · Streamlit")
