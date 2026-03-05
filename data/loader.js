// Wine List - Data Loader
// Runtime normalization for catalog/trainer compatibility

(function () {
    'use strict';

    window.allWineItems = []; // raw wine records
    window.allWineCards = []; // normalized cards used by UI
    window.previousWineItems = [];

    // Backward compatibility aliases
    window.allFoodItems = [];
    window.previousFoodItems = [];

    window.wineDataReady = false;
    window.foodDataReady = false;

    function slugify(input) {
        return String(input || '')
            .toLowerCase()
            .normalize('NFKD')
            .replace(/[^a-z0-9]+/g, '-')
            .replace(/^-+|-+$/g, '')
            .replace(/-{2,}/g, '-');
    }

    function compactText(text, maxLen) {
        if (!text) return null;
        const value = String(text).trim();
        if (!value) return null;
        if (value.length <= maxLen) return value;
        return value.slice(0, maxLen - 1).trim() + '...';
    }

    function normalizeCategoryValue(value) {
        const v = String(value || '').trim();
        if (!v) return null;
        const normalized = v
            .normalize('NFKD')
            .replace(/[\u0300-\u036f]/g, '')
            .toLowerCase()
            .replace(/\s+/g, ' ')
            .trim();

        const map = {
            'rose': 'rose',
            'rose wine': 'rose',
            'pink': 'rose',
            'red': 'red',
            'white': 'white',
            'white wine': 'white',
            'chardonnay': 'white',
            'viognier': 'white',
            'moscato': 'white',
            'sweet white': 'white',
            'yellow': 'white',
            'straw yellow with greenish hues': 'white',
            'pale gold': 'white',
            'pale in color': 'white',
            'gelb': 'white',
            'sparkling wine': 'sparkling',
            'sparkling white': 'sparkling',
            'sparkling': 'sparkling',
            'champagne': 'sparkling',
            'brut': 'sparkling',
            'port': 'port',
            'tawny port': 'port',
            'madeira': 'port',
            'amber, golden tawny': 'port',
            'dry': 'white',
            'null': ''
        };

        return map[normalized] || normalized;
    }

    function normalizeWineRecord(raw, index) {
        const vintage = raw.vintage || 'nv';
        const baseId = slugify((raw.wine_name || 'wine') + '-' + vintage);
        const id = baseId || 'wine-' + index;

        const imagePath = raw.image
            ? ('data/categories/images/' + String(raw.image).replace(/^\/+/, ''))
            : null;

        const baseCategory =
            normalizeCategoryValue(raw.wine_type) ||
            normalizeCategoryValue(raw.wine_color) ||
            normalizeCategoryValue(raw.country) ||
            'other';

        const sweetness = detectSweetness(raw);
        const category = getRuntimeCategory(baseCategory, sweetness);

        const wineMeta = {
            wineName: raw.wine_name || null,
            producer: raw.producer || null,
            country: raw.country || null,
            region: raw.region || null,
            subregion: raw.subregion || null,
            appellation: raw.appellation || null,
            vintage: raw.vintage || null,
            wineType: raw.wine_type || null,
            wineColor: raw.wine_color || null,
            grapeVarieties: Array.isArray(raw.grape_varieties) ? raw.grape_varieties : [],
            alcoholAbv: raw.alcohol_abv || null,
            residualSugar: raw.residual_sugar || null,
            acidity: raw.acidity || null,
            ph: raw.ph || null,
            soil: raw.soil || null,
            vineyard: raw.vineyard || null,
            harvest: raw.harvest || null,
            vinification: raw.vinification || null,
            aging: raw.aging || null,
            tastingNotes: raw.tasting_notes || null,
            aroma: raw.aroma || null,
            palate: raw.palate || null,
            finish: raw.finish || null,
            foodPairing: raw.food_pairing || null,
            servingTemperature: raw.serving_temperature || null,
            volume: raw.volume || null,
            closure: raw.closure || null,
            certifications: Array.isArray(raw.certifications) ? raw.certifications : [],
            awards: Array.isArray(raw.awards) ? raw.awards : [],
            importer: raw.importer || null,
            distributor: raw.distributor || null,
            website: raw.website || null,
            allFacts: raw.all_facts || null,
            missingFields: Array.isArray(raw.missing_fields) ? raw.missing_fields : [],
            sweetness: sweetness,
            isSweet: sweetness === 'sweet',
            styleCategory: category
        };

        return {
            id,
            name: raw.wine_name || 'Unnamed Wine',
            subtitle: raw.producer || '',
            category,
            description: raw.tasting_notes || compactText(raw.all_facts, 220) || null,
            image: imagePath,
            tags: [],
            wineMeta,
            source: raw
        };
    }

    function getRuntimeCategory(baseCategory, sweetness) {
        if (baseCategory === 'port') return 'port';
        if (sweetness === 'sweet') return 'dessert wine';
        return baseCategory || 'other';
    }

    function parseResidualSugar(value) {
        if (!value) return null;
        const text = String(value).toLowerCase().replace(',', '.');
        const match = text.match(/(\d+(\.\d+)?)/);
        if (!match) return null;
        return Number(match[1]);
    }

    function hasSweetKeyword(raw) {
        const text = [
            raw.wine_name,
            raw.wine_type,
            raw.tasting_notes,
            raw.all_facts
        ].filter(Boolean).join(' ').toLowerCase();

        const sweetWords = [
            'sweet wine',
            'dessert wine',
            'puttonyos',
            'tokaji',
            'moscato',
            'port',
            'madeira',
            'late harvest',
            'ice wine',
            'vin santo',
            'sauternes'
        ];
        function escapeRe(str) {
            return String(str).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        }

        return sweetWords.some(function (w) {
            const re = new RegExp('\\b' + escapeRe(w) + '\\b', 'i');
            return re.test(text);
        });
    }

    function detectSweetness(raw) {
        const sugar = parseResidualSugar(raw.residual_sugar);
        if (sugar !== null) {
            if (sugar >= 45) return 'sweet';
            if (sugar >= 12) return 'off-dry';
            return 'dry';
        }

        if (hasSweetKeyword(raw)) return 'sweet';
        return 'unknown';
    }

    function emitDataLoaded() {
        window.wineDataReady = true;
        window.foodDataReady = true;
        window.dispatchEvent(new CustomEvent('wineLoaded'));
        window.dispatchEvent(new CustomEvent('foodLoaded'));
    }

    function finalize(rawItems) {
        window.allWineItems = Array.isArray(rawItems) ? rawItems : [];
        window.allWineCards = window.allWineItems.map(normalizeWineRecord);
        window.previousWineItems = [];

        // Backward compatibility aliases
        window.allFoodItems = window.allWineCards;
        window.previousFoodItems = window.previousWineItems;

        emitDataLoaded();
    }

    function failSafe(error) {
        console.error('Failed to load wines-list.json', error);
        finalize([]);
    }

    window.registerFoodCategory = function (data) {
        if (!Array.isArray(data)) return;
        window.allWineCards = window.allWineCards.concat(data);
        window.allFoodItems = window.allWineCards;
        emitDataLoaded();
    };

    window.registerPreviousFoodCategory = function (data) {
        if (Array.isArray(data)) {
            window.previousWineItems = window.previousWineItems.concat(data);
            window.previousFoodItems = window.previousWineItems;
        }
        emitDataLoaded();
    };

    function loadFileProtocolFallback() {
        // file:// cannot fetch local JSON due browser CORS/security rules.
        // Fallback uses a prebuilt JS payload with raw wine data.
        window.registerWineRawData = function (data) {
            finalize(data);
        };
        var script = document.createElement('script');
        script.src = 'data/categories/wines-runtime.js';
        script.async = false;
        script.onerror = function () {
            console.error('Failed to load wines-runtime.js fallback');
            failSafe(new Error('file-protocol fallback load failed'));
        };
        document.head.appendChild(script);
    }

    if (window.location && window.location.protocol === 'file:') {
        console.warn('Running via file://. Using wines-runtime.js fallback. For full support use http://localhost:8080');
        loadFileProtocolFallback();
    } else {
        fetch('data/categories/wines-list.json', { cache: 'no-cache' })
            .then(function (response) {
                if (!response.ok) {
                    throw new Error('HTTP ' + response.status);
                }
                return response.json();
            })
            .then(finalize)
            .catch(failSafe);
    }
})();
