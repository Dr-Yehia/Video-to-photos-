# 🎬 فيديو إلى شرائح — Video to Slides 📄

حوّل أي فيديو يوتيوب (أو ملف فيديو من جهازك) إلى **صور + ملف PDF** بأعلى جودة ممكنة.

كثير من المحاضرات والشروحات على يوتيوب لا يرفق أصحابها ملفات العرض — هذا المشروع يستخرجها لك تلقائياً وبذكاء.

## ✨ ما الذي يميّزه؟

المشكلة الأصعب في استخراج الشرائح: الشارح يكتب على الشريحة **تدريجياً** (سطر، نقطة، كلمة…). الأدوات الساذجة تعتبر كل ضغطة قلم "صفحة جديدة" فتنتج آلاف الصفحات. هذا المشروع يحلّها بخوارزمية ذكية:

- ✍️ **الكتابة تضيف ولا تمحو**: طالما المحتوى القديم باقٍ والجديد يُضاف، فهي نفس الشريحة — ويُحتفظ دائماً بأحدث نسخة، فتُلتقط الشريحة **بعد اكتمال الكتابة عليها**.
- 📄 **قلب الصفحة يمحو المحتوى**: عندما تختفي حواف المحتوى السابق (أو تتغير ألوان مساحة كبيرة) تُعتبر صفحة جديدة وتُطبع الشريحة السابقة في أكمل حالاتها.
- 🌫️ **الانتقالات لا تُلتقط**: التلاشي (fade) وحركة الكاميرا لا تنتج إطارات مستقرة، فتُهمل تلقائياً — لن تحصل أبداً على صورة "نصف انتقال".
- 🔁 **إزالة التكرار**: إذا رجع الشارح لصفحة سابقة، تُحذف النسخة المكررة ويُحتفظ بالنسخة الأغنى محتوىً (الأكثر "حبراً").
- 🖼️ **جودة بلا فقدان**: الـ PDF يُبنى بـ img2pdf الذي يضمّن الصور كما هي بدون إعادة ضغط.

## 🧩 المكتبات مفتوحة المصدر المستخدمة

| المكتبة | الدور |
|---|---|
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | تحميل الفيديو من يوتيوب (وأكثر من 1000 موقع آخر) |
| [OpenCV](https://opencv.org/) | قراءة الإطارات وتحليل التغيّر البصري |
| [ImageHash](https://github.com/JohannesBuchner/imagehash) | البصمة الإدراكية لإزالة الشرائح المكررة |
| [img2pdf](https://gitlab.mister-muffin.de/josch/img2pdf) | تجميع الصور في PDF بدون فقدان جودة |
| [FastAPI](https://fastapi.tiangolo.com/) + Uvicorn | خادم الموقع |
| [imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg) | نسخة ffmpeg جاهزة بدون تثبيت يدوي |

## 🚀 التشغيل

### الطريقة 1: Streamlit (الأسهل — موصى بها على اللابتوب)

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

يفتح المتصفح تلقائياً. يمكن نشره مجاناً على [Streamlit Community Cloud](https://streamlit.io/cloud) — لكن انتبه: يوتيوب كثيراً ما يحجب التحميل من خوادم السحابة، فاستخدم خيار "رفع ملف" هناك، أما على جهازك فروابط يوتيوب تعمل طبيعياً.

### الطريقة 2: FastAPI

```bash
pip install -r requirements.txt
python app.py
```

ثم افتح المتصفح على: **http://localhost:8000**

1. الصق رابط الفيديو (أو ارفع ملفاً من جهازك) واضغط "استخراج الشرائح".
2. تابع شريط التقدم (تحميل ← تحليل ← استخراج).
3. راجع الشرائح، ألغِ تحديد ما لا تريده.
4. حمّل **PDF** أو **ZIP** بكل الصور.

## 💻 سطر الأوامر (CLI)

```bash
# من يوتيوب
python cli.py "https://www.youtube.com/watch?v=XXXX" -o my_slides

# من ملف محلي، بحساسية عالية، مع ZIP
python cli.py lecture.mp4 -s high --zip
```

| خيار | الوصف |
|---|---|
| `-o, --output` | مجلد الإخراج (افتراضي: `slides_output`) |
| `-s, --sensitivity` | `low` / `medium` / `high` — كم تغييراً يُعتبر صفحة جديدة |
| `-q, --quality` | أقصى دقة للتحميل (افتراضي 1080) |
| `--no-pdf` / `--zip` | تخطي الـ PDF / إنشاء ZIP إضافي |

## 🧠 كيف تعمل الخوارزمية؟ (للمطورين)

1. **أخذ عينات**: إطار واحد كل ثانية (grab-skip سريع بدون فك ترميز كل الإطارات).
2. **مقارنة ملونة**: تصغير + تمويه ثم قياس نسبة البكسلات المتغيرة (أقوى قناة لونية لكل بكسل) — التمويه يخفي المؤشر وضجيج الضغط.
3. **كشف المحو**: حواف Canny للإطار السابق تُقارن بحواف الحالي الموسّعة — النسبة المختفية = محتوى مُسح = صفحة جديدة.
4. **الإطار المستقر**: لا تُعتمد إلا الإطارات التي لم يتغير قبلها شيء تقريباً، فلا تدخل إطارات الانتقال في النتيجة أبداً.
5. **إزالة التكرار**: بصمة pHash + توقيع لوني؛ عند التطابق يُحتفظ بالنسخة ذات كثافة الحواف الأعلى.

كل العتبات قابلة للضبط في `slide_extractor/extractor.py` (`ExtractorConfig`).

## 🧪 الاختبار

```bash
python tests/test_extractor.py
```

يولّد فيديو محاضرة اصطناعياً (كتابة تدريجية + تلاشي + شريحة مكررة) ويتحقق أن الناتج ٣ شرائح فريدة وأن الشريحة المكتوبة التُقطت **كاملة**.

---

# English Summary

Convert any YouTube video (or local file) into images + a high-quality PDF by intelligently extracting unique, fully-written slides.

**The hard problem solved:** lecturers write on slides incrementally; naive scene detection emits thousands of pages. This project uses the writing/page-flip asymmetry — writing only *adds* ink while a page flip *removes* the previous content's edges — plus stable-frame selection (no mid-fade blends) and perceptual-hash de-duplication that keeps the most detailed copy of each slide.

**Run:** `pip install -r requirements.txt && python app.py` → open http://localhost:8000
**CLI:** `python cli.py "<youtube-url-or-file>" -o out -s medium`

Built entirely from open-source: yt-dlp, OpenCV, ImageHash, img2pdf, FastAPI.
