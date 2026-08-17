"""Task c1: Generate the Arabic AI Business Prompt Kit (50 prompts, HTML + PDF)."""
import html
import subprocess
import tempfile
from pathlib import Path

from ._common import write, out_path

# Category: (name_ar, name_en, [(prompt_ar, prompt_en, example_ar) x N])
CATEGORIES = [
    ("سوشيال ميديا", "Social Media", [
        ("أنت مدير سوشيال ميديا محترف للعقارات في مسقط. اكتب منشور إنستغرام جذاب عن شقة فاخرة من غرفتين في [المنطقة] بسعر [السعر]. استخدم لغة خليجية راقية، 100 كلمة، مع 5 هاشتاقات عربية وإنجليزية.",
         "You are a real estate social media manager in Muscat. Write an engaging Instagram post about a luxury 2-bedroom apartment in [area] priced at [price]. Use refined Gulf Arabic, 100 words, with 5 Arabic and English hashtags.",
         "مثال: «شقة فاخرة في الموج… إطلالة بحرية كاملة، 3 دقائق من الشاطئ. #عقارات_عمان #MuscatRealEstate»"),
        ("اكتب 10 أفكار منشورات لوكالة عقارية عمانية لمدة أسبوعين. تنوع: إنجازات، نصائح، عقارات مميزة، شهادات عملاء. كل فكرة بجملة افتتاحية جذابة.",
         "Write 10 post ideas for an Omani real estate agency covering two weeks. Variety: wins, tips, featured properties, client testimonials. Each with a catchy opening line.",
         "مثال: «3 أخطاء يقع فيها مشترو المنازل الأولى في عُمان — وهذه هي الحلول»"),
        ("أنت كاتب إعلانات. أعد كتابة هذا الإعلان العقاري ليكون أكثر إقناعًا: [الصق الإعلان]. حافظ على الحقائق، حسّن العاطفة، أضف دعوة واضحة للتواصل.",
         "You are a copywriter. Rewrite this real estate ad to be more persuasive: [paste ad]. Keep the facts, improve the emotion, add a clear call to action.",
         "مثال: قبل «شقة للبيع» → بعد «شقة العمر… مع إطلالة لا تُنسى وموقع يليق بك»"),
        ("اكتب سلسلة 5 منشورات عن منطقة [اسم الحي] في مسقط: لماذا هي خيار مثالي للعائلات، المدارس، الخدمات، الأسعار، ونصائح الشراء.",
         "Write a 5-post series about [neighborhood] in Muscat: why it's ideal for families, schools, amenities, prices, and buying tips.",
         "مثال: «لماذا تختار العائلات السيب؟ الجواب في هذه السلسلة»"),
        ("اكتب ردًا احترافيًا على تعليق سلبي على منشور وكالتك: [الصق التعليق]. النبرة: هادئة، معتذرة، تقدم حلاً وترغب بالتواصل الخاص.",
         "Write a professional response to a negative comment on your agency's post: [paste comment]. Tone: calm, apologetic, offering a solution and a private follow-up.",
         "مثال: «نعتذر عن تجربتك… يسعدنا التواصل معك مباشرة لحل الأمر»"),
        ("اكتب ردًا على رسالة مباشرة من عميل مهتم بعقار: [رسالة العميل]. اطرح سؤالين لتأهيله (الميزانية، المنطقة) واقترح موعد اتصال.",
         "Write a reply to a direct message from a client interested in a property: [client message]. Ask two qualifying questions (budget, area) and suggest a call time.",
         "مثال: «أهلاً! ممتاز اختياركم… ما الميزانية التقريبية؟ وأي منطقة تفضلون؟ نقدر نرتب مكالمة سريعة»"),
        ("اكتب 10 هاشتاقات لمنشور عقاري في مسقط (5 عربية، 5 إنجليزية) مع نصيحة عن أفضل 3 للاستخدام.",
         "Write 10 hashtags for a Muscat real estate post (5 Arabic, 5 English) with a tip on the best 3 to use.",
         "مثال: #عقارات_مسقط #شقق_للبيع #Muscat #RealEstateOman #OmanProperty"),
        ("اكتب قصة إنستغرام تفاعلية (سؤال + استطلاع) عن السوق العقاري في عُمان: [الموضوع]. سؤالان بأسلوب خليجي.",
         "Write an interactive Instagram story (question + poll) about the Omani real estate market: [topic]. Two questions in Gulf style.",
         "مثال: «هل تعتقد أن أسعار الموج سترتفع العام القادم؟ استطلاع: نعم/لا»"),
    ]),
    ("عقارات", "Real Estate", [
        ("أنت وكيل عقاري محترف. اكتب إعلانًا جذابًا لعقار بالتفاصيل التالية: [نوع العقار]، [عدد الغرف]، [المنطقة]، [السعر]. استخدم لغة خليجية راقية تناسب المشترين الجادين. الإعلان 150 كلمة ويبرز 3 مزايا رئيسية.",
         "You are a professional real estate agent. Write a compelling ad for a property with these details: [type], [rooms], [area], [price]. Use refined Gulf Arabic for serious buyers. 150 words highlighting 3 key features.",
         "مثال: «فيلا عائلية في القرم… 4 غرف + مجلس كبير + حديقة خاصة»"),
        ("أنت مساعد متابعة عقاري. اكتب رسالة واتساب قصيرة (50 كلمة) لمتابعة عميل زار عقارًا قبل يومين. النبرة: ودية ومهنية. لا تضغط. اذكر اسم العقار: [اسم العقار].",
         "You are a real estate follow-up assistant. Write a short WhatsApp message (50 words) to follow up with a client who visited a property 2 days ago. Tone: friendly, professional, not pushy. Mention: [property name].",
         "مثال: «أهلاً [الاسم]، أتمنى أن تكون الفكرة عن [العقار] ما زالت حاضرة… حاب نرتب لكم زيارة ثانية؟»"),
        ("لخّص بيانات سوق العقارات هذه لجمهور عميل غير تقني. اكتب بالعربية الخليجية الرسمية. أبرز: اتجاهات الأسعار، أفضل مناطق الشراء، و3 توصيات استثمارية. البيانات: [الصق البيانات].",
         "Summarize this real estate market data for a non-technical GCC client audience. Write in formal Gulf Arabic. Highlight: price trends, best areas to buy, and 3 investment recommendations. Data: [paste data].",
         "مثال: «الأسعار في الموج ارتفعت 8% خلال الربع…»"),
        ("أنت مستشار عقاري. قارن بين هذين العقارين لعميل يبحث عن [الغرض: سكن/استثمار]. قدم مقارنة موضوعية في جدول، ثم توصيتك النهائية مع السبب. العقار الأول: [التفاصيل]. العقار الثاني: [التفاصيل].",
         "You are a real estate consultant. Compare these two properties for a client looking for [purpose: living/investment]. Provide an objective table comparison, then your final recommendation with reasoning.",
         "مثال: جدول يقارن السعر، الموقع، العائد المتوقع، ثم توصية"),
        ("اكتب سكريبت مكالمة هاتفية بالعربية (90 ثانية) لوكيل عقاري يتصل بعميل محتمل أبدى اهتمامًا عبر الإنترنت لكنه لم يرد على واتساب. الهدف: حجز زيارة عقار. النبرة: واثقة، غير ملحّة. أضف سطرين لمعالجة الاعتراضات.",
         "Write a 90-second Arabic phone script for a real estate agent calling a potential buyer who showed interest online but didn't respond on WhatsApp. Goal: book a viewing. Tone: confident, not pushy. Include 2 objection-handling lines.",
         "مثال: «العميل: ما عندي وقت… الوكيل: أتفهم تمامًا، الزيارة 20 دقيقة فقط»"),
        ("اكتب رسالة تأكيد موعد زيارة عقار عبر واتساب: التاريخ، الوقت، العنوان، رقم التواصل، مع نصيحة صغيرة عن الحي. النبرة: مهنية ودودة.",
         "Write a WhatsApp viewing confirmation: date, time, address, contact number, plus a small tip about the neighborhood. Tone: professional and friendly.",
         "مثال: «تم تأكيد زيارتكم غدًا الساعة 5 مساءً… نصيحة: جربوا طريق السلطان قابوس، أسرع»"),
        ("اكتب رسالة اعتذار ومتابعة لعملاء انتظروا ردًا طويلًا من وكالتك: [السبب]. اعتذار صادق + قيمة تعويضية (جولة افتراضية، تقرير سوق) + خطوة تالية.",
         "Write an apology + follow-up message to clients who waited long for your agency's reply: [reason]. Sincere apology + compensatory value (virtual tour, market report) + next step.",
         "مثال: «نعتذر عن التأخير… عوضًا عن ذلك أرسلنا لكم تقرير السوق الأسبوعي مجانًا»"),
        ("اكتب سكريبت رسالة صوتية (60 ثانية) لوكيل عقاري يقدم عقارًا جديدًا لعميل تواصل معه سابقًا: [العقار]. حماس محسوب + دعوة للزيارة.",
         "Write a 60-second voice note script for an agent introducing a new property to a past client: [property]. Measured enthusiasm + viewing invite.",
         "مثال: «أهلاً [الاسم]، وصلنا عقار جديد أعتقد يناسبكم…»"),
    ]),
    ("ضيافة وفنادق", "Hospitality", [
        ("أنت مدير فندق 5 نجوم في مسقط. اكتب رسالة ترحيب بالضيوف عند الوصول بالعربية والإنجليزية (100 كلمة): ترحيب، مزايا الفندق، عروض خاصة.",
         "You are a 5-star hotel manager in Muscat. Write a guest welcome message on arrival in Arabic and English (100 words): welcome, hotel perks, special offers.",
         "مثال: «أهلاً بكم في [الفندق]… استمتعوا بعشاء مجاني في مطعمنا الليلة»"),
        ("اكتب ردًا على تقييم فندقي إيجابي (شكر + دعوة للعودة) وتقييم سلبي (اعتذار + حل + دعوة للتواصل الخاص). بالعربية الفصحى المهذبة.",
         "Write responses to a positive hotel review (thanks + return invite) and a negative one (apology + solution + private follow-up invite). In polite formal Arabic.",
         "مثال: «نشكركم على تقييمكم الرائع… نتشرف بعودتكم»"),
        ("اكتب عرض بيع إضافي للضيوف: ترقية غرفة، عشاء رومانسي، جولة سياحية. رسالة واتساب قصيرة أثناء الإقامة. بالعربية والإنجليزية.",
         "Write an upsell offer for guests: room upgrade, romantic dinner, city tour. Short WhatsApp message during stay. In Arabic and English.",
         "مثال: «بمناسبة ذكرى زواجكم… نقدم لكم ترقية مجانية إلى جناح»"),
        ("اكتب سكريبت استقبال مكالمة حجز: الرد، جمع التفاصيل (التواريخ، عدد الغرف، الإقامة)، تأكيد السعر، إنهاء ودود. بالعربية.",
         "Write a booking call script: answering, collecting details (dates, rooms, stay), confirming price, friendly close. In Arabic.",
         "مثال: «فندق [الاسم]، أهلاً… كيف أقدر أساعدكم اليوم؟»"),
        ("اكتب رسالة ما بعد الإقامة لضيف فندق: شكر، طلب تقييم، وعرض عودة مخفض. بالعربية والإنجليزية.",
         "Write a post-stay message to a hotel guest: thanks, review request, discounted return offer. Arabic and English.",
         "مثال: «نشكركم على إقامتكم… خصم 15% عند الحجز المباشر خلال 30 يومًا»"),
        ("اكتب رسالة للشركات لعقد اتفاقية إقامة شهرية لفريق عمل: [عدد الغرف]، [المدة]. اذكر مزايا العقد طويل الأجل.",
         "Write a message to companies offering a monthly-stay corporate agreement: [rooms], [duration]. Highlight long-term contract benefits.",
         "مثال: «عقد إقامة شهرية لموظفيكم… أسعار خاصة + خدمات غسيل مجانية»"),
    ]),
    ("تجارة إلكترونية", "E-commerce", [
        ("اكتب وصف منتج مقنع (150 كلمة) للمتجر الإلكتروني: [اسم المنتج]، [الميزات]، [الفوائد]، [السعر]. بالعربية + الإنجليزية، مع دعوة شراء واضحة.",
         "Write a persuasive product description (150 words) for the online store: [product], [features], [benefits], [price]. Arabic + English, with a clear buy call.",
         "مثال: «عود بخور فاخر… يدوم 3 ساعات… اطلب الآن وادفع عند الاستلام»"),
        ("اكتب رسالة استرداد سلة مهجورة (3 رسائل: بعد ساعة، يوم، 3 أيام) بلغة خليجية ودودة مع حافز إغلاق.",
         "Write an abandoned cart recovery sequence (3 messages: 1 hour, 1 day, 3 days) in friendly Gulf Arabic with a closing incentive.",
         "مثال: «سلة مشترياتك تنتظرك… خصم 10% ينتهي اليوم»"),
        ("اكتب رسالة تأكيد طلب + رسالة شحن + رسالة تسليم بالعربية، تتضمن رقم الطلب، التتبع، وشكر العميل.",
         "Write order confirmation + shipping + delivery messages in Arabic, including order number, tracking, and thanks.",
         "مثال: «تم شحن طلبكم رقم 1234… التتبع: [الرابط]»"),
        ("اكتب وصف المتجر (bio) لمنصة بيع عمانية: من نحن، ماذا نبيع، لماذا تختارنا، ضمانات. 80 كلمة.",
         "Write a store bio for an Omani selling platform: who we are, what we sell, why choose us, guarantees. 80 words.",
         "مثال: «متجر عماني 100%… منتجات أصلية، شحن سريع لجميع المحافظات»"),
        ("اكتب رسالة استرداد عميل بعد الشراء: شكر، نصائح استخدام، عرض منتج مكمّل. بالعربية.",
         "Write a post-purchase recovery message: thanks, usage tips, complementary product offer. In Arabic.",
         "مثال: «شكرًا لطلبكم! نصيحة: [نصيحة استخدام]… قد يعجبكم أيضًا [منتج مكمّل]»"),
        ("اكتب رسالة لطلب مراجعة منتج بعد 7 أيام من التسليم: طلب لطيف + رابط مباشر + حافز بسيط.",
         "Write a product review request 7 days after delivery: friendly ask + direct link + small incentive.",
         "مثال: «تقييمكم يساعدنا… ومن يقيّم اليوم يدخل سحب على قسيمة 20 ريال»"),
    ]),
    ("خدمة العملاء", "Customer Service", [
        ("أنت ممثل خدمة عملاء. اكتب ردًا على استفسار شائع: [الصق السؤال]. أجب بوضوح، تعاطف، واقترح الخطوة التالية. بالعربية.",
         "You are a customer service rep. Write a response to a common inquiry: [paste question]. Answer clearly, empathetically, suggest next step. In Arabic.",
         "مثال: «نفهم استفساركم… وإليكم التفاصيل الكاملة»"),
        ("اكتب رسالة اعتذار احترافية عن تأخير/خطأ: [وصف الموقف]. تشمل: الاعتراف، الاعتذار، الحل، تعويض رمزي، والتزام بعدم التكرار.",
         "Write a professional apology for a delay/error: [describe situation]. Includes: acknowledgment, apology, solution, small compensation, commitment.",
         "مثال: «نعتذر عن التأخير… خصم 15% على طلبكم القادم»"),
        ("اكتب سكريبت تصعيد غاضب: كيف تهدئ العميل، تستمع، تعيد الصياغة، وتقدم حلاً خلال 3 دقائق. بالعربية الخليجية.",
         "Write an angry-caller de-escalation script: calm the client, listen, paraphrase, offer a solution within 3 minutes. In Gulf Arabic.",
         "مثال: «أتفهم انزعاجك تمامًا… دعني أتحقق فورًا وأعود لك خلال 10 دقائق»"),
        ("اكتب رسالة تذكير موعد: [نوع الموعد]، [التاريخ]، [الوقت]، [المكان]، مع خيار إعادة الجدولة بضغطة واحدة.",
         "Write an appointment reminder: [type], [date], [time], [location], with a one-tap reschedule option.",
         "مثال: «تذكير بموعدكم غدًا 10 صباحًا… لإعادة الجدولة اضغط هنا»"),
        ("اكتب ردًا على شكوى عبر واتساب حول جودة منتج/خدمة: [الشكوى]. خطوات: اعتذار، طلب تفاصيل، حل مقترح، تعويض.",
         "Write a WhatsApp response to a quality complaint: [complaint]. Steps: apology, request details, proposed solution, compensation.",
         "مثال: «نأسف جدًا… أرسل لنا صورة المنتج وسنبدله فورًا»"),
        ("اكتب سكريبت معالجة عميل يريد إلغاء اشتراك/خدمة: فهم السبب، عرض بديل، تسهيل الإلغاء باحترام.",
         "Write a script for a client wanting to cancel a subscription/service: understand the reason, offer an alternative, facilitate cancellation respectfully.",
         "مثال: «نفهم قراركم… هل جربتم الباقة الشهرية الأصغر قبل الإلغاء؟»"),
    ]),
    ("عروض ومقترحات", "Proposals", [
        ("اكتب بريدًا تقديميًا لوكالة عقارية عمانية تقدم خدمة مساعد ذكاء اصطناعي. الفوائد: رد 24/7، حجز مواعيد، متابعة تلقائية. 120 كلمة، نبرة واثقة غير ملحّة.",
         "Write a pitch email to an Omani real estate agency offering an AI assistant service. Benefits: 24/7 replies, appointment booking, auto follow-up. 120 words, confident not pushy.",
         "مثال: «تخيلوا أن كل عميل يرد عليه خلال ثوانٍ… حتى بعد دوامكم»"),
        ("اكتب هيكل مقترح خدمة احترافي: الملخص، المشكلة، الحل، المنهجية، التسعير، الجدول الزمني، الضمانات، الشروط.",
         "Write a professional service proposal structure: summary, problem, solution, methodology, pricing, timeline, guarantees, terms.",
         "مثال: «الضمان: إذا ما رضيتم بالشهر الأول… استرداد كامل»"),
        ("اكتب رسالة متابعة بعد اجتماع: شكر، ملخص النقاط، الخطوة التالية، وتاريخ محدد للقرار. بالعربية.",
         "Write a post-meeting follow-up: thanks, summary of points, next step, and a specific decision date. In Arabic.",
         "مثال: «شكرًا لوقتكم… بانتظار قراركم قبل الخميس»"),
        ("اكتب رسالة عرض سعر (quotation) واضحة: الخدمة، النطاق، السعر، مدة التنفيذ، شروط الدفع، مدة صلاحية العرض.",
         "Write a clear quotation message: service, scope, price, timeline, payment terms, quote validity.",
         "مثال: «عرض سعر ساري حتى 30 الجاري… الدفع 50% مقدماً»"),
        ("اكتب رسالة متابعة لعرض سعر لم يُرد عليه العميل بعد 5 أيام: تذكير لطيف + قيمة إضافية + سؤال مفتوح.",
         "Write a follow-up for a quote unanswered after 5 days: gentle reminder + added value + open question.",
         "مثال: «أرسلت لكم العرض الأسبوع الماضي… أضفنا شهر دعم مجاني إذا أُغلقت الصفقة هذا الأسبوع»"),
    ]),
    ("تحليل السوق", "Market Analysis", [
        ("اكتب تحليلًا منافسًا: [اسم المنافس] — نقاط القوة، الضعف، الفرص، التهديدات (SWOT) وتوصيات للتفوق عليه.",
         "Write a competitor analysis: [competitor] — strengths, weaknesses, opportunities, threats (SWOT) and recommendations to beat them.",
         "مثال: «نقطة ضعف المنافس: لا يرد بعد الدوام… وهنا فرصتنا»"),
        ("اكتب تقرير طلب سوقي قصير: [الخدمة/المنتج] في [السوق]. حجم الطلب، الجمهور المستهدف، الاستعداد للدفع، قنوات الوصول.",
         "Write a short market demand report: [service/product] in [market]. Demand size, target audience, willingness to pay, reach channels.",
         "مثال: «وكالات العقارات في مسقط: 300+ وكالة نشطة… 80% تستخدم واتساب»"),
        ("اكتب توصية استثمارية: [القطاع/المنطقة]. المخاطر، العوائد المتوقعة، أفق الاستثمار، ومعايير النجاح.",
         "Write an investment recommendation: [sector/area]. Risks, expected returns, investment horizon, success criteria.",
         "مثال: «عقارات الموج: عائد متوقع 6-8% سنويًا…»"),
        ("اكتب تحليلًا سريعًا لمنافس مباشر: [المنافس]. منتجه، تسعيره، جمهوره، وثغرة يمكن استغلالها.",
         "Write a quick analysis of a direct competitor: [competitor]. Their product, pricing, audience, and an exploitable gap.",
         "مثال: «الثغرة: لا يقدمون دعمًا عربيًا بعد الدوام…»"),
        ("اكتب تقرير أداء شهري بسيط لنشاط تجاري: [الأرقام]. اتجاهات، نقاط قوة، توصيتان للشهر القادم.",
         "Write a simple monthly performance report for a business: [numbers]. Trends, strengths, two recommendations for next month.",
         "مثال: «ارتفعت الاستفسارات 20%… التوصية: أتمتة الردود»"),
    ]),
    ("مبيعات ومفاوضات", "Sales & Negotiation", [
        ("اكتب سطر افتتاح مبيعات لواتساب (40 كلمة) لعميل محتمل: [نوع العميل]. سؤال مفتوح + قيمة فورية. بالعربية.",
         "Write a sales opening line for WhatsApp (40 words) to a prospect: [client type]. Open question + immediate value. In Arabic.",
         "مثال: «أهلاً! لاحظنا أنكم تستقبلون استفسارات كثيرة… كم نسبة الرد خلال ساعة؟»"),
        ("اكتب 5 ردود لمعالجة الاعتراضات: «غالي»، «نفكر»، «ما عندنا وقت»، «جرّبنا غيركم»، «نحتاج موافقة الإدارة». كل رد 30 كلمة.",
         "Write 5 objection-handling replies: 'too expensive', 'we'll think about it', 'no time', 'we tried others', 'need management approval'. Each 30 words.",
         "مثال: «أتفهم… لكن الفاتورة الشهرية أقل من راتب موظف استقبال ليوم واحد»"),
        ("اكتب سكريبت إغلاق صفقة: تلخيص القيمة، طلب القرار، خياران للدفع، والتعامل مع الصمت. بالعربية.",
         "Write a closing script: summarize value, ask for the decision, offer two payment options, handle silence. In Arabic.",
         "مثال: «أبي أبدأ معكم هذا الأسبوع… إيداع 25 ريال يحجز لكم الأولوية»"),
        ("اكتب رسالة طلب ترشيح بعد إتمام خدمة ناجحة: شكر + طلب تقييم + طلب ترشيح عميل واحد. بالعربية.",
         "Write a referral request after a successful delivery: thanks + review request + ask for one referral. In Arabic.",
         "مثال: «إذا أعجبتكم الخدمة… من تعرفون قد يستفيد؟»"),
        ("اكتب رسالة إعادة إحياء عميل قديم (لم يتعامل معك منذ 6 أشهر): ذكرى إيجابية + عرض جديد + لا ضغط.",
         "Write a re-engagement message to an old client (inactive 6 months): positive memory + new offer + no pressure.",
         "مثال: «أهلاً [الاسم]! آخر مرة ساعدناكم في [شيء]… عندنا الآن [عرض جديد]»"),
        ("اكتب سكريبت بيع عبر المكالمة لخدمة شهرية: افتتاح، قيمة، اعتراضات، إغلاق ناعم مع مهلة قرار.",
         "Write a phone sales script for a monthly service: opening, value, objections, soft close with decision deadline.",
         "مثال: «إذا قررتم هذا الأسبوع، نبدأ التنفيذ الاثنين المقبل»"),
    ]),
]

TOTAL = sum(len(items) for _, _, items in CATEGORIES)


def build_html():
    cards = []
    for cat_ar, cat_en, items in CATEGORIES:
        rows = ""
        for i, (p_ar, p_en, ex) in enumerate(items, 1):
            rows += f"""
            <div class="prompt">
              <div class="p-num">{i}</div>
              <div class="p-body">
                <p class="p-ar" dir="rtl">{html.escape(p_ar)}</p>
                <p class="p-en">{html.escape(p_en)}</p>
                <p class="p-ex" dir="rtl">💡 {html.escape(ex)}</p>
              </div>
            </div>"""
        cards.append(f"""
        <div class="cat">
          <div class="cat-hdr">
            <span class="cat-ar" dir="rtl">{cat_ar}</span>
            <span class="cat-en">{cat_en}</span>
          </div>
          {rows}
        </div>""")

    return f"""<!DOCTYPE html>
<html lang="ar">
<head>
<meta charset="UTF-8">
<title>Arabic AI Business Prompt Kit</title>
<style>
  @page {{ size: A4; margin: 14mm 12mm; }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Noto Naskh Arabic','Noto Sans Arabic','DejaVu Sans',sans-serif; color: #1a2333; font-size: 10.5pt; line-height: 1.6; }}
  .cover {{ text-align: center; padding: 40px 10px 30px; border-bottom: 3px solid #0f766e; margin-bottom: 20px; }}
  .cover h1 {{ font-size: 22pt; color: #0f766e; margin-bottom: 6px; }}
  .cover h2 {{ font-size: 13pt; color: #475569; font-weight: 400; }}
  .cover .badge {{ display:inline-block; margin-top:12px; background:#0f766e; color:#fff; padding:6px 18px; border-radius:20px; font-size:11pt; }}
  .cat {{ margin-bottom: 18px; page-break-inside: avoid; }}
  .cat-hdr {{ display:flex; justify-content:space-between; align-items:center; background:#0f766e; color:#fff; padding:8px 14px; border-radius:8px 8px 0 0; }}
  .cat-ar {{ font-size: 12.5pt; font-weight: 700; }}
  .cat-en {{ font-size: 9.5pt; opacity:.9; }}
  .prompt {{ display:flex; gap:10px; padding:10px 12px; border:1px solid #e2e8f0; border-top:none; }}
  .prompt:nth-child(odd) {{ background:#f8fafc; }}
  .p-num {{ flex-shrink:0; width:22px; height:22px; background:#0f766e; color:#fff; border-radius:50%; text-align:center; font-size:10pt; line-height:22px; }}
  .p-ar {{ font-weight: 600; color:#0f172a; }}
  .p-en {{ font-size: 9pt; color:#475569; margin-top:3px; }}
  .p-ex {{ font-size: 9pt; color:#0f766e; margin-top:5px; background:#f0fdfa; padding:5px 8px; border-radius:5px; }}
  .footer {{ text-align:center; color:#94a3b8; font-size:9pt; margin-top:20px; padding-top:10px; border-top:1px solid #e2e8f0; }}
</style>
</head>
<body>
  <div class="cover">
    <h1>حزمة بروميتات الأعمال بالذكاء الاصطناعي</h1>
    <h2>Arabic AI Business Prompt Kit — {TOTAL} Ready-to-Use Prompts for GCC Businesses</h2>
    <div class="badge">🇴🇲 Arabic + English • Khaleeji Dialect • Example Outputs</div>
  </div>
  {''.join(cards)}
  <div class="footer">OmanAI • Murshed • {TOTAL} prompts across {len(CATEGORIES)} categories — use in ChatGPT, Claude, or any AI tool</div>
</body>
</html>"""


def run(ctx):
    html_str = build_html()
    html_path = write(ctx, "gumroad/arabic-ai-prompt-kit.html", html_str)
    pdf_path = out_path(ctx, "gumroad/arabic-ai-prompt-kit.pdf")

    # Convert HTML → PDF via headless Chromium
    chromium = None
    for c in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable"):
        import shutil
        if shutil.which(c):
            chromium = c
            break
    if chromium:
        cmd = [chromium, "--headless", "--disable-gpu", "--no-sandbox",
               f"--print-to-pdf={pdf_path}", str(html_path)]
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=120)
            pdf_ok = pdf_path.exists() and pdf_path.stat().st_size > 1000
        except Exception:
            pdf_ok = False
    else:
        pdf_ok = False

    # Product copy
    write(ctx, "gumroad/product-copy.md", f"""# Arabic AI Business Prompt Kit — Gumroad Listing

**Name:** Arabic AI Business Prompt Kit — 50 Ready-to-Use Prompts for GCC Businesses

**Description:**

{50} professionally written AI prompts for Arabic-speaking businesses in the GCC — ready to use in ChatGPT, Claude, or any AI tool.

Includes prompts for:
- 📱 Social Media (Instagram, TikTok, LinkedIn — Arabic + English)
- 🏠 Real Estate listing descriptions that convert
- 🏨 Hotel and hospitality guest communications
- 🛍️ E-commerce product descriptions
- 📞 Customer service scripts in Khaleeji Arabic
- 💼 Business proposal writing
- 📊 Market analysis requests
- 🎯 Sales and negotiation scripts

Each prompt includes:
- Arabic version (Khaleeji dialect)
- English version
- Example output
- Customization guide

Perfect for: business owners, marketing teams, sales reps, and anyone who wants professional Arabic AI outputs without spending hours on prompt engineering.

Instant download. No subscription. Use forever.
**Price:** $19
**File:** arabic-ai-prompt-kit.pdf""")

    return {
        "summary": f"Prompt kit generated: {TOTAL} prompts, {len(CATEGORIES)} categories" + (" + PDF ✓" if pdf_ok else " (PDF failed — use the HTML)"),
        "out": "assets/gumroad/",
    }
