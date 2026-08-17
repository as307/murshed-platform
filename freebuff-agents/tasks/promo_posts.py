"""Task c4: Generate promo posts (LinkedIn + WhatsApp groups)."""
from ._common import write

LINKEDIN = """# LinkedIn Post — English
I just released something for GCC businesses: 50 ready-to-use AI prompts in Arabic and English — built specifically for the Gulf market.

Whether you're in real estate, hospitality, or retail — these prompts give you professional Arabic AI outputs immediately, no prompt engineering experience needed.

Includes Khaleeji dialect prompts for WhatsApp, property listings, customer service, and more.

Grabbing it now for $19 → [your Gumroad link]

Arabic version post coming next 👇
"""

LINKEDIN_AR = """# LinkedIn Post — Arabic
أطلقت للتو شيئًا مفيدًا للأعمال الخليجية: 50 بروميت ذكاء اصطناعي جاهزًا بالعربية والإنجليزية — مصمم خصيصًا لسوق الخليج.

سواء كنت في العقارات أو الضيافة أو التجارة الإلكترونية — هذه البروميتات تعطيك نتائج احترافية فورًا، بدون خبرة في هندسة البروميتات.

تشمل اللهجة الخليجية لواتساب، إعلانات العقارات، خدمة العملاء، وأكثر.

احصل عليه الآن بـ 19 دولار → [رابط Gumroad]
"""

WHATSAPP = """# WhatsApp Group Post — Arabic
📦 مجموعة جديدة: 50 بروميت ذكاء اصطناعي جاهزة للأعمال الخليجية

إذا تستخدم ChatGPT أو Claude في عملك، هذه المجموعة توفر عليك وقت البحث عن الكلمات الصح.

الباقة تشمل:
🏠 عقارات
🏨 ضيافة وفنادق
📱 سوشيال ميديا
💼 مبيعات ومفاوضات

كل بروميت: عربي خليجي + إنجليزي + مثال على النتيجة.

السعر: 19 دولار — رابط التحميل: [your Gumroad link]
"""

DISCORD = """# Post for Oman/GCC Tech Groups
Building an Arabic AI WhatsApp assistant for real estate agencies in Oman (Murshed 🇴🇲). Handles inquiries, books viewings, follows up — 24/7 in Khaleeji Arabic.

Also selling a prompt kit ($19) with 50 bilingual Arabic/English business prompts: [link]

Happy to answer questions — or connect anyone interested in the AI assistant.
"""


def run(ctx):
    p1 = write(ctx, "posts/linkedin.md", LINKEDIN + "\n\n---\n\n" + LINKEDIN_AR)
    p2 = write(ctx, "posts/whatsapp-groups.md", WHATSAPP)
    p3 = write(ctx, "posts/tech-groups.md", DISCORD)
    return {"summary": "Posts generated: LinkedIn (EN+AR), WhatsApp groups, tech groups", "out": "assets/posts/"}
