# النشر المجاني الدائم — Free Hosting Guide

الخلاصة: **Streamlit Community Cloud غير مناسبة لمعالجة الفيديو** (تخنق التطبيق
عند تجاوز حصة المعالجة). البدائل التالية مجانية بلا انتهاء وأقوى بكثير.

## 1️⃣ Hugging Face Spaces — الأفضل والأسهل (موصى به)

مجاني دائماً، بموارد أسخى من Streamlit (2 vCPU · 16GB RAM · 50GB قرص)،
ويدعم Streamlit مباشرة بدون Docker.

1. أنشئ حساباً على <https://huggingface.co> ثم **New Space**
2. الإعدادات: SDK = **Streamlit** · Hardware = **CPU basic (free)**
3. اربطه بمستودع GitHub، أو ارفع الملفات مباشرة
4. أضف ملف `packages.txt` (موجود بالفعل في المستودع) لتثبيت ffmpeg/node
5. الأسرار (cookies/بروكسي): **Settings ← Variables and secrets**

ملاحظة: Spaces تُوقف التطبيق بعد ٤٨ ساعة خمول وتعيده تلقائياً عند أول زيارة.

## 2️⃣ Oracle Cloud Always Free — الأقوى (إعداد أطول)

خادم مجاني **مدى الحياة**: 4 أنوية ARM + 24GB ذاكرة + 200GB قرص — أقوى من
أي خطة مجانية أخرى، وبلا خنق إطلاقاً، ويمكنك تشغيل خادم Cobalt الخاص بك
عليه في نفس الوقت.

```bash
sudo apt update && sudo apt install -y python3-pip ffmpeg
git clone <repo> && cd Video-to-photos-
pip install -r requirements.txt
# تشغيل دائم في الخلفية
nohup streamlit run streamlit_app.py --server.port 8501 \
      --server.address 0.0.0.0 --server.headless true &
```
ثم افتح المنفذ 8501 من إعدادات الشبكة (Security List) في لوحة Oracle.

## 3️⃣ محلياً على جهازك — مجاني وأسرع من الجميع

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```
بلا حدود موارد، وروابط يوتيوب تعمل مباشرة لأن عنوانك سكني نظيف.

---

## لماذا حدث الخنق أصلاً؟

معالجة الفيديو ثقيلة على المعالج. الإصدار 2.6.0 يخفض الاستهلاك بشكل ملموس:

| التحسين | الأثر |
|---|---|
| عيّنات تكيّفية للفيديوهات الطويلة | ثلث العمل التحليلي لفيديو > ساعتين |
| تشغيل خادم رموز PO ومحرك JS عند الحاجة فقط | صفر استهلاك عند رفع الملفات |
| تحليل مباشر بدل تحويل كامل (مقيس) | أسرع ٢٠٪ من مسار الوسيط |

كل هذه المكتبات مفتوحة المصدر ومجانية دائماً: yt-dlp · OpenCV · ImageHash ·
img2pdf · ffmpeg · Streamlit.
