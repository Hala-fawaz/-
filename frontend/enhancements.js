/*
  Page enhancements kept apart from script.js so its logic and wiring stay untouched:
  - map page: quick search over the stations sidebar
  - station page: full historical text, source excerpt, and image-free stations
  - all pages: translation of content that is rendered after the page loads
  Load this file after script.js.
*/

/*
  Dynamic translation.
  script.js translates the text that is on the page when it loads, through the backend
  /api/translate-batch endpoint. Station titles, histories, the sidebar list, map popups
  and other content are rendered later from data.js, so they are sent to the same
  endpoint here as soon as they appear. Nothing needs a per-string key: any Arabic text
  added to the page is picked up automatically.
*/
(() => {
    const language = localStorage.getItem('risaala-language') || 'ar';
    if (language === 'ar' || !document.body) return;

    const apiBase = window.RISAALA_CONFIG?.apiBaseUrl || 'http://127.0.0.1:8000';
    const ARABIC = /[؀-ۿ]/;
    const SKIP = 'script,style,select,textarea,.notranslate,[aria-hidden="true"],#language-status';
    // Letters used by Persian, Urdu, Pashto and similar languages but not by Arabic:
    // text containing them has already been translated into an Arabic-script language
    const NON_ARABIC_LETTERS = /[پچژگکیےٹڈڑںھہږړڅځګڼٲ]/;

    const cacheKey = `risaala-translations-${language}`;
    let cache = {};
    try { cache = JSON.parse(sessionStorage.getItem(cacheKey)) || {}; } catch { cache = {}; }
    const saveCache = () => { try { sessionStorage.setItem(cacheKey, JSON.stringify(cache)); } catch { /* storage full or blocked */ } };

    const pending = new Set(); // text nodes waiting for a translation
    const produced = new Set(Object.values(cache)); // translated texts, never sent back for translation
    let timer = null;

    const wanted = node => {
        const value = node.nodeValue.trim();
        if (!value || !ARABIC.test(value) || NON_ARABIC_LETTERS.test(value) || produced.has(value)) return false;
        const parent = node.parentElement;
        return Boolean(parent) && !parent.closest(SKIP);
    };
    // Short labels are built from parts ("title · place", "icon date", "next: title").
    // Each part is translated on its own: the service handles parts reliably, and place
    // names and dates repeat across stations, so most are answered from the cache.
    const plan = source => {
        if (source.length > 120) return [{ lead: '', core: source, trail: '' }];
        return source.split(/(\s·\s|:\s)/).map((piece, index) => {
            if (index % 2) return { lead: piece, core: '', trail: '' }; // the separator itself
            const [, lead, core, trail] = piece.match(/^([^\p{L}\p{N}]*)([\s\S]*?)([^\p{L}\p{N}]*)$/u);
            // "624م" is sent as "624 م", which the service translates as a year
            return { lead, core: core.replace(/(\d)م(?![\u0600-\u06FF])/g, '$1 م'), trail };
        });
    };
    const compose = source => plan(source)
        .map(part => part.lead + (ARABIC.test(part.core) ? (cache[part.core] || part.core) : part.core) + part.trail)
        .join('');
    const apply = (node, source) => {
        if (!node.isConnected || node.nodeValue.trim() !== source) return;
        const translated = compose(source);
        if (translated === source) return;
        produced.add(translated.trim());
        node.nodeValue = node.nodeValue.replace(source, translated);
    };

    const flush = async () => {
        timer = null;
        const nodes = [...pending].filter(node => node.isConnected && wanted(node));
        pending.clear();
        const sources = new Map(nodes.map(node => [node, node.nodeValue.trim()]));
        const missing = [...new Set([...sources.values()].flatMap(source =>
            plan(source).map(part => part.core).filter(core => ARABIC.test(core) && !cache[core])))];

        // Returns the texts the service sent back unchanged, so they can be tried again
        const translate = async (texts, size) => {
            const unchanged = [];
            for (let start = 0; start < texts.length; start += size) {
                const batch = texts.slice(start, start + size);
                const response = await fetch(`${apiBase}/api/translate-batch`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ texts: batch, source_language: 'ar', target_language: language })
                });
                if (!response.ok) throw new Error(`Translation request failed (${response.status})`);
                const translations = (await response.json()).translations || [];
                batch.forEach((text, index) => {
                    const translated = (translations[index] || '').trim();
                    if (!translated || translated === text) { unchanged.push(text); return; }
                    cache[text] = translated;
                    produced.add(translated);
                });
            }
            return unchanged;
        };

        try {
            const unchanged = await translate(missing, 40);
            // The service sometimes skips items in a large batch; retry those in small ones
            if (unchanged.length) await translate(unchanged, 8);
        } catch (error) {
            console.error(error); // the Arabic text stays in place if the service is unreachable
        }
        saveCache();
        nodes.forEach(node => apply(node, sources.get(node)));
    };

    const queue = root => {
        if (root.nodeType === Node.TEXT_NODE) {
            if (wanted(root)) pending.add(root);
        } else if (root.nodeType === Node.ELEMENT_NODE && !root.closest(SKIP)) {
            const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
            while (walker.nextNode()) if (wanted(walker.currentNode)) pending.add(walker.currentNode);
        }
        if (pending.size && !timer) timer = setTimeout(flush, 80);
    };

    // Content can arrive as new nodes or as new text written into an existing node
    new MutationObserver(mutations => {
        mutations.forEach(mutation => {
            if (mutation.type === 'characterData') queue(mutation.target);
            else mutation.addedNodes.forEach(queue);
        });
    }).observe(document.body, { childList: true, characterData: true, subtree: true });
})();

document.addEventListener('DOMContentLoaded', () => {
    // Fold Arabic so a search matches with or without diacritics and letter variants
    const fold = text => text.toLocaleLowerCase()
        .replace(/[ً-ْٰـ]/g, '')
        .replace(/[أإآٱ]/g, 'ا').replace(/ى/g, 'ي').replace(/ة/g, 'ه')
        .replace(/\s+/g, ' ').trim();

    // ---- Map page: sidebar quick search ----
    const eventList = document.querySelector('.event-sidebar .event-list');
    const searchInput = document.getElementById('event-search');
    if (eventList && searchInput) {
        const searchEmpty = document.getElementById('event-search-empty');
        const countEl = document.getElementById('event-count');
        const countLabel = n => n === 1 ? 'محطة واحدة' : n === 2 ? 'محطتان' : n >= 3 && n <= 10 ? `${n} محطات` : `${n} محطة`;

        const applySearch = () => {
            const query = fold(searchInput.value);
            let visible = 0;
            eventList.querySelectorAll('.sidebar-group').forEach(group => {
                let groupVisible = 0;
                group.querySelectorAll('.event-row').forEach(row => {
                    const match = !query || fold(row.textContent).includes(query);
                    row.hidden = !match;
                    if (match) groupVisible++;
                });
                group.hidden = groupVisible === 0;
                // Open matching groups while searching, then restore how they were
                if (query) {
                    if (group.dataset.wasOpen === undefined) group.dataset.wasOpen = String(group.open);
                    group.open = true;
                } else if (group.dataset.wasOpen !== undefined) {
                    group.open = group.dataset.wasOpen === 'true';
                    delete group.dataset.wasOpen;
                }
                visible += groupVisible;
            });
            if (countEl) countEl.textContent = countLabel(visible);
            if (searchEmpty) searchEmpty.hidden = visible > 0;
        };

        searchInput.addEventListener('input', applySearch);
        // script.js rebuilds the list when a filter chip is clicked; re-apply the search then
        new MutationObserver(applySearch).observe(eventList, { childList: true });
        applySearch();
    }

    // ---- Station page: history, source excerpt, image-free stations ----
    const copyEl = document.getElementById('station-copy');
    const eventId = new URLSearchParams(location.search).get('event');
    const station = copyEl && eventId && (window.JOURNEY_DATA || [])
        .find(e => String(e.id) === eventId || String(e.num) === eventId);
    if (station) {
        if (station.history) copyEl.textContent = station.history;

        // Show this station's own place and date in the hero tag and the meta line
        const tagEl = document.querySelector('.station-hero .tag');
        if (tagEl) tagEl.textContent = `محطة ${station.num} · ${station.location}`;
        const metaEl = document.querySelector('#tab-history .event-meta');
        // In other languages script.js later writes the translated date of the last map
        // event into the first ".event-meta" on the page. Give it a hidden one to write
        // into, so this station's own date stays in place.
        if (metaEl && !document.querySelector('.event-meta-decoy')) {
            const decoy = document.createElement('div');
            decoy.className = 'event-meta event-meta-decoy notranslate';
            decoy.hidden = true;
            decoy.setAttribute('aria-hidden', 'true');
            decoy.innerHTML = '<span></span><span></span>';
            document.querySelector('main')?.prepend(decoy);
        }
        if (metaEl) metaEl.innerHTML = `<span>⌖ ${station.location}</span><span>◷ ${station.date}</span><span>📚 موثق من المصادر</span>`;

        // Verbatim passage from the source book, with its citation
        if (station.details && !document.querySelector('.station-source-quote')) {
            const holder = document.createElement('div');
            holder.innerHTML = station.details;
            const quote = holder.querySelector('blockquote');
            if (quote) {
                quote.classList.add('station-source-quote');
                const label = document.createElement('strong');
                label.textContent = 'مقتطف من المصدر';
                quote.prepend(label);
                copyEl.after(quote);
            }
        }

        const hero = document.getElementById('station-hero-section');
        if (!station.image) {
            document.querySelector('.station-photo')?.remove();
            if (hero) {
                hero.style.backgroundImage = '';
                hero.classList.add('no-image');
            }
        } else if (hero) {
            // Keep the picture clear: darken only the side the title sits on
            const titleSide = document.documentElement.dir === 'ltr' ? '90deg' : '270deg';
            hero.style.backgroundImage = `linear-gradient(${titleSide}, #102945e6 0%, #102945b3 38%, #10294533 100%), url('${station.image}')`;
        }
    }
    // ---- Home page: play the hero animation once, then settle on a still frame ----
    const heroMedia = document.querySelector('.hero-media');
    const lessMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
        || document.documentElement.classList.contains('reduce-motion')
        || Boolean(navigator.connection && navigator.connection.saveData);
    if (heroMedia && !lessMotion) {
        const DURATION = 6000; // length of one pass of the GIF, in milliseconds
        const anim = new Image();
        anim.className = 'hero-anim';
        anim.alt = '';
        // The still image stays visible until the animation has fully downloaded
        anim.addEventListener('load', () => {
            heroMedia.append(anim);
            requestAnimationFrame(() => anim.classList.add('playing'));
            setTimeout(() => {
                // Copy the frame on screen to the canvas, then drop the GIF so it cannot loop
                const frame = heroMedia.querySelector('.hero-frame');
                if (frame && anim.naturalWidth) {
                    frame.width = anim.naturalWidth;
                    frame.height = anim.naturalHeight;
                    frame.getContext('2d').drawImage(anim, 0, 0);
                    frame.hidden = false;
                }
                anim.remove();
                anim.removeAttribute('src');
            }, DURATION - 120);
        }, { once: true });
        anim.src = 'assets/earth-orbit-clean.gif';
    }
});
