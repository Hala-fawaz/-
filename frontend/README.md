# رِسالة | رحلة الإسلام عبر الزمان والمكان

واجهة عربية RTL متجاوبة، مبنية بـ HTML وCSS وJavaScript، من دون إطار عمل أو عملية بناء. استلهمت صفحات الخريطة والمحطة والمصادر والإعدادات من البروتوتايب المرفق، مع الإبقاء على لوحة الألوان والهوية البصرية للنسخة الأولى.

## التشغيل

افتح `index.html` مباشرة، أو شغّل خادم ملفات محليًا:

```bash
python3 -m http.server 8000
```

ثم افتح `http://localhost:8000`.

## الصفحات

- `index.html` الصفحة الرئيسية ومحطات الاستكشاف والبحث والخريطة التمهيدية.
- `explore.html` خريطة تضاريس تفاعلية تجريبية، والأحداث التاريخية مع النص والصوت.
- `trust.html` المصادر وضوابط الإجابة.
- `station.html` صفحة المحطة؛ تتغير تفاصيلها بحسب الحدث في الرابط، وتتضمن النبذة والأحداث والأماكن والمصادر والمرشد التجريبي.
- `about.html` نبذة عنا: فكرة رسالة وأهدافها، محتوى الموقع، خطوات التجربة والتقنيات المقترحة.
- `login.html` واجهة تجريبية بخياري تسجيل الدخول وإنشاء حساب، عبر البريد أو رقم الجوال.
- `account.html` صفحة الحساب.
- `settings.html` إعدادات اللغة والمظهر والصوت.

## اللغات

قائمة اللغات تتضمن أكثر من 100 لغة. العربية هي اللغة الأصلية، ويوجد عرض أساسي باللغة الإنجليزية دون إعداد إضافي. لتفعيل الترجمة لبقية اللغات، املئي `googleTranslationApiKey` في `config.js` بمفتاح Google Cloud Translation - Basic API، وقيّديه بنطاق الموقع وبواجهة Cloud Translation. لا تضعي مفتاحًا غير مقيّد في مستودع عام. الترجمة ترسل النصوص الظاهرة للخدمة.

مفتاح Google Cloud Translation يحتاج مشروعًا مفعّلًا وقد تترتب عليه تكلفة وفق إعدادات حساب Google Cloud. تبقى العربية والإنجليزية متاحتين دون المفتاح، أما اللغات الإضافية فتتطلب إعداد المفتاح والاتصال بالإنترنت.

## الدخول والحساب

تسجيل الدخول وإنشاء الحساب وحسابي نماذج واجهة أمامية فقط. يتحقق النموذج من صيغة البريد أو الجوال، ثم يحفظ الاسم والمعرّف محليًا في المتصفح؛ لا يرسل البيانات ولا يخزن كلمة المرور. زر نفاذ ظاهر لكنه غير مفعّل. لا تستخدمي بيانات حقيقية في النسخة التجريبية.

## الخريطة والصوت

الخريطة تمثيل تضاريس SVG تفاعلي بمنظور ثلاثي الأبعاد، مع وضع مسطح، تكبير وتصغير، مرشحات، وعلامات أحداث قابلة للاختيار. هي ليست خريطة GIS دقيقة أو Cesium/Three.js متصلة ببيانات تضاريس.

زر الاستماع يستخدم `SpeechSynthesis` والأصوات المتاحة في جهاز الزائر. يحتاج دعم المتصفح للصوت؛ جودة النطق واختيار الصوت يعتمدان على الأصوات المثبتة على الجهاز.

محتوى المحطات في `data.js`: لكل حدث ملخص قصير `summary` يظهر على الخريطة، ونبذة تاريخية مفصلة `history` ومقتطف من المصدر `details` يظهران في صفحة المحطة عبر `enhancements.js`.

## الصور

صورة محطة «نزول الوحي» (`assets/stations/quran-open.jpg`): مصحف من العصر المملوكي نحو سنة 1380م، متحف الفنون التركية والإسلامية بإسطنبول. تصوير Mustafa-trit20، ويكيميديا كومنز، رخصة CC BY-SA 4.0: https://commons.wikimedia.org/wiki/File:Mamluk_era_Quran,_circa_1380,_open_to_sura_16.jpg

صور المحطات الأخرى من ويكيميديا كومنز، محفوظة محليًّا في `assets/stations/`:

| الملف | الصورة الأصلية | المصوّر | الرخصة |
|---|---|---|---|
| `abwa.jpg` | [الضريح الأيمن لضريح السيدة آمنة عليها السلام.JPG](https://commons.wikimedia.org/wiki/File:%D8%A7%D9%84%D8%B6%D8%B1%D9%8A%D8%AD_%D8%A7%D9%84%D8%A3%D9%8A%D9%85%D9%86_%D9%84%D8%B6%D8%B1%D9%8A%D8%AD_%D8%A7%D9%84%D8%B3%D9%8A%D8%AF%D8%A9_%D8%A2%D9%85%D9%86%D8%A9_%D8%B9%D9%84%D9%8A%D9%87%D8%A7_%D8%A7%D9%84%D8%B3%D9%84%D8%A7%D9%85.JPG) | — | Public domain |
| `aksum.jpg` | [Stelae, Aksum, Ethiopia (7158408756).jpg](https://commons.wikimedia.org/wiki/File:Stelae,_Aksum,_Ethiopia_(7158408756).jpg) | Rod Waddington from Kergunyah, Australia | CC BY-SA 2.0 |
| `aqsa.jpg` | [Jerusalem-2013-Temple Mount-Al-Aqsa Mosque (NE exposure).jpg](https://commons.wikimedia.org/wiki/File:Jerusalem-2013-Temple_Mount-Al-Aqsa_Mosque_(NE_exposure).jpg) | Godot13 | CC BY-SA 4.0 |
| `arafat.jpg` | [Jabal-e-Rehmat (Mount of Mercy) Mount Arafat.jpg](https://commons.wikimedia.org/wiki/File:Jabal-e-Rehmat_(Mount_of_Mercy)_Mount_Arafat.jpg) | Fahad Faisal | CC BY-SA 4.0 |
| `badr.jpg` | [General view of the battlefield and burial ground of Badr, Saudi Arabia, site of the historic battle between the Prophet Muhammad and the Quraysh in 624 (6).jpg](https://commons.wikimedia.org/wiki/File:General_view_of_the_battlefield_and_burial_ground_of_Badr,_Saudi_Arabia,_site_of_the_historic_battle_between_the_Prophet_Muhammad_and_the_Quraysh_in_624_(6).jpg) | Prof. Mortel | CC BY 2.0 |
| `bosra.jpg` | [Bosra, Daraa, Syria, Ancient City, Columns.jpg](https://commons.wikimedia.org/wiki/File:Bosra,_Daraa,_Syria,_Ancient_City,_Columns.jpg) | Vyacheslav Argenberg | CC BY 4.0 |
| `damascus.jpg` | [The Umayyad Mosque, Courtyard, Damascus, Syria.jpg](https://commons.wikimedia.org/wiki/File:The_Umayyad_Mosque,_Courtyard,_Damascus,_Syria.jpg) | Vyacheslav Argenberg | CC BY 4.0 |
| `green-dome.jpg` | [Green Dome, Masjid Al Nabawi.jpg](https://commons.wikimedia.org/wiki/File:Green_Dome,_Masjid_Al_Nabawi.jpg) | Wadie Al-Houh | CC0 |
| `hira.jpg` | [Entrance of Hira cave.jpg](https://commons.wikimedia.org/wiki/File:Entrance_of_Hira_cave.jpg) | Mardetanha | CC BY-SA 3.0 |
| `kaaba.jpg` | [The Kaaba during Hajj - edited.jpg](https://commons.wikimedia.org/wiki/File:The_Kaaba_during_Hajj_-_edited.jpg) | Adli Wahid Minor modifications made by Basile Morin, from the original version. | CC BY-SA 4.0 |
| `kaaba-1880.jpg` | [Edited Khalili Collection Hajj and Arts of Pilgrimage arc.pp 0211.04 The Kaaba photo by M Sadiq Bey ca. 1880-ccbysa3.0.jpg](https://commons.wikimedia.org/wiki/File:Edited_Khalili_Collection_Hajj_and_Arts_of_Pilgrimage_arc.pp_0211.04_The_Kaaba_photo_by_M_Sadiq_Bey_ca._1880-ccbysa3.0.jpg) | Original Photograph: Muhammad Sadiq Bey; original uploaded media file: Khalili C | CC BY-SA 3.0 |
| `khandaq.jpg` | [Mosque of Ali ibn Abi Talib at the Seven Mosques, Madinah, Saudi Arabia (2).jpg](https://commons.wikimedia.org/wiki/File:Mosque_of_Ali_ibn_Abi_Talib_at_the_Seven_Mosques,_Madinah,_Saudi_Arabia_(2).jpg) | Richard Mortel | CC BY 2.0 |
| `khaybar.jpg` | [Khaybar - fortress Qamus (2).jpg](https://commons.wikimedia.org/wiki/File:Khaybar_-_fortress_Qamus_(2).jpg) | Hardscarf | CC BY-SA 4.0 |
| `makkah-engraving.jpg` | [The Open court (1887) (14780927801).jpg](https://commons.wikimedia.org/wiki/File:The_Open_court_(1887)_(14780927801).jpg) | Internet Archive Book Images | No restrictions |
| `mina.jpg` | [Mina Overview.JPG](https://commons.wikimedia.org/wiki/File:Mina_Overview.JPG) | Mubeen Rahman | CC BY 3.0 |
| `mualla.jpg` | [Jannat-ul-Maualla at present.JPG](https://commons.wikimedia.org/wiki/File:Jannat-ul-Maualla_at_present.JPG) | Md iet (talk) | CC BY-SA 3.0 |
| `mushaf.jpg` | [First pages of the Quran written by Şeyh Hamdullah in 1503-1504, Topkapi A. 5.jpg](https://commons.wikimedia.org/wiki/File:First_pages_of_the_Quran_written_by_%C5%9Eeyh_Hamdullah_in_1503-1504,_Topkapi_A._5.jpg) | Sheikh Hamdullah | Public domain |
| `mutah.jpg` | [Battle of Mu'tah.jpg](https://commons.wikimedia.org/wiki/File:Battle_of_Mu%27tah.jpg) | Bashar Tabbah | CC BY-SA 4.0 |
| `nabawi.jpg` | [Green Dome of Madinah.jpg](https://commons.wikimedia.org/wiki/File:Green_Dome_of_Madinah.jpg) | King Eliot | CC BY-SA 4.0 |
| `nakhla.jpg` | [Taif Mountains (8355942584).jpg](https://commons.wikimedia.org/wiki/File:Taif_Mountains_(8355942584).jpg) | Nick Shields | CC BY 2.0 |
| `negash.jpg` | [Negash, la moschea sul sito della più antica moschea d'etiopia, del vii secolo 03.jpg](https://commons.wikimedia.org/wiki/File:Negash,_la_moschea_sul_sito_della_pi%C3%B9_antica_moschea_d%27etiopia,_del_vii_secolo_03.jpg) | Sailko | CC BY 3.0 |
| `nour.jpg` | [Jabbal An-Nour - Makkah (2241558560).jpg](https://commons.wikimedia.org/wiki/File:Jabbal_An-Nour_-_Makkah_(2241558560).jpg) | Wal N. | CC BY 2.0 |
| `old-makkah.jpg` | [Panénjoan Mekah ku Haji Gofur (Christiaan Snouck Hurgronje).jpg](https://commons.wikimedia.org/wiki/File:Pan%C3%A9njoan_Mekah_ku_Haji_Gofur_(Christiaan_Snouck_Hurgronje).jpg) | Christiaan Snouck Hurgronje | Public domain |
| `qiblatayn.jpg` | [Masjid al-Qiblatain.jpg](https://commons.wikimedia.org/wiki/File:Masjid_al-Qiblatain.jpg) | Aiman titi | CC BY-SA 3.0 |
| `quba.jpg` | [Quba Mosque Full Picture (2024).jpg](https://commons.wikimedia.org/wiki/File:Quba_Mosque_Full_Picture_(2024).jpg) | Kaliper1 | CC BY-SA 4.0 |
| `saad.jpg` | [Taif Mountains 2 (8355944458).jpg](https://commons.wikimedia.org/wiki/File:Taif_Mountains_2_(8355944458).jpg) | Nick Shields | CC BY 2.0 |
| `safa-hill.jpg` | [Safa-Marwa in my Mind 4 (6599924413).jpg](https://commons.wikimedia.org/wiki/File:Safa-Marwa_in_my_Mind_4_(6599924413).jpg) | KELANTAN JOTTINGS | CC BY 2.0 |
| `tabuk.jpg` | [Tabuk Fortress 2022.jpg](https://commons.wikimedia.org/wiki/File:Tabuk_Fortress_2022.jpg) | amanderson2 | CC BY 2.0 |
| `taif.jpg` | [Taif Mountains 3.jpg](https://commons.wikimedia.org/wiki/File:Taif_Mountains_3.jpg) | Nick Shields | CC BY 2.0 |
| `uhud.jpg` | [Jabal-e-Uhud.jpg](https://commons.wikimedia.org/wiki/File:Jabal-e-Uhud.jpg) | Bintladen | CC BY-SA 4.0 |

## النشر على GitHub Pages

ارفعي محتويات مجلد `risaala-site` إلى مستودع GitHub، ثم من **Settings → Pages** اختاري فرع النشر ومجلد الجذر. يبدأ الموقع من `index.html`.
