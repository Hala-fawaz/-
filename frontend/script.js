document.addEventListener('DOMContentLoaded', () => {
    const themeBtn = document.getElementById('theme-toggle');
    const currentTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', currentTheme);
    if (themeBtn) {
        themeBtn.innerHTML = currentTheme === 'dark' ? '☀️' : '🌙';
        themeBtn.addEventListener('click', () => {
            let newTheme = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            themeBtn.innerHTML = newTheme === 'dark' ? '☀️' : '🌙';
        });
    }
});

(() => {
  const $ = (s, root = document) => root.querySelector(s);
  const $$ = (s, root = document) => [...root.querySelectorAll(s)];
  let languages = [
    ['ar','العربية'],['en','English'],['fr','Français'],['es','Español'],['de','Deutsch'],['it','Italiano'],['pt','Português'],['ru','Русский'],['tr','Türkçe'],['ur','اردو'],['fa','فارسی'],['hi','हिन्दी'],['bn','বাংলা'],['id','Bahasa Indonesia'],['ms','Bahasa Melayu'],['zh-CN','中文（简体）'],['zh-TW','中文（繁體）'],['ja','日本語'],['ko','한국어'],['sw','Kiswahili'],['ha','Hausa'],['yo','Yorùbá'],['ig','Igbo'],['am','አማርኛ'],['af','Afrikaans'],['sq','Shqip'],['az','Azərbaycanca'],['eu','Euskara'],['be','Беларуская'],['bg','Български'],['bs','Bosanski'],['ca','Català'],['ceb','Cebuano'],['co','Corsu'],['hr','Hrvatski'],['cs','Čeština'],['da','Dansk'],['nl','Nederlands'],['eo','Esperanto'],['et','Eesti'],['fi','Suomi'],['fy','Frysk'],['gl','Galego'],['ka','ქართული'],['el','Ελληνικά'],['gu','ગુજરાતી'],['ht','Kreyòl Ayisyen'],['haw','ʻŌlelo Hawaiʻi'],['he','עברית'],['hu','Magyar'],['is','Íslenska'],['ga','Gaeilge'],['jv','Basa Jawa'],['kn','ಕನ್ನಡ'],['kk','Қазақша'],['km','ខ្មែរ'],['rw','Ikinyarwanda'],['ku','Kurdî'],['ky','Кыргызча'],['lo','ລາວ'],['la','Latina'],['lv','Latviešu'],['lt','Lietuvių'],['lb','Lëtzebuergesch'],['mk','Македонски'],['mg','Malagasy'],['ml','മലയാളം'],['mt','Malti'],['mi','Māori'],['mr','मराठी'],['mn','Монгол'],['my','မြန်မာ'],['ne','नेपाली'],['no','Norsk'],['ny','Chichewa'],['or','ଓଡ଼ିଆ'],['ps','پښتو'],['pl','Polski'],['pa','ਪੰਜਾਬੀ'],['ro','Română'],['sm','Gagana Samoa'],['gd','Gàidhlig'],['sr','Српски'],['st','Sesotho'],['sn','chiShona'],['sd','سنڌي'],['si','සිංහල'],['sk','Slovenčina'],['sl','Slovenščina'],['so','Soomaali'],['su','Basa Sunda'],['sv','Svenska'],['tg','Тоҷикӣ'],['ta','தமிழ்'],['tt','Tatarça'],['te','తెలుగు'],['th','ไทย'],['tk','Türkmençe'],['uk','Українська'],['ug','ئۇيغۇرچە'],['uz','Oʻzbekcha'],['vi','Tiếng Việt'],['cy','Cymraeg'],['xh','isiXhosa'],['yi','ייִדיש'],['zu','isiZulu']
  ];
  let langMap = Object.fromEntries(languages);
  const chosen = () => localStorage.getItem('risaala-language') || 'ar';
  const langSelects = [$('#language-select'), $('#settings-language')].filter(Boolean);
  const renderLanguages = () => langSelects.forEach(select => {
    const selected = chosen(); select.innerHTML = '';
    languages.forEach(([code, name]) => { const option = document.createElement('option'); option.value = code; option.textContent = name; select.append(option); });
    select.value = langMap[selected] ? selected : 'ar';
  });
  renderLanguages();
  const translationKey = window.RISAALA_CONFIG?.googleTranslationApiKey || '';
  if (translationKey) fetch(`https://translation.googleapis.com/language/translate/v2/languages?target=ar&key=${encodeURIComponent(translationKey)}`)
    .then(response => response.ok ? response.json() : Promise.reject(response.status))
    .then(data => { const available=data.data?.languages||[]; if(available.length){languages=available.map(item=>[item.language,item.name||item.language]);langMap=Object.fromEntries(languages);renderLanguages();} })
    .catch(error => console.warn('Could not fetch supported language list', error));
  const english = {
    'الرئيسية':'Home','عن المشروع':'About the project','الرحلة والخريطة':'Journey & Map','المصادر':'Sources','نبذة عنا':'About us','تسجيل الدخول':'Sign in','إنشاء حساب':'Create account','حسابي':'My account','الإعدادات':'Settings','دخول':'Sign in',
    'منصة معرفية تفاعلية':'An interactive knowledge platform','رحلة في سيرة النبي ﷺ':'A Journey Through the Prophet’s Biography','اكتشف محطات الرحلة وتعرّف على الأحداث التاريخية بأسلوب تفاعلي وموثوق.':'Explore key moments and historical events through an interactive, trusted experience.','ابحث عن محطة أو موضوع...':'Search for a stop or topic...','ابدأ الرحلة':'Begin the journey','محطات، خريطة تفاعلية، ومصادر موثوقة':'Stops, an interactive map, and trusted sources','محطات الرحلة':'Journey stops','اختر محطة وابدأ الاستكشاف':'Choose a stop to explore','تعرّف على الأحداث والمواقع المرتبطة بالسيرة، وانتقل من المحطة إلى مصادرها.':'Discover events and places from the biography, then explore their sources.','بداية الرسالة':'The beginning of the message','مكة المكرمة':'Makkah','الهجرة':'The Hijrah','إلى المدينة':'To Madinah','بدر':'Badr','غزوة بدر':'The Battle of Badr','فتح مكة':'The Conquest of Makkah','المدينة':'Madinah','بناء المجتمع':'Building a community','ما لقينا محطة بهذا الاسم. جربي كلمة ثانية.':'No stops found. Try another search.','الخريطة التفاعلية':'Interactive map','شاهد المحطات على الخريطة':'See the journey on the map','تنقّل بين مكة والمدينة وبدر وغيرها، واطّلع على النبذة النصية أو استمع إليها.':'Explore Makkah, Madinah, Badr, and more. Read or listen to each summary.','استكشف الخريطة':'Explore the map','عرض توضيحي':'Preview','رحلة عبر المكان والزمن':'A journey through place and time','افتح الخريطة لاختيار الأحداث والفترة الزمنية':'Open the map to choose events and a time period','محطات مقترحة للاستكشاف':'suggested stops to explore','هدف دقة إسناد للاختبار':'target source attribution accuracy','لغة مستهدفة':'target languages',
    'خريطة الرحلة':'Journey map','استكشف محطات السيرة النبوية على خريطة تضاريس ثلاثية الأبعاد. اختر حدثًا لقراءة نبذته أو الاستماع إليها.':'Explore journey stops on a 3D terrain map. Choose an event to read or hear its summary.','الكل':'All','الرحلات والهجرات':'Journeys & migrations','الأحداث المهمة':'Key events','الفترة الزمنية':'Time period','كل الفترات':'All periods','عرض مسطح':'Flat view','تضاريس':'Terrain','شبه الجزيرة العربية':'Arabian Peninsula','خريطة تفاعلية':'Interactive map','أهم الأحداث':'Key events','محطات':'stops','استمع للنبذة':'Listen to summary','صفحة المحطة':'Stop details','رحلة مختصرة':'Journey at a glance','عن مشروع رِسالة':'About Risaala','أهداف المشروع':'Project goals','معرفة يسهل استكشافها':'Knowledge made easy to explore','كيف تعمل الرحلة؟':'How does the journey work?','التقنيات المقترحة':'Proposed technologies','المشكلة والحل':'Challenge & solution','الجمهور المستهدف':'Who it is for','نبذة تاريخية':'Historical overview','الأحداث المرتبطة':'Related events','الأماكن المهمة':'Important places','اسأل عن هذه المحطة':'Ask about this stop','اكتب سؤالك هنا...':'Type your question...','إرسال':'Send','العودة إلى الخريطة':'Back to map','الفترة الزمنية':'Time period','الموقع':'Location','نوع المحطة':'Stop type','مكان':'Place','الكعبة المشرفة':'The Kaaba','المسجد الحرام':'The Grand Mosque','عرض المحطة على الخريطة':'Show on map','مرشدك في الرحلة':'Your journey guide','هذه المراجع واردة في نموذج المصادر. .':'These references are listed on the sources page.','عرض صفحة المصادر':'View sources','معاينة':'Preview','إعدادات اللغة والمظهر والصوت':'Language, appearance, and audio settings','اختر اللغة':'Choose language','حفظ التغييرات':'Save changes','الدخول إلى حسابك':'Sign in to your account','أدخل بريدك الإلكتروني أو رقم جوالك.':'Enter your email or mobile number.','البريد الإلكتروني أو رقم الجوال':'Email address or mobile number','كلمة المرور':'Password','الدخول عبر نفاذ':'Sign in with Nafath','قريبًا':'Coming soon','الاسم':'Name','الاسم الكامل':'Full name'
  };
  const applyEnglish = () => {
    const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT); const nodes=[];
    while(walker.nextNode()) nodes.push(walker.currentNode);
    for(const node of nodes){const value=node.nodeValue.trim(); if(english[value]) node.nodeValue=node.nodeValue.replace(value,english[value]);}
    $$('input[placeholder],input[aria-label],button[aria-label],select[aria-label]').forEach(el=>{
      for(const attr of ['placeholder','aria-label']) if(el.hasAttribute(attr)&&english[el.getAttribute(attr)]) el.setAttribute(attr,english[el.getAttribute(attr)]);
    });
  };
  const translatePage = async target => {
    const status = $('#language-status');
    const apiBase = window.RISAALA_CONFIG?.apiBaseUrl || 'http://127.0.0.1:8000';

    document.documentElement.lang = target;
    document.documentElement.dir = ['ar','he','fa','ur'].includes(target) ? 'rtl' : 'ltr';

    if (status) {
      status.textContent = '\u062c\u0627\u0631\u064d \u062a\u0631\u062c\u0645\u0629 \u0627\u0644\u0635\u0641\u062d\u0629\u2026';
    }

    const items = [];

    const walker = document.createTreeWalker(
      document.body,
      NodeFilter.SHOW_TEXT,
      {
        acceptNode(node) {
          const value = node.nodeValue.trim();
          if (!value || !/[\u0600-\u06FF]/.test(value)) {
            return NodeFilter.FILTER_REJECT;
          }

          const parent = node.parentElement;
          if (
            !parent ||
            parent.closest(
              'script,style,select,textarea,.notranslate,[aria-hidden="true"],#language-status'
            )
          ) {
            return NodeFilter.FILTER_REJECT;
          }

          return NodeFilter.FILTER_ACCEPT;
        }
      }
    );

    while (walker.nextNode()) {
      items.push({
        type: 'text',
        node: walker.currentNode,
        value: walker.currentNode.nodeValue.trim()
      });
    }

    $$('[placeholder],[aria-label],[title]').forEach(el => {
      if (el.closest('.notranslate')) return;

      ['placeholder','aria-label','title'].forEach(attr => {
        if (!el.hasAttribute(attr)) return;
        const value = el.getAttribute(attr)?.trim();
        if (value && /[\u0600-\u06FF]/.test(value)) {
          items.push({type:'attr', node:el, attr, value});
        }
      });
    });

    try {
      for (let start = 0; start < items.length; start += 40) {
        const batchItems = items.slice(start, start + 40);

        const response = await fetch(`${apiBase}/api/translate-batch`, {
          method: 'POST',
          headers: {'Content-Type':'application/json'},
          body: JSON.stringify({
            texts: batchItems.map(item => item.value),
            source_language: 'ar',
            target_language: target
          })
        });

        if (!response.ok) {
          throw new Error(`Translation request failed (${response.status})`);
        }

        const data = await response.json();
        const translations = data.translations || [];

        batchItems.forEach((item, index) => {
          const translated = translations[index];
          if (!translated || !item.node?.isConnected) return;

          if (item.type === 'text') {
            item.node.nodeValue = translated;
          } else {
            item.node.setAttribute(item.attr, translated);
          }
        });
      }

      if (status) {
        status.textContent =
          '\u062a\u0645 \u0639\u0631\u0636 \u0627\u0644\u0635\u0641\u062d\u0629 \u0628\u0644\u063a\u0629 ' +
          (langMap[target] || target);
      }
    } catch (error) {
      console.error(error);

      if (status) {
        status.textContent =
          '\u062a\u0639\u0630\u0631\u062a \u0627\u0644\u062a\u0631\u062c\u0645\u0629. \u062a\u0623\u0643\u062f\u064a \u0623\u0646 \u0627\u0644\u062e\u062f\u0645\u0629 \u0627\u0644\u062e\u0644\u0641\u064a\u0629 \u062a\u0639\u0645\u0644.';
      }
    }
  };

  const setLanguage = code => {
    localStorage.setItem('risaala-language',code);
    langSelects.forEach(select=>select.value=code);
    if(code==='ar') { location.reload(); return; }
    location.reload();
  };
  langSelects.forEach(select=>select.addEventListener('change',()=>setLanguage(select.value)));
  if(chosen()!=='ar') translatePage(chosen());

  const toggle = $('.menu-toggle');
  if (toggle) toggle.addEventListener('click', () => {
    const nav = $('.nav-links'); const open = nav?.classList.toggle('open');
    toggle.setAttribute('aria-expanded', String(Boolean(open)));
  });
  const current = location.pathname.split('/').pop() || 'index.html';
  $$('.nav-links a').forEach(a => { if (a.getAttribute('href') === current) a.classList.add('active'); });

  const eventData = {
    makkah: { title:'مكة المكرمة · بداية الرسالة', kicker:'المحطة الأولى', text:'في مكة المكرمة وُلد النبي ﷺ عام الفيل، وفيها نشأ وعُرف بين قومه بالصادق الأمين. وفي غار حراء المطل عليها نزل عليه الوحي أول مرة وهو في الأربعين، فبدأت الدعوة سرًّا ثم جهرًا، وصبر مع أصحابه ثلاث عشرة سنة على الأذى والحصار حتى أذن الله بالهجرة إلى المدينة.', meta:'مكة المكرمة · 610م' },
    hijrah: { title:'الهجرة إلى المدينة', kicker:'محطة انتقال', text:'بعد بيعة العقبة الثانية أذن النبي ﷺ لأصحابه بالهجرة إلى يثرب، ثم خرج مع أبي بكر الصديق ليلة ائتمرت قريش بقتله، فمكثا في غار ثور ثلاث ليال، ثم سلكا طريق الساحل حتى بلغا قباء في ربيع الأول. وفي المدينة بُني المسجد وآخى النبي ﷺ بين المهاجرين والأنصار، وبالهجرة أُرّخ التقويم الإسلامي.', meta:'المدينة المنورة · 622م' },
    badr: { title:'غزوة بدر', kicker:'حدث تاريخي', text:'في السابع عشر من رمضان من السنة الثانية للهجرة التقى ثلاثمئة وبضعة عشر مسلمًا بنحو ألف من قريش عند ماء بدر. انتهت المعركة بنصر حاسم للمسلمين ومقتل عدد من زعماء قريش، وسمّاها القرآن «يوم الفرقان».', meta:'بدر · 624م' },
    uhud: { title:'غزوة أحد', kicker:'حدث تاريخي', text:'في شوال من السنة الثالثة للهجرة خرجت قريش في ثلاثة آلاف تطلب الثأر لبدر. كانت الغلبة للمسلمين أول المعركة، ثم تبدّل الحال حين ترك أكثر الرماة مواقعهم على الجبل، فاستُشهد نحو سبعين من الصحابة، منهم حمزة بن عبد المطلب ومصعب بن عمير.', meta:'جبل أحد · 625م' },
    khaybar: { title:'فتح خيبر', kicker:'حدث تاريخي', text:'في المحرم من السنة السابعة للهجرة سار النبي ﷺ إلى حصون خيبر شمال المدينة، ففُتحت حصنًا بعد حصن، وأُعطيت الراية علي بن أبي طالب. وصالح النبي ﷺ أهلها على أن يعملوا في أرضها ولهم نصف ثمرها، وفيها قدم جعفر بن أبي طالب من الحبشة.', meta:'خيبر · 628م' },
    'makkah-opening': { title:'فتح مكة', kicker:'محطة في الخط الزمني', text:'في رمضان من السنة الثامنة للهجرة، وبعد أن نقضت قريش صلح الحديبية، سار النبي ﷺ في عشرة آلاف فدخل مكة من غير قتال يُذكر. طهّر الكعبة من الأصنام، وأمّن أهلها وعفا عنهم، فدخل الناس في دين الله أفواجًا.', meta:'مكة المكرمة · 630م' },
    isra: { title:'الإسراء والمعراج', kicker:'محطة في الرحلة', text:'أُسري بالنبي ﷺ ليلًا من المسجد الحرام إلى المسجد الأقصى، ثم عُرج به إلى السماوات العلى، وفيها فُرضت الصلوات الخمس. وقعت الحادثة قبل الهجرة بنحو سنة على المشهور، وجاءت تثبيتًا له بعد عام الحزن ورحلة الطائف.', meta:'المسجد الأقصى · 621م' }
  };
  const selectEvent = id => {
    const data = eventData[id]; if (!data) return;
    const title = $('#event-title'), copy = $('#event-copy'), kicker = $('#event-kicker');
    const englishEvent={makkah:['Makkah · The beginning of the message','First stop','The Prophet ﷺ was born in Makkah in the Year of the Elephant and grew up there, known among his people as the truthful and trustworthy. In the cave of Hira above the city the first revelation came to him at the age of forty. The call began in secret and then in public, and for thirteen years he and his companions endured persecution and boycott until the migration to Madinah.'],hijrah:['The Hijrah to Madinah','A turning point','After the second pledge of Aqabah the Prophet ﷺ allowed his companions to migrate to Yathrib. He left with Abu Bakr on the night Quraysh plotted to kill him, stayed three nights in the cave of Thawr, then took the coastal route and reached Quba in Rabi al-Awwal. In Madinah the mosque was built and the emigrants and helpers were made brothers; the Islamic calendar counts from this event.'],badr:['The Battle of Badr','Historical event','On 17 Ramadan in the second year after the Hijrah, a little over three hundred Muslims met about a thousand men of Quraysh at the wells of Badr. The battle ended in a decisive Muslim victory and the death of several Quraysh leaders. The Quran calls it the Day of the Criterion.'],uhud:['The Battle of Uhud','Historical event','In Shawwal of the third year after the Hijrah, Quraysh marched with three thousand men to avenge Badr. The Muslims prevailed at first, but the battle turned when most of the archers left their post on the hill. About seventy companions were martyred, among them Hamzah ibn Abd al-Muttalib and Musab ibn Umayr.'],khaybar:['The Conquest of Khaybar','Historical event','In Muharram of the seventh year after the Hijrah the Prophet ﷺ marched on the fortresses of Khaybar, north of Madinah. They fell one after another, with the banner given to Ali ibn Abi Talib. The people of Khaybar were allowed to stay and farm the land for half its produce, and Jafar ibn Abi Talib arrived there from Abyssinia.'],'makkah-opening':['The Conquest of Makkah','Timeline stop','In Ramadan of the eighth year after the Hijrah, after Quraysh broke the treaty of Hudaybiyyah, the Prophet ﷺ marched with ten thousand men and entered Makkah almost without fighting. He cleared the Kaaba of idols, granted its people safety and pardoned them, and people then entered Islam in great numbers.'],isra:['The Night Journey and Ascension','Journey stop','The Prophet ﷺ was taken by night from the Sacred Mosque to Al-Aqsa Mosque and then raised through the heavens, where the five daily prayers were prescribed. By the best-known account it took place about a year before the Hijrah, as a consolation after the Year of Sorrow and the journey to Taif.']}[id];
    if (title) title.textContent = chosen()==='en'&&englishEvent ? englishEvent[0] : data.title;
    if (copy) copy.textContent = chosen()==='en'&&englishEvent ? englishEvent[2] : data.text;
    if (kicker) kicker.textContent = chosen()==='en'&&englishEvent ? englishEvent[1] : data.kicker;
    const lang=chosen(), key=translationKey;
    if(lang!=='ar'){
      const apiBase=window.RISAALA_CONFIG?.apiBaseUrl||'http://127.0.0.1:8000';
      fetch(`${apiBase}/api/translate-batch`,{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({
          texts:[data.title,data.kicker,data.text,data.meta],
          source_language:'ar',
          target_language:lang
        })
      }).then(r=>r.ok?r.json():Promise.reject(r.status))
        .then(result=>{
          const t=result.translations||[];
          if(t.length>=4){
            if(title)title.textContent=t[0];
            if(kicker)kicker.textContent=t[1];
            if(copy)copy.textContent=t[2];
            const metaDate=$('.event-meta span:nth-child(2)');
            if(metaDate)metaDate.textContent=t[3];
          }
        }).catch(()=>{});
    }
    const meta = $('.event-meta span:nth-child(1)'); if (meta) meta.textContent = `⌖ ${chosen()==='en'&&englishEvent ? ({makkah:'Makkah',hijrah:'Madinah',badr:'Badr',uhud:'Uhud',khaybar:'Khaybar','makkah-opening':'Makkah',isra:'Makkah'}[id]) : data.meta.split(' · ')[0]}`;
    const metaDate = $('.event-meta span:nth-child(2)'); if (metaDate) metaDate.textContent = `◷ ${chosen()==='en'&&englishEvent ? data.meta.split(' · ').slice(1).join(' · ').replace('م',' CE') : data.meta.split(' · ').slice(1).join(' · ') || 'قبل الهجرة'}`;
    const stationLink=$('#station-page-link'); if(stationLink)stationLink.href=`station.html?event=${encodeURIComponent(id)}`;
    $$('.map-pin,.event-row').forEach(el => el.classList.toggle('selected', el.dataset.event === id));
    localStorage.setItem('risaala-last-event', id);
  };
  $$('[data-event]').forEach(el => el.addEventListener('click', () => selectEvent(el.dataset.event)));
  const savedEvent = localStorage.getItem('risaala-last-event'); selectEvent(savedEvent && eventData[savedEvent] ? savedEvent : 'makkah');

  const stationData={
    makkah:{title:'مكة المكرمة',subtitle:'بداية الرسالة',period:'العهد المكي · 610 – 622م',location:'مكة المكرمة',heading:'مكة المكرمة · بداية الرسالة',copy:'مكة المكرمة هي البلد الحرام الذي رفع فيه إبراهيم وإسماعيل عليهما السلام قواعد الكعبة، وفيها وُلد النبي محمد ﷺ عام الفيل، نحو سنة 570م. كانت مركزًا تجاريًّا مهمًّا على طريق القوافل بين اليمن والشام، ومقصدًا يحج إليه العرب من مختلف القبائل، وتولّت قريش فيها سقاية الحجيج ورفادتهم. نشأ النبي ﷺ فيها يتيمًا، وعُرف بين أهلها بالصادق الأمين، وحكّموه في وضع الحجر الأسود عند تجديد بناء الكعبة.\n\nوفي غار حراء بجبل النور المطل على مكة نزل عليه الوحي أول مرة في رمضان وهو في الأربعين، نحو سنة 610م، بقوله تعالى: «اقرأ باسم ربك الذي خلق». فبدأ دعوته سرًّا نحو ثلاث سنين، ثم جهر بها من فوق جبل الصفا. ولقي هو وأصحابه من قريش الأذى والتعذيب والمقاطعة في شعب أبي طالب، فهاجر بعضهم إلى الحبشة، وصبر الباقون ثلاث عشرة سنة حتى أذن الله بالهجرة إلى المدينة سنة 622م. ثم عاد ﷺ إلى مكة فاتحًا في السنة الثامنة للهجرة، فطهّر البيت من الأصنام وعفا عن أهلها.'},
    hijrah:{title:'الهجرة إلى المدينة',subtitle:'محطة انتقال وبداية مرحلة جديدة',period:'622م · 1هـ',location:'من مكة إلى المدينة',heading:'الهجرة النبوية',copy:'لما هاجر أكثر الصحابة إلى يثرب اجتمع زعماء قريش في دار الندوة، وأجمعوا أن يأخذوا من كل قبيلة فتى فيضربوا النبي ﷺ ضربة رجل واحد ليتفرق دمه في القبائل. قال تعالى: «وإذ يمكر بك الذين كفروا ليثبتوك أو يقتلوك أو يخرجوك». فأذن الله لنبيه بالهجرة، فخرج ليلًا وترك عليًّا في فراشه ليردّ الودائع إلى أهلها. وسار مع أبي بكر الصديق إلى غار ثور جنوب مكة، فمكثا فيه ثلاث ليال، يأتيهما عبد الله بن أبي بكر بالأخبار، وأسماء ذات النطاقين بالطعام، وعامر بن فهيرة بالغنم يعفّي الأثر. وبلغ المشركون فم الغار، فقال ﷺ لصاحبه: «ما ظنك باثنين الله ثالثهما؟».\n\nثم سلكا طريق الساحل مع الدليل عبد الله بن أريقط، ولحق بهما سراقة بن مالك طمعًا في الجائزة فساخت قوائم فرسه، فرجع يصرف عنهما الطلب. ووصل ﷺ قباء يوم الاثنين من ربيع الأول، في سبتمبر 622م، فأسّس مسجدها، ثم دخل المدينة والناس يستقبلونه، ونزل في دار أبي أيوب الأنصاري. وبهذه الهجرة أرّخ المسلمون تقويمهم في خلافة عمر.'},
    badr:{title:'بدر',subtitle:'غزوة بدر',period:'624م · 2هـ',location:'بدر',heading:'غزوة بدر',copy:'في رمضان من السنة الثانية للهجرة، مارس 624م، خرج النبي ﷺ في ثلاثمئة وبضعة عشر رجلًا، معهم فَرَسان وسبعون بعيرًا يتعاقبون عليها، يريدون قافلة لقريش عائدة من الشام بقيادة أبي سفيان، وكانت قريش قد استولت على أموال المهاجرين بمكة. فنجا أبو سفيان بالقافلة عن طريق الساحل، لكن قريشًا خرجت في نحو ألف مقاتل وأصرّ أبو جهل على القتال. فاستشار النبي ﷺ أصحابه، فتكلم المقداد بن عمرو عن المهاجرين، ثم قال سعد بن معاذ عن الأنصار: «لو استعرضت بنا هذا البحر فخضته لخضناه معك».\n\nونزل المسلمون عند ماء بدر بمشورة الحُباب بن المنذر، وبات النبي ﷺ يدعو ربه: «اللهم إن تهلك هذه العصابة لا تُعبد في الأرض». والتقى الجمعان صبيحة السابع عشر من رمضان، وأمدّ الله المؤمنين بالملائكة، فانتهت المعركة بنصر حاسم: قُتل سبعون من المشركين فيهم أبو جهل وأمية بن خلف، وأُسر سبعون، واستُشهد أربعة عشر من المسلمين. وجُعل فداء بعض الأسرى أن يعلّم عشرة من أبناء المدينة الكتابة. وسمّاه القرآن «يوم الفرقان».'},
    uhud:{title:'أحد',subtitle:'غزوة أحد',period:'625م · 3هـ',location:'جبل أحد · المدينة',heading:'غزوة أحد',copy:'في شوال من السنة الثالثة للهجرة، مارس 625م، زحفت قريش في ثلاثة آلاف مقاتل بقيادة أبي سفيان تطلب الثأر لقتلى بدر. فاستشار النبي ﷺ أصحابه، ثم خرج في نحو ألف، فانخذل رأس المنافقين عبد الله بن أُبيّ بثلث الجيش في الطريق. ونزل المسلمون بسفح جبل أحد شمال المدينة وجعلوا ظهورهم إليه، وأقام النبي ﷺ خمسين راميًا على جبل صغير بقيادة عبد الله بن جبير، وأمرهم ألا يبرحوا مكانهم سواء كان النصر أو الهزيمة.\n\nكانت الغلبة للمسلمين أول النهار وولّى المشركون، فظنّ أكثر الرماة أن المعركة انتهت فنزلوا يطلبون الغنيمة. فانتهز خالد بن الوليد الثغرة والتفّ بالفرسان من الخلف، فاضطرب الصف، وشاع أن النبي ﷺ قُتل، وقد شُجّ وجهه وكُسرت رباعيته وثبتت معه قلة من أصحابه يفدونه بأنفسهم. واستُشهد نحو سبعين، فيهم حمزة بن عبد المطلب ومصعب بن عمير وأنس بن النضر. ونزلت آيات آل عمران تعزّي وتربّي: «ولا تهنوا ولا تحزنوا وأنتم الأعلون إن كنتم مؤمنين». وبقي درس أحد شاهدًا على أثر مخالفة الأمر.'},
    khaybar:{title:'خيبر',subtitle:'فتح خيبر',period:'628م · 7هـ',location:'خيبر',heading:'فتح خيبر',copy:'كانت خيبر واحة حصينة شمال المدينة، كثيرة النخل والحصون، وقد صارت بعد إجلاء بني النضير مركزًا للتأليب على المسلمين، ومنها خرج من حزّب الأحزاب يوم الخندق. فلما أمن النبي ﷺ جانب قريش بصلح الحديبية، سار إليها في المحرم من السنة السابعة للهجرة، سنة 628م، في نحو ألف وأربعمئة ممن شهدوا الحديبية. فحاصر حصونها واحدًا بعد واحد: ناعم، والصعب بن معاذ، والقَموص، ثم الوَطيح والسُّلالم.\n\nواستعصى أحد الحصون أيامًا، فقال ﷺ كما في الصحيحين: «لأعطينّ الراية غدًا رجلًا يحب الله ورسوله ويحبه الله ورسوله، يفتح الله على يديه». فدعا عليًّا وكان يشتكي عينيه، فبصق فيهما ودعا له فبرئ، وأوصاه: «لأن يهدي الله بك رجلًا واحدًا خير لك من حُمر النعم». ففتح الله عليه. ثم صالح أهل خيبر على أن يبقوا في أرضهم يعملون فيها ولهم نصف ثمرها. وفي خيبر قدم جعفر بن أبي طالب ومن معه من مهاجري الحبشة، وتزوج النبي ﷺ صفية بنت حُيي.'},
    'makkah-opening':{title:'فتح مكة',subtitle:'العودة إلى مكة',period:'630م · 8هـ',location:'مكة المكرمة',heading:'فتح مكة',copy:'أعانت قريش حلفاءها بني بكر على خزاعة حلفاء النبي ﷺ فقتلوا منهم رجالًا، فكان ذلك نقضًا لصلح الحديبية. وقدم عمرو بن سالم الخزاعي المدينة يستنصر، ثم جاء أبو سفيان يطلب تجديد العهد فلم يُجَب. وتجهّز النبي ﷺ في كتمان شديد، وخرج في رمضان من السنة الثامنة للهجرة، يناير 630م، في عشرة آلاف. فلما نزل بمرّ الظهران أسلم أبو سفيان، وأعلن النبي ﷺ الأمان: «من دخل دار أبي سفيان فهو آمن، ومن أغلق عليه بابه فهو آمن، ومن دخل المسجد فهو آمن».\n\nودخل ﷺ مكة من أعلاها خاشعًا متواضعًا يقرأ سورة الفتح، ولم يقع قتال إلا مناوشة يسيرة في الجهة التي دخل منها خالد بن الوليد. وطاف بالبيت وحوله ثلاثمئة وستون صنمًا، فجعل يطعنها وهو يقول: «جاء الحق وزهق الباطل». ثم خاطب أهل مكة الذين آذوه وأخرجوه، فعفا عنهم، ويروي ابن إسحاق قوله: «اذهبوا فأنتم الطلقاء». وردّ مفتاح الكعبة إلى عثمان بن طلحة، وأذّن بلال فوق الكعبة. ودخل الناس بعد الفتح في دين الله أفواجًا.'},
    isra:{title:'الإسراء والمعراج',subtitle:'حدث في السيرة النبوية',period:'نحو 621م · قبل الهجرة',location:'من المسجد الحرام إلى المسجد الأقصى',heading:'الإسراء والمعراج',copy:'بعد عام الحزن ورحلة الطائف أكرم الله نبيه ﷺ برحلة الإسراء والمعراج. قال تعالى: «سبحان الذي أسرى بعبده ليلًا من المسجد الحرام إلى المسجد الأقصى الذي باركنا حوله لنريه من آياتنا». وقد اختلف أهل السير في تاريخها، والمشهور أنها كانت قبل الهجرة بنحو سنة. أُسري به ﷺ على البراق من مكة إلى بيت المقدس، فصلى هناك بالأنبياء إمامًا، ثم عُرج به إلى السماوات.\n\nوفي الصحيحين أنه لقي في السماوات آدم، ثم يحيى وعيسى، ثم يوسف، ثم إدريس، ثم هارون، ثم موسى، ثم إبراهيم عليهم السلام، ثم رُفع إلى سدرة المنتهى. وهناك فُرضت الصلاة خمسين صلاة، فما زال يراجع ربه بمشورة موسى عليه السلام حتى صارت خمسًا في العمل وخمسين في الأجر. فلما أصبح أخبر قريشًا فكذّبوه واستعظموا الأمر، فوصف لهم بيت المقدس وصفًا دقيقًا. وأما أبو بكر فقال: «إن كان قال فقد صدق»، فلُقّب بالصدّيق.'}
  };
  const params=new URLSearchParams(location.search), requested=params.get('event');
  if($('#station-title')){
    const stop=stationData[requested]||stationData.makkah;
    const englishStops={makkah:['Makkah','The beginning of the message','Makkan period · 610 – 622 CE','Makkah','Makkah · The beginning of the message','Makkah is the sacred city where Ibrahim and Ismail, peace be upon them, raised the foundations of the Kaaba, and where Prophet Muhammad ﷺ was born in the Year of the Elephant, around 570 CE. It was an important trading center on the caravan route between Yemen and Syria and a place of pilgrimage for the Arab tribes, with Quraysh serving the pilgrims. He grew up there an orphan, known as the truthful and trustworthy, and was chosen to settle the dispute over the Black Stone when the Kaaba was rebuilt.\n\nIn the cave of Hira on the Mountain of Light the first revelation came to him in Ramadan at the age of forty, around 610 CE: “Read in the name of your Lord who created.” He called people in secret for about three years, then publicly from Mount Safa. He and his companions faced persecution and a boycott in the valley of Abu Talib; some migrated to Abyssinia, and the rest endured for thirteen years until the migration to Madinah in 622 CE. He returned to Makkah in the eighth year after the Hijrah, cleared the Kaaba of idols and pardoned its people.'],hijrah:['The Hijrah to Madinah','A transition and a new beginning','622 CE · 1 AH','From Makkah to Madinah','The Prophet’s migration','After most of the companions had left for Yathrib, the leaders of Quraysh met in Dar al-Nadwah and agreed that a young man from every clan would strike the Prophet ﷺ together. He left by night, leaving Ali in his bed to return the deposits people had entrusted to him, and went with Abu Bakr to the cave of Thawr south of Makkah, where they stayed three nights. When the pursuers reached the mouth of the cave he said to his companion: “What do you think of two whose third is Allah?”\n\nThey then took the coastal route with their guide Abdullah ibn Urayqit. Suraqah ibn Malik overtook them hoping for the reward, but his horse sank into the ground and he turned back. The Prophet ﷺ reached Quba on a Monday in Rabi al-Awwal, September 622 CE, founded its mosque, then entered Madinah and stayed in the house of Abu Ayyub al-Ansari. The Muslim calendar was later dated from this migration during the caliphate of Umar.'],badr:['Badr','The Battle of Badr','624 CE · 2 AH','Badr','The Battle of Badr','In Ramadan of the second year after the Hijrah, March 624 CE, the Prophet ﷺ set out with a little over three hundred men, two horses and seventy camels to intercept a Quraysh caravan returning from Syria under Abu Sufyan. The caravan escaped along the coast, but Quraysh marched out with about a thousand fighters. The Prophet ﷺ consulted his companions, and Sad ibn Muadh answered for the Ansar that they would follow him even into the sea.\n\nThe Muslims camped by the wells of Badr on the advice of al-Hubab ibn al-Mundhir. The two sides met on the morning of 17 Ramadan and the battle ended in a decisive victory: seventy of Quraysh were killed, among them Abu Jahl and Umayyah ibn Khalaf, seventy were captured, and fourteen Muslims were martyred. Some captives were ransomed by teaching ten children of Madinah to write. The Quran calls it the Day of the Criterion.'],uhud:['Uhud','The Battle of Uhud','625 CE · 3 AH','Mount Uhud · Madinah','The Battle of Uhud','In Shawwal of the third year after the Hijrah, March 625 CE, Quraysh marched with three thousand fighters under Abu Sufyan to avenge Badr. The Prophet ﷺ went out with about a thousand men, and Abdullah ibn Ubayy withdrew on the way with a third of the army. The Muslims camped at the foot of Mount Uhud, north of Madinah, and fifty archers under Abdullah ibn Jubayr were posted on a small hill with orders not to leave it whatever happened.\n\nThe Muslims prevailed at first and the enemy fled. Most of the archers then came down to collect the spoils, and Khalid ibn al-Walid led the cavalry around through the gap. The ranks were thrown into confusion, the Prophet ﷺ was wounded, and a rumor spread that he had been killed. About seventy companions were martyred, among them Hamzah ibn Abd al-Muttalib and Musab ibn Umayr. Verses of Surah Al Imran were revealed to console and teach the believers.'],khaybar:['Khaybar','The Conquest of Khaybar','628 CE · 7 AH','Khaybar','The Conquest of Khaybar','Khaybar was a fortified oasis north of Madinah, rich in date palms. After the expulsion of Banu al-Nadir it had become a center for stirring up the tribes against the Muslims, and the confederates of the Trench were gathered from there. Once the treaty of Hudaybiyyah had secured peace with Quraysh, the Prophet ﷺ marched on it in Muharram of the seventh year after the Hijrah, 628 CE, with about fourteen hundred men, and besieged its fortresses one after another.\n\nWhen one fortress held out he said: “Tomorrow I shall give the banner to a man who loves Allah and His Messenger, and whom Allah and His Messenger love.” He gave it to Ali ibn Abi Talib, and the fortress was taken. The people of Khaybar were then allowed to stay and work the land for half its produce. At Khaybar Jafar ibn Abi Talib arrived with the emigrants returning from Abyssinia.'],'makkah-opening':['The Conquest of Makkah','Return to Makkah','630 CE · 8 AH','Makkah','The Conquest of Makkah','Quraysh helped their allies Banu Bakr attack Khuzaah, the allies of the Prophet ﷺ, which broke the treaty of Hudaybiyyah. He prepared in great secrecy and set out in Ramadan of the eighth year after the Hijrah, January 630 CE, with ten thousand men. At Marr al-Zahran Abu Sufyan accepted Islam, and safety was announced for whoever entered his house, stayed behind his own door, or entered the mosque.\n\nThe Prophet ﷺ entered Makkah humbly, reciting Surah al-Fath, and there was no fighting apart from a brief skirmish on the side where Khalid ibn al-Walid entered. He went around the Kaaba, struck down the three hundred and sixty idols around it saying “Truth has come and falsehood has vanished,” and pardoned the people who had persecuted and expelled him. He returned the key of the Kaaba to Uthman ibn Talhah, and Bilal called the prayer from its roof.'],isra:['The Night Journey and Ascension','An event in the biography','c. 621 CE · before the Hijrah','From the Sacred Mosque to Al-Aqsa Mosque','The Night Journey and Ascension','After the Year of Sorrow and the journey to Taif, the Prophet ﷺ was honored with the Night Journey and Ascension. The Quran says: “Glory be to Him who took His servant by night from the Sacred Mosque to the Farthest Mosque, whose surroundings We have blessed.” Biographers differ on its date; the best-known view is that it took place about a year before the Hijrah. He was carried on the Buraq to Jerusalem, where he led the prophets in prayer, and was then raised through the heavens.\n\nThere he met Adam, Yahya and Isa, Yusuf, Idris, Harun, Musa and Ibrahim, peace be upon them, and was raised to the Lote Tree of the Utmost Boundary. Prayer was prescribed there, fifty prayers reduced to five. When he told Quraysh in the morning they denied it, and he described Jerusalem to them in detail. Abu Bakr said: “If he said it, then it is true,” and was called al-Siddiq.']}[requested]||null;
    $('#station-title').textContent=chosen()==='en'&&englishStops?englishStops[0]:stop.title; $('#station-subtitle').textContent=chosen()==='en'&&englishStops?englishStops[1]:stop.subtitle;
    $('#station-period').textContent=chosen()==='en'&&englishStops?englishStops[2]:stop.period; $('#station-location').textContent=chosen()==='en'&&englishStops?englishStops[3]:stop.location;
    $('#station-event-heading').textContent=chosen()==='en'&&englishStops?englishStops[4]:stop.heading; $('#station-copy').textContent=chosen()==='en'&&englishStops?englishStops[5]:stop.copy;
    const tag=$('.station-hero .tag'); if(tag)tag.textContent=`${chosen()==='en'?'Stop':'محطة'} · ${chosen()==='en'&&englishStops?englishStops[3]:stop.location}`;
    if(chosen()!=='ar'&&chosen()!=='en'&&translationKey){
      const fields=[$('#station-title'),$('#station-subtitle'),$('#station-period'),$('#station-location'),$('#station-event-heading'),$('#station-copy')];
      const originals=[stop.title,stop.subtitle,stop.period,stop.location,stop.heading,stop.copy];
      const apiBase=window.RISAALA_CONFIG?.apiBaseUrl||'http://127.0.0.1:8000';
      fetch(`${apiBase}/api/translate-batch`,{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({
          texts:originals,
          source_language:'ar',
          target_language:chosen()
        })
      }).then(r=>r.ok?r.json():Promise.reject(r.status))
        .then(result=>(result.translations||[]).forEach((item,i)=>{
          if(fields[i]&&item)fields[i].textContent=item;
        }))
        .catch(()=>{});
    }
  }
  $$('.station-tab').forEach(button=>button.addEventListener('click',()=>{
    $$('.station-tab').forEach(tab=>tab.classList.toggle('active',tab===button));
    $$('.station-panel').forEach(panel=>panel.hidden=panel.id!==`tab-${button.dataset.tab}`);
  }));


const attachSpeechToggle = (selector, getText) => {
  const button = $(selector);
  if (!button) return;

  const originalLabel = button.innerHTML;

  button.addEventListener('click', () => {
    if (localStorage.getItem('risaala-voice') === 'off') {
      alert('الصوت متوقف من الإعدادات.');
      return;
    }

    if (!('speechSynthesis' in window)) {
      alert('ميزة القراءة الصوتية غير متاحة في هذا المتصفح.');
      return;
    }

    const speech = window.speechSynthesis;

    // إذا كان التعليق متوقفًا مؤقتًا، تابعي من مكان التوقف
    if (speech.paused) {
      speech.resume();
      button.textContent = '⏸ إيقاف مؤقت';
      return;
    }

    // إذا كان التعليق يعمل، أوقفيه مؤقتًا
    if (speech.speaking) {
      speech.pause();
      button.textContent = '▶ متابعة التعليق الصوتي';
      return;
    }

    const text = getText().trim();
    if (!text) return;

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = chosen() === 'ar' ? 'ar-SA' : chosen();
    utterance.rate = 0.92;

    utterance.onend = () => {
      button.innerHTML = originalLabel;
    };

    utterance.onerror = () => {
      button.innerHTML = originalLabel;
    };

    button.innerHTML = originalLabel;
    speech.speak(utterance);
    button.textContent = '⏸ إيقاف مؤقت';
  });
};

// زر صفحة المحطة
attachSpeechToggle('#station-speak', () =>
  $('#station-copy')?.textContent || ''
);

// زر صفحة الخريطة
attachSpeechToggle('#speak-event', () =>
  `${$('#event-title')?.textContent || ''}. ${$('#event-copy')?.textContent || ''}`
);


    
  $$('.suggested-questions [data-question]').forEach(button=>button.addEventListener('click',()=>{const input=$('#guide-question');if(input)input.value=button.dataset.question;}));
  $('#guide-form')?.addEventListener('submit', async e => {
    e.preventDefault();

    const input = $('#guide-question');
    const box = $('#guide-answer');
    const question = input?.value.trim();

    if (!box || !question) return;

    const apiBase = window.RISAALA_CONFIG?.apiBaseUrl || 'http://127.0.0.1:8000';
    const lang = chosen();

    const translateTexts = async (texts, sourceLanguage, targetLanguage) => {
      if (sourceLanguage === targetLanguage) return texts;

      const response = await fetch(`${apiBase}/api/translate-batch`, {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({
          texts,
          source_language: sourceLanguage,
          target_language: targetLanguage
        })
      });

      if (!response.ok) {
        throw new Error(`Translation HTTP ${response.status}`);
      }

      const data = await response.json();
      return data.translations || texts;
    };

    let loadingText =
      '\u062c\u0627\u0631\u064a \u0627\u0644\u0628\u062d\u062b \u0641\u064a \u0627\u0644\u0645\u0635\u0627\u062f\u0631 \u0627\u0644\u0645\u0648\u062b\u0642\u0629...';

    if (lang !== 'ar') {
      try {
        [loadingText] = await translateTexts(
          [loadingText],
          'ar',
          lang
        );
      } catch (error) {
        console.warn('Could not translate loading message', error);
      }
    }

    box.textContent = loadingText;
    box.classList.add('show');

    try {
      let guideQuestion = question;

      // If the interface is not Arabic and the user typed in that language,
      // translate the question to Arabic before sending it to the Arabic RAG.
      if (
        lang !== 'ar' &&
        !/[\u0600-\u06FF]/.test(question)
      ) {
        try {
          const translatedQuestion = await translateTexts(
            [question],
            lang,
            'ar'
          );

          if (translatedQuestion[0]) {
            guideQuestion = translatedQuestion[0];
          }
        } catch (error) {
          console.warn('Could not translate guide question', error);
        }
      }

      const response = await fetch(`${apiBase}/api/guide`, {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({question: guideQuestion})
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();

      let answerText =
        data.answer ||
        '\u0644\u0645 \u064a\u062a\u0645 \u0627\u0644\u0639\u062b\u0648\u0631 \u0639\u0644\u0649 \u0625\u062c\u0627\u0628\u0629.';

      let sourcesLabel = '\u0627\u0644\u0645\u0635\u0627\u062f\u0631:';
      let pageLabel = '\u0635\u0641\u062d\u0629';

      if (lang !== 'ar') {
        try {
          const translatedUi = await translateTexts(
            [answerText, sourcesLabel, pageLabel],
            'ar',
            lang
          );

          answerText = translatedUi[0] || answerText;
          sourcesLabel = translatedUi[1] || sourcesLabel;
          pageLabel = lang === 'en'
            ? 'p.'
            : (translatedUi[2] || pageLabel);
        } catch (error) {
          console.warn('Could not translate guide answer', error);
        }
      }

      box.textContent = '';

      const answer = document.createElement('p');
      answer.textContent = answerText;
      box.appendChild(answer);

      if (Array.isArray(data.sources) && data.sources.length) {
        const title = document.createElement('strong');
        title.textContent = sourcesLabel;
        box.appendChild(title);

        const list = document.createElement('ul');

        data.sources.slice(0, 5).forEach(source => {
          const item = document.createElement('li');

          const sourceName =
            (source.source || '\u0645\u0635\u062f\u0631 \u0645\u0648\u062b\u0642')
              .split(/[\\/]/)
              .pop()
              .replace(/\.txt$/i, '');

          item.textContent = source.page
            ? `${sourceName} \u2014 ${pageLabel} ${source.page}`
            : sourceName;

          list.appendChild(item);
        });

        box.appendChild(list);
      }
    } catch (error) {
      console.error('Guide error:', error);

      let errorText =
        '\u062a\u0639\u0630\u0631 \u0627\u0644\u0627\u062a\u0635\u0627\u0644 \u0628\u0627\u0644\u0645\u0631\u0634\u062f. \u062a\u0623\u0643\u062f\u064a \u0623\u0646 \u0627\u0644\u062e\u062f\u0645\u0629 \u0627\u0644\u062e\u0644\u0641\u064a\u0629 \u062a\u0639\u0645\u0644 \u062b\u0645 \u062d\u0627\u0648\u0644\u064a \u0645\u0631\u0629 \u0623\u062e\u0631\u0649.';

      if (lang === 'en') {
        errorText =
          'Could not connect to the guide. Make sure the backend service is running, then try again.';
      }

      box.textContent = errorText;
    }
  });


    $('#station-search-form')?.addEventListener('submit', e => {
  e.preventDefault();

  const input = $('#station-search');
  const query = (input?.value || '').trim().toLocaleLowerCase();

  if (!query) return;

  const cards = $$('[data-home-station]');

  const match = cards.find(card =>
    card.textContent.toLocaleLowerCase().includes(query)
  );

  if (match) {
    window.location.href = match.getAttribute('href');
    return;
  }

  const empty = $('#search-empty');
  if (empty) empty.hidden = false;
});

    
    $('#station-search')?.addEventListener('input',e=>{
    const query=e.target.value.trim().toLocaleLowerCase();let visible=0;
    $$('[data-home-station]').forEach(card=>{const match=card.textContent.toLocaleLowerCase().includes(query);card.hidden=!match;if(match)visible++;});
    const empty=$('#search-empty');if(empty)empty.hidden=visible>0;
  });

  const map = $('#journey-map'), plane = $('#terrain-plane'); let zoom = 1;
  $$('.mode-button').forEach(button => button.addEventListener('click', () => {
    const flat = button.dataset.mode === 'flat'; map?.classList.toggle('map-flat', flat); map?.classList.toggle('map-3d', !flat);
    $$('.mode-button').forEach(b => b.classList.toggle('active', b === button));
  }));
  const applyZoom = () => { if (map) map.style.setProperty('--map-zoom', zoom); };
  $('#zoom-in')?.addEventListener('click', () => { zoom = Math.min(1.65, +(zoom + .12).toFixed(2)); applyZoom(); });
  $('#zoom-out')?.addEventListener('click', () => { zoom = Math.max(.82, +(zoom - .12).toFixed(2)); applyZoom(); });
  $('#reset-map')?.addEventListener('click', () => { zoom = 1; applyZoom(); });
  const categories = {makkah:'events',hijrah:'hijra',badr:'events',uhud:'events',khaybar:'events',isra:'events','makkah-opening':'events'};
  const periods={makkah:'570',hijrah:'622',badr:'624',uhud:'625',khaybar:'',isra:'621','makkah-opening':'630'};
  $$('.map-pin,.event-row').forEach(el=>el.dataset.period=periods[el.dataset.event]||'');
  let activeCategory='all', activePeriod='all';
  const applyMapFilters=()=>$$('.map-pin,.event-row').forEach(el=>{
    const id=el.dataset.event;
    el.hidden=(activeCategory!=='all'&&activeCategory!=='timeline'&&categories[id]!==activeCategory)||(activePeriod!=='all'&&el.dataset.period!==activePeriod);
  });
  $$('.filter-chip').forEach(button => button.addEventListener('click', () => {
    const filter = button.dataset.filter; activeCategory=filter;
    $$('.filter-chip').forEach(b => b.classList.toggle('active', b === button));
    applyMapFilters();
  }));
  $('#period-filter')?.addEventListener('change',e=>{
    activePeriod=e.target.value; applyMapFilters();
  });



  let authMode='login';
  const setAuthMode=mode=>{
    authMode=mode==='register'?'register':'login';
    const creating=authMode==='register', form=$('#login-form'); if(form)form.dataset.mode=authMode;
    $$('.auth-tab').forEach(tab=>{const active=tab.dataset.authMode===authMode;tab.classList.toggle('active',active);tab.setAttribute('aria-selected',String(active));});
    const nameWrap=$('#register-name-wrap');if(nameWrap)nameWrap.hidden=!creating;
    const nafath=$('#nafath-button');if(nafath)nafath.hidden=creating;
    const title=$('#auth-title');if(title)title.textContent=chosen()==='en'?(creating?'Create a new account':'Sign in to your account'):(creating?'إنشاء حساب جديد':'الدخول إلى حسابك');
    const description=$('#auth-description');if(description)description.textContent=chosen()==='en'?(creating?'Enter your name and email or mobile number to create a demo account.':'Enter your email or mobile number.'):(creating?'أدخل اسمك وبريدك الإلكتروني أو رقم جوالك لإنشاء حساب جديد.':'أدخل بريدك الإلكتروني أو رقم جوالك.');
    const submit=$('#auth-submit');if(submit)submit.textContent=chosen()==='en'?(creating?'Create account':'Sign in'):(creating?'إنشاء حساب':'تسجيل الدخول');
    const password=$('#login-password');if(password)password.autocomplete=creating?'new-password':'current-password';
    const feedback=$('#login-feedback');if(feedback)feedback.textContent='';
  };
  $$('.auth-tab').forEach(tab=>tab.addEventListener('click',()=>setAuthMode(tab.dataset.authMode)));
  if($('#login-form')&&chosen()==='en')setAuthMode('login');
  $('#login-form')?.addEventListener('submit', async e => {
    e.preventDefault();

    const email = $('#login-id').value.trim().toLowerCase();
    const password = $('#login-password').value;
    const displayName = $('#register-name')?.value.trim() || '';
    const feedback = $('#login-feedback');
    const submit = $('#auth-submit');
    const apiBase = window.RISAALA_CONFIG?.apiBaseUrl || 'http://127.0.0.1:8000';

    const validEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);

    if (!validEmail) {
      feedback.textContent = '\u0623\u062f\u062e\u0644\u064a \u0628\u0631\u064a\u062f\u064b\u0627 \u0625\u0644\u0643\u062a\u0631\u0648\u0646\u064a\u064b\u0627 \u0635\u062d\u064a\u062d\u064b\u0627.';
      return;
    }

    if (authMode === 'register' && !displayName) {
      feedback.textContent = '\u0623\u062f\u062e\u0644\u064a \u0627\u0633\u0645\u0643 \u0644\u0625\u0643\u0645\u0627\u0644 \u0625\u0646\u0634\u0627\u0621 \u0627\u0644\u062d\u0633\u0627\u0628.';
      return;
    }

    if (password.length < 8) {
      feedback.textContent = '\u0643\u0644\u0645\u0629 \u0627\u0644\u0645\u0631\u0648\u0631 \u064a\u062c\u0628 \u0623\u0646 \u062a\u062a\u0643\u0648\u0646 \u0645\u0646 8 \u0623\u062d\u0631\u0641 \u0639\u0644\u0649 \u0627\u0644\u0623\u0642\u0644.';
      return;
    }

    submit.disabled = true;
    feedback.textContent = authMode === 'register'
      ? '\u062c\u0627\u0631\u064a \u0625\u0646\u0634\u0627\u0621 \u0627\u0644\u062d\u0633\u0627\u0628...'
      : '\u062c\u0627\u0631\u064a \u062a\u0633\u062c\u064a\u0644 \u0627\u0644\u062f\u062e\u0648\u0644...';

    try {
      if (authMode === 'register') {
        const registerResponse = await fetch(`${apiBase}/api/auth/register`, {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({email, password, name: displayName})
        });

        const registerData = await registerResponse.json();

        if (!registerResponse.ok) {
          throw new Error(registerData.detail || '\u062a\u0639\u0630\u0631 \u0625\u0646\u0634\u0627\u0621 \u0627\u0644\u062d\u0633\u0627\u0628.');
        }
      }

      const loginResponse = await fetch(`${apiBase}/api/auth/login`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({email, password})
      });

      const loginData = await loginResponse.json();

      if (!loginResponse.ok) {
        throw new Error(loginData.detail || '\u062a\u0639\u0630\u0631 \u062a\u0633\u062c\u064a\u0644 \u0627\u0644\u062f\u062e\u0648\u0644.');
      }

      localStorage.setItem('risaala-token', loginData.access_token);
      localStorage.setItem(
        'risaala-user',
        JSON.stringify({
          identifier: loginData.email || email,
          name: loginData.name || displayName
        })
      );

      $('#login-password').value = '';
      location.href = 'account.html';

    } catch (error) {
      const messages = {
        'Email is already registered.': '\u0627\u0644\u0628\u0631\u064a\u062f \u0627\u0644\u0625\u0644\u0643\u062a\u0631\u0648\u0646\u064a \u0645\u0633\u062c\u0644 \u0645\u0633\u0628\u0642\u064b\u0627.',
        'Invalid email or password.': '\u0627\u0644\u0628\u0631\u064a\u062f \u0627\u0644\u0625\u0644\u0643\u062a\u0631\u0648\u0646\u064a \u0623\u0648 \u0643\u0644\u0645\u0629 \u0627\u0644\u0645\u0631\u0648\u0631 \u063a\u064a\u0631 \u0635\u062d\u064a\u062d\u0629.',
        'Password must be at least 8 characters.': '\u0643\u0644\u0645\u0629 \u0627\u0644\u0645\u0631\u0648\u0631 \u064a\u062c\u0628 \u0623\u0646 \u062a\u062a\u0643\u0648\u0646 \u0645\u0646 8 \u0623\u062d\u0631\u0641 \u0639\u0644\u0649 \u0627\u0644\u0623\u0642\u0644.'
      };

      feedback.textContent =
        messages[error.message] ||
        error.message ||
        '\u062d\u062f\u062b \u062e\u0637\u0623 \u0641\u064a \u0627\u0644\u0627\u062a\u0635\u0627\u0644 \u0628\u0627\u0644\u062e\u0627\u062f\u0645.';
    } finally {
      submit.disabled = false;
    }
  });

  const user = (() => {
    try {
      return JSON.parse(localStorage.getItem('risaala-user'));
    } catch {
      return null;
    }
  })();

  const token = localStorage.getItem('risaala-token');

  if (user && token && $('#account-name')) {
    $('#account-name').textContent =
      user.name ||
      (user.identifier.includes('@')
        ? user.identifier.split('@')[0]
        : '\u0639\u0636\u0648 \u0631\u0650\u0633\u0627\u0644\u0629');

    $('#account-identifier').textContent = user.identifier;
    $('#account-login-link').hidden = true;
    $('#logout-button').hidden = false;
  }

  $('#logout-button')?.addEventListener('click', () => {
    localStorage.removeItem('risaala-user');
    localStorage.removeItem('risaala-token');
    location.reload();
  });

  const settingsLang = $('#settings-language');
  if (settingsLang) settingsLang.value = chosen();
  const theme = localStorage.getItem('risaala-theme') || 'light';
  document.body.classList.toggle('dark-theme', theme === 'dark');
  const themeRadio=$(`input[name="theme"][value="${theme}"]`); if(themeRadio) themeRadio.checked=true;
  const voiceToggle = $('#voice-toggle'); if (voiceToggle) voiceToggle.checked = localStorage.getItem('risaala-voice') !== 'off';
  const motionToggle = $('#motion-toggle'); if (motionToggle) motionToggle.checked = localStorage.getItem('risaala-reduced-motion') === 'on';
  $('#settings-form')?.addEventListener('submit', e => {
    e.preventDefault();
    const selectedTheme = $('input[name="theme"]:checked')?.value || 'light';
    localStorage.setItem('risaala-theme', selectedTheme); document.body.classList.toggle('dark-theme', selectedTheme === 'dark');
    localStorage.setItem('risaala-voice', voiceToggle?.checked ? 'on' : 'off');
    localStorage.setItem('risaala-reduced-motion', motionToggle?.checked ? 'on' : 'off');
    document.documentElement.classList.toggle('reduce-motion', Boolean(motionToggle?.checked));
    const feedback = $('#settings-feedback'); if (feedback) feedback.textContent = 'تم حفظ التغييرات على هذا الجهاز.';
  });
  if (localStorage.getItem('risaala-reduced-motion') === 'on') document.documentElement.classList.add('reduce-motion');
})();

document.addEventListener('DOMContentLoaded', function() {
    const mapContainer = document.getElementById('gis-map');
    if (!mapContainer || typeof L === 'undefined' || !window.JOURNEY_DATA) return;

    window.JOURNEY_DATA.sort((a, b) => a.num - b.num);

    const map = L.map('gis-map').setView([23.8859, 39.1925], 6);

    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        attribution: 'Tiles &copy; Esri',
        maxZoom: 18
    }).addTo(map);

    const FullscreenControl = L.Control.extend({
        options: { position: 'topleft' },
        onAdd: function(map) {
            const btn = L.DomUtil.create('a', 'leaflet-control-fullscreen');
            btn.innerHTML = '⛶'; btn.title = "ملء الشاشة";
            btn.onclick = function(e) { e.preventDefault(); mapContainer.classList.toggle('fullscreen-map'); setTimeout(() => map.invalidateSize(), 300); };
            return btn;
        }
    });
    map.addControl(new FullscreenControl());

    const eventList = document.querySelector('.event-list');
    let markers = [];
    let sidebarBtns = [];
    let currentLine = null;
    let prevCoords = null;

    function renderEvents(filterCategory) {
        // Clear existing map markers, paths, and sidebar
        markers.forEach(m => map.removeLayer(m));
        markers = [];
        sidebarBtns = [];
        if (eventList) eventList.innerHTML = '';
        if (currentLine) map.removeLayer(currentLine);
        prevCoords = null;

        const groups = {};

        // 1. Group the events based on the selected filter
        window.JOURNEY_DATA.forEach(event => {
            // Battles filter logic
            const isBattle = event.title.match(/(غزوة|معركة|فتح|حصار|سرية)/);
            if (filterCategory === 'battles' && !isBattle) return;

            // Determine Group Key and Title
            let groupKey, groupTitle;
            if (filterCategory === 'location') {
                groupKey = event.location;
                groupTitle = `📍 ${event.location}`;
            } else {
                // 'timeline', 'all', or 'battles' standard eras
                if (event.num <= 32) { groupKey = 'makkah'; groupTitle = 'العهد المكي'; }
                else if (event.num <= 48) { groupKey = 'madinah'; groupTitle = 'العهد المدني'; }
                else { groupKey = 'caliphs'; groupTitle = 'عهد الخلفاء الراشدين'; }
            }

            if (!groups[groupKey]) {
                groups[groupKey] = { title: groupTitle, events: [] };
            }

            // Create Map Marker
            const customIcon = L.divIcon({
                className: 'custom-map-pin',
                html: `<div style="background:var(--ink); color:white; width:28px; height:28px; border-radius:50%; display:flex; align-items:center; justify-content:center; border:2px solid var(--gold); font-weight:bold; box-shadow:0 4px 8px rgba(0,0,0,0.3); font-size:12px;">${event.num}</div>`,
                iconSize: [28, 28], iconAnchor: [14, 14]
            });

            const marker = L.marker([event.lat, event.lng], { icon: customIcon }).addTo(map);
            markers.push(marker);

            const popupContent = `
                <div class="popup-title">${event.num}. ${event.title}</div>
                <div class="popup-meta"><span>📍 ${event.location}</span><span>📅 ${event.date}</span></div>
                <div class="popup-summary">${event.summary}</div>
                <a href="${event.url}" class="popup-btn">انتقل إلى التفاصيل ←</a>
            `;
            marker.bindPopup(popupContent);

            groups[groupKey].events.push({ event, marker });
        });

        // 2. Build the Sidebar Accordions
        if (eventList) {
            for (const [key, group] of Object.entries(groups)) {
                if (group.events.length === 0) continue;

                const detailsEl = document.createElement('details');
                detailsEl.className = 'sidebar-group';
                
                // Keep the first group open by default for a clean, uncluttered look
                if (Object.keys(groups)[0] === key || filterCategory === 'location') detailsEl.open = true;

                const summaryEl = document.createElement('summary');
                summaryEl.innerText = group.title;
                detailsEl.appendChild(summaryEl);

                const contentDiv = document.createElement('div');
                contentDiv.className = 'group-content';

                group.events.forEach(item => {
                    const { event, marker } = item;
                    const btn = document.createElement('button');
                    btn.className = 'event-row';
                    btn.innerHTML = `<span class="event-icon" style="font-size:16px;">${event.icon}</span><span style="text-align:right;"><strong>${event.num}. ${event.title}</strong><small>${event.location} · ${event.date}</small></span><span style="color:var(--gold);">‹</span>`;
                    
                    const triggerInteraction = () => {
                        sidebarBtns.forEach(el => el.classList.remove('selected'));
                        btn.classList.add('selected');

                        // Update Info Card
                        const titleEl = document.getElementById('event-title');
                        const copyEl = document.getElementById('event-copy');
                        const linkEl = document.getElementById('station-page-link');
                        const metaEl = document.querySelector('.event-meta');

                        if(titleEl) titleEl.innerText = `${event.title}`;
                        if(copyEl) copyEl.innerText = event.summary;
                        if(linkEl) { linkEl.href = event.url; linkEl.innerText = "انتقل إلى صفحة الحدث ←"; }
                        if(metaEl) metaEl.innerHTML = `<span>⌖ ${event.location}</span><span>◷ ${event.date}</span><span>📚 موثق من المصادر</span>`;

                        // Animated Line Logic
                        const currCoords = [event.lat, event.lng];
                        if (prevCoords && (prevCoords[0] !== currCoords[0] || prevCoords[1] !== currCoords[1])) {
                            if (currentLine) map.removeLayer(currentLine);
                            currentLine = L.polyline([prevCoords, currCoords], { color: '#e4d4a5', weight: 4, className: 'animated-route' }).addTo(map);
                        }
                        prevCoords = currCoords;

                        map.flyTo(currCoords, 10, { duration: 1.5 });
                        marker.openPopup();
                    };

                    btn.addEventListener('click', triggerInteraction);
                    marker.on('click', triggerInteraction);
                    contentDiv.appendChild(btn);
                    sidebarBtns.push(btn);
                });

                detailsEl.appendChild(contentDiv);
                eventList.appendChild(detailsEl);
            }
        }
    }

    // Initialize with all events
    renderEvents('all');

    // Filter Buttons Logic
    document.querySelectorAll('.filter-chip').forEach(chip => {
        chip.addEventListener('click', (e) => {
            document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
            e.target.classList.add('active');
            renderEvents(e.target.dataset.filter);
        });
    });
});

document.addEventListener('DOMContentLoaded', function() {
    if (!window.JOURNEY_DATA) return;
    
    // Check if we are on the station page by looking for the URL param
    const urlParams = new URLSearchParams(window.location.search);
    const eventId = urlParams.get('event');
    if (!eventId) return;

    // Keep the stations in chronological order so previous/next follow the sequence
    window.JOURNEY_DATA.sort((a, b) => a.num - b.num);

    // Find the event in the database (the URL param may hold the id or the number)
    const eventIndex = window.JOURNEY_DATA.findIndex(e => String(e.id) === eventId || String(e.num) === eventId);
    const eventData = window.JOURNEY_DATA[eventIndex];
    if (eventData) {
        // Update DOM elements dynamically
        const titleEl = document.getElementById('station-title');
        const subtitleEl = document.getElementById('station-subtitle');
        const heroSec = document.getElementById('station-hero-section');
        const locEl = document.getElementById('station-location');
        const periodEl = document.getElementById('station-period');
        const copyEl = document.getElementById('station-copy');
        const photoEl = document.querySelector('.station-photo');
        const eventHeadingEl = document.getElementById('station-event-heading');

        if (titleEl) titleEl.textContent = eventData.title;
        if (subtitleEl) subtitleEl.textContent = eventData.location;
        if (eventHeadingEl) eventHeadingEl.textContent = `${eventData.title} · ${eventData.location}`;
        if (locEl) locEl.textContent = eventData.location;
        if (periodEl) periodEl.textContent = eventData.date;
        if (copyEl) copyEl.textContent = eventData.summary;
        if (photoEl) photoEl.src = eventData.image; // Updates the body image
        
        // Update the top banner background with the real image dynamically
        if (heroSec) {
            heroSec.style.backgroundImage = `linear-gradient(110deg, #102945ee, #1029459c), url('${eventData.image}')`;
            heroSec.style.backgroundPosition = 'center';
            heroSec.style.backgroundSize = 'cover';
        }

        // Pagination: link to the neighbouring stations in numerical order
        const setStationLink = (el, target, label) => {
            if (!el) return;
            if (!target) { el.style.visibility = 'hidden'; return; }
            el.href = target.url;
            el.textContent = label(target);
            el.style.visibility = 'visible';
        };
        setStationLink(document.getElementById('prev-station'), window.JOURNEY_DATA[eventIndex - 1], t => `← السابق: ${t.title}`);
        setStationLink(document.getElementById('next-station'), window.JOURNEY_DATA[eventIndex + 1], t => `التالي: ${t.title} →`);
    }
});
