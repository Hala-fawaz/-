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

        if (!station.image) {
            document.querySelector('.station-photo')?.remove();
            const hero = document.getElementById('station-hero-section');
            if (hero) {
                hero.style.backgroundImage = '';
                hero.classList.add('no-image');
            }
        }
    }
});
