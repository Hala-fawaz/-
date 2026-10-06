/*
  Page enhancements kept apart from script.js so its logic and wiring stay untouched:
  - map page: quick search over the stations sidebar
  - station page: full historical text, source excerpt, and image-free stations
  Load this file after script.js.
*/
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
