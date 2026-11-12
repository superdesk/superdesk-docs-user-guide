// Pure parsing for the screenshot manifests: free-text steps, crop, highlight,
// route and viewport. No Playwright import here, so `node --test` can exercise it.
//
// Parsed targets are plain objects. capture.mjs turns them into Playwright locators:
//   {kind: 'css', css, hasText?, nth?}       page.locator(css)
//   {kind: 'bare', value}                    test id, then CSS, then text
//   {kind: 'role', role, name}               getByRole(role, {name})
//   {kind: 'label', text, hint?}             button / tab / radio / link / text, first visible wins
//   {kind: 'phrase', text, hint?}            unquoted prose ("Slugline field"), best effort
//   {kind: 'alias', name}                    a known UI region, see ALIASES
//   {kind: 'prev'}                           the element the previous action touched
// Any target may carry `within: [target, ...]` (outermost first) and `scopePrev: true`.

export const VERBS = [
    'click', 'double-click', 'dblclick', 'tap', 'hover', 'move', 'wait', 'open', 'go', 'navigate',
    'select', 'choose', 'pick', 'type', 'enter', 'fill', 'change', 'set', 'press', 'check', 'tick',
    'uncheck', 'untick', 'turn', 'scroll', 'make sure', 'confirm', 'ensure', 'verify', 'keep',
    'leave', 'do', 'close', 'optionally', 'switch', 'reset',
];

const HTML_TAGS = new Set([
    'a', 'article', 'aside', 'button', 'div', 'figure', 'footer', 'form', 'h1', 'h2', 'h3', 'h4',
    'h5', 'h6', 'header', 'i', 'img', 'input', 'label', 'li', 'main', 'nav', 'ol', 'option', 'p',
    'section', 'select', 'span', 'svg', 'table', 'td', 'textarea', 'th', 'tr', 'ul',
]);

const KEY_NAMES = {
    escape: 'Escape', esc: 'Escape', enter: 'Enter', return: 'Enter', tab: 'Tab', space: 'Space',
    backspace: 'Backspace', delete: 'Delete', up: 'ArrowUp', down: 'ArrowDown', left: 'ArrowLeft',
    right: 'ArrowRight', arrowup: 'ArrowUp', arrowdown: 'ArrowDown', arrowleft: 'ArrowLeft',
    arrowright: 'ArrowRight', home: 'Home', end: 'End', pageup: 'PageUp', pagedown: 'PageDown',
};

const VIEW_SWITCHER_TOGGLE = '[data-test-id="monitoring-view"] button.dropdown__toggle[aria-label$=" View"]';

// Known UI regions that writers describe in prose. Keys are matched as substrings of the
// lower-cased phrase, longest first. `css` may be an array: the region is then the union.
export const ALIASES = {
    'open view switcher dropdown': {css: [
        VIEW_SWITCHER_TOGGLE,
        `.dropdown:has(> ${'button.dropdown__toggle[aria-label$=" View"]'}) > .dropdown__menu`,
    ]},
    'view switcher': {css: VIEW_SWITCHER_TOGGLE},
    'open popover': {css: '.sd-popup-positioner'},
    'popover': {css: '.sd-popup-positioner'},
    'open dropdown': {css: '.dropdown.open > .dropdown__menu, .dropdown__menu'},
    'dropdown menu': {css: '.dropdown.open > .dropdown__menu, .dropdown__menu'},
    'item row': {lastItem: true},
    'more actions': {css: '.monitoring__toolbar-container button.dropdown__toggle:has(i.icon-dots-vertical)'},
    'vertical dots': {css: '.monitoring__toolbar-container button.dropdown__toggle:has(i.icon-dots-vertical)'},
    'sort control': {css: '.monitoring__toolbar-container .sortbar-container'},
    'monitoring dropdown': {css: '.monitoring__toolbar-container .dropdown__toggle:has-text("Monitoring")'},
    'file type buttons': {css: '.monitoring__toolbar-container .button-list'},
    'picture file type': {css: '.monitoring__toolbar-container .toggle-button:has(i.filetype-icon-picture)'},
    'columns input': {css: '.monitoring__toolbar-container input[type="number"]'},
    'search box': {css: '#search-input'},
    'tab row': {css: '[role="tablist"]'},
    'filters icon': {css: '[data-test-id="filters-dropdown"]'},
    'create new item': {css: '[data-test-id="content-create"]'},
};

const NOUN_HINTS = [
    'button', 'buttons', 'tab', 'tabs', 'radio', 'switch', 'switches', 'field', 'input', 'icon',
    'link', 'menu', 'option', 'section', 'label', 'panel', 'box', 'tag', 'action', 'control', 'row',
    'item', 'card', 'header', 'checkbox',
];

const PH = (type, i) => `\u00ab${type}${i}\u00bb`;
const PH_RE = /\u00ab([SQRP])(\d+)\u00bb/g;

// ---------------------------------------------------------------------------
// Tokenizer
// ---------------------------------------------------------------------------

function isQuoteChar(ch) {
    return ch === '\'' || ch === '"' || ch === '\u2018' || ch === '\u201c';
}

function closingQuote(ch) {
    return {'\u2018': '\u2019', '\u201c': '\u201d'}[ch] ?? ch;
}

const QUOTE_OPEN_PREV = /[\s([{=:,/>]/;
const QUOTE_CLOSE_NEXT = /[\s)\]},.;:!?]/;

function readBracketRun(text, start) {
    let i = start;
    let out = '';

    while (text[i] === '[') {
        let quote = null;
        let j = i;

        for (; j < text.length; j++) {
            const ch = text[j];

            if (quote != null) {
                if (ch === quote) {
                    quote = null;
                }
            } else if (ch === '"' || ch === '\'') {
                quote = ch;
            } else if (ch === ']') {
                break;
            }
        }

        if (j >= text.length) {
            return null;
        }

        out += text.slice(i, j + 1);
        i = j + 1;

        // `[a="b"].class` or `[a="b"]:has(...)` stay glued to the run
        const tail = /^(?:[.#][A-Za-z_][\w-]*|:[\w-]+(?:\([^)]*\))?)*/.exec(text.slice(i));

        if (tail != null && tail[0].length > 0) {
            out += tail[0];
            i += tail[0].length;
        }
    }

    return {css: out, end: i};
}

const CSS_WORD_RE = /^([a-z][a-z0-9]*)?((?:[.#][A-Za-z_][\w-]*)+)((?:\[[^\]]*\])*)((?::[\w-]+(?:\([^)]*\))?)*)$/;
const CSS_WORD_EXCLUDE = new Set(['e.g', 'i.e', 'etc']);

export function looksLikeCssWord(word) {
    if (CSS_WORD_EXCLUDE.has(word)) {
        return false;
    }

    const m = CSS_WORD_RE.exec(word);

    if (m == null) {
        return false;
    }

    if (m[1] != null && !HTML_TAGS.has(m[1])) {
        return false;
    }

    // file names such as `send-publish-button.png` or `index.js`
    if (m[1] == null && word[0] === '.' && /^\.(png|jpe?g|json|js|mjs|ts|tsx|html|md)$/.test(word)) {
        return false;
    }

    return true;
}

/**
 * Replaces selectors, quoted strings and routes with placeholders so the
 * grammar can work on plain words. Returns {template, sel, quotes, routes, parens}.
 */
export function tokenize(input) {
    const sel = [];
    const quotes = [];
    const routes = [];
    const parens = [];
    let out = '';
    let i = 0;

    while (i < input.length) {
        const ch = input[i];
        const prev = i === 0 ? ' ' : input[i - 1];

        if (ch === '[' && /^\[\s*[\w-]+\s*(?:[~|^$*]?=|\])/.test(input.slice(i))) {
            const run = readBracketRun(input, i);

            if (run != null) {
                out += PH('S', sel.length);
                sel.push(run.css);
                i = run.end;
                continue;
            }
        }

        if (isQuoteChar(ch) && QUOTE_OPEN_PREV.test(prev)) {
            const close = closingQuote(ch);
            let j = i + 1;
            let found = -1;

            while (j < input.length) {
                const k = input.indexOf(close, j);

                if (k < 0) {
                    break;
                }

                const next = k + 1 >= input.length ? ' ' : input[k + 1];

                if (QUOTE_CLOSE_NEXT.test(next)) {
                    found = k;
                    break;
                }

                j = k + 1;
            }

            if (found > i) {
                out += PH('Q', quotes.length);
                quotes.push(input.slice(i + 1, found));
                i = found + 1;
                continue;
            }
        }

        out += ch;
        i++;
    }

    // routes: `#/x/y` or `/#/x/y`, optionally with a query string
    out = out.replace(/(^|[\s(])(\/?#\/[\w\-/.?=&%]*)/g, (m, lead, route) => {
        const clean = route.replace(/[.,;:]+$/, '');
        const rest = route.slice(clean.length);

        routes.push(clean);

        return `${lead}${PH('R', routes.length - 1)}${rest}`;
    });

    // bare CSS words: `button.sd-navbtn`, `.sd-grid-list`, `#search-input`
    out = out.replace(/(^|[\s(:])([a-z#.][^\s,;()]*[\w\]])(?=$|[\s,;:)])/g, (m, lead, word) => {
        if (!looksLikeCssWord(word)) {
            return m;
        }

        sel.push(word);

        return `${lead}${PH('S', sel.length - 1)}`;
    });

    // `the input with name="slugline"` -> input[name="slugline"]
    out = out.replace(
        /\b([a-z]+) with (aria-label|name|title|placeholder|id|type|role)\s*=?\s*\u00abQ(\d+)\u00bb/g,
        (m, tag, attr, qi) => {
            const value = quotes[Number(qi)].replace(/"/g, '\\"');
            const prefix = HTML_TAGS.has(tag) ? tag : '';

            sel.push(`${prefix}[${attr}="${value}"]`);

            return HTML_TAGS.has(tag)
                ? PH('S', sel.length - 1)
                : `${tag} ${PH('S', sel.length - 1)}`;
        },
    );

    // `X containing Y` -> X:has(Y)
    out = out.replace(/\u00abS(\d+)\u00bb containing \u00abS(\d+)\u00bb/g, (m, a, b) => {
        sel.push(`${sel[Number(a)]}:has(${sel[Number(b)]})`);

        return PH('S', sel.length - 1);
    });

    // adjacent selector runs are one descendant selector
    let merged = true;

    while (merged) {
        merged = false;
        out = out.replace(/\u00abS(\d+)\u00bb[ \t]+\u00abS(\d+)\u00bb/, (m, a, b) => {
            merged = true;
            sel.push(`${sel[Number(a)]} ${sel[Number(b)]}`);

            return PH('S', sel.length - 1);
        });
    }

    // prose parentheticals, innermost first
    let replaced = true;

    while (replaced) {
        replaced = false;
        out = out.replace(/\(([^()]*)\)/, (m, inner) => {
            replaced = true;
            parens.push(inner);

            return PH('P', parens.length - 1);
        });
    }

    return {template: out.replace(/\s+/g, ' ').trim(), sel, quotes, routes, parens};
}

function placeholders(text, type) {
    const result = [];

    for (const m of text.matchAll(PH_RE)) {
        if (m[1] === type) {
            result.push(Number(m[2]));
        }
    }

    return result;
}

function stripParens(text) {
    return text.replace(/\s*\u00abP\d+\u00bb/g, '').replace(/\s+/g, ' ').trim();
}

function parenSelectors(text, tok) {
    const result = [];

    for (const pi of placeholders(text, 'P')) {
        for (const si of placeholders(tok.parens[pi], 'S')) {
            result.push(si);
        }
    }

    return result;
}

/** Puts quoted strings and selectors back for log output. */
export function detokenize(text, tok) {
    return text.replace(PH_RE, (m, type, idx) => {
        const i = Number(idx);

        switch (type) {
        case 'S': return tok.sel[i];
        case 'Q': return `'${tok.quotes[i]}'`;
        case 'R': return tok.routes[i];
        case 'P': return `(${detokenize(tok.parens[i], tok)})`;
        default: return m;
        }
    });
}

// ---------------------------------------------------------------------------
// Clause splitting
// ---------------------------------------------------------------------------

const VERB_ALT = VERBS.map((v) => v.replace(/[-]/g, '\\-').replace(/ /g, '\\s+')).join('|');
const SPLIT_RE = new RegExp(
    `(?:,\\s*then\\s+|\\s+then\\s+|,\\s*and\\s+(?:then\\s+)?|\\s+and\\s+(?:then\\s+)?|,\\s+|;\\s+)(?=(?:${VERB_ALT})\\b)`,
    'i',
);

export function splitClauses(template) {
    return template.split(SPLIT_RE).map((s) => s.trim()).filter((s) => s.length > 0);
}

// ---------------------------------------------------------------------------
// Targets
// ---------------------------------------------------------------------------

const STOP_WORDS = new Set(['the', 'a', 'an', 'open', 'opened', 'visible', 'its', 'this', 'that', 'of', 'on']);

function phraseWords(text) {
    return text
        .replace(PH_RE, ' ')
        .replace(/[^A-Za-z0-9:/' -]/g, ' ')
        .split(/\s+/)
        .filter((w) => w.length > 0);
}

export function matchAlias(phrase) {
    const p = phrase.toLowerCase();
    const keys = Object.keys(ALIASES).sort((a, b) => b.length - a.length);

    for (const key of keys) {
        if (p.includes(key)) {
            return key;
        }
    }

    return null;
}

function hasNounHint(words) {
    const last = words[words.length - 1]?.toLowerCase();

    return last != null && NOUN_HINTS.includes(last);
}

function singular(word) {
    if (word == null) {
        return null;
    }

    if (word.endsWith('ches')) {
        return word.slice(0, -2);
    }

    if (word.endsWith('s') && word !== 'radio' && !word.endsWith('ss')) {
        return word.slice(0, -1);
    }

    return word;
}

/**
 * A target from unquoted prose: "the Slugline field", "Marked for me button".
 */
export function phraseTarget(text) {
    const alias = matchAlias(text);

    if (alias != null) {
        return {kind: 'alias', name: alias};
    }

    let words = phraseWords(text.replace(/\b(on|in|at|to|under|below|above) the (right|left|top|bottom)\b.*$/i, ''));

    while (words.length > 0 && STOP_WORDS.has(words[0].toLowerCase())) {
        words = words.slice(1);
    }

    let hint = null;

    if (hasNounHint(words)) {
        hint = singular(words[words.length - 1].toLowerCase());
        words = words.slice(0, -1);
    }

    const value = words.join(' ').trim();

    if (value.length === 0) {
        return null;
    }

    return {kind: 'phrase', text: value, hint};
}

function roleHintNear(text, qIndex) {
    const ph = PH('Q', qIndex);
    const re = new RegExp(`(?:\\b(button|tab|radio|link|option|switch|checkbox|menu item)\\s+${ph})|(?:${ph}\\s+(button|tab|radio|link|option|switch|checkbox|menu item)\\b)`, 'i');
    const m = re.exec(text);

    if (m == null) {
        return null;
    }

    const role = (m[1] ?? m[2]).toLowerCase();

    return role === 'menu item' ? 'menuitem' : role;
}

function ordinalBefore(text, si) {
    const ph = PH('S', si);
    const idx = text.indexOf(ph);
    const before = text.slice(0, idx);

    if (/\blast\b[^\u00ab]*$/i.test(before)) {
        return 'last';
    }

    if (/\bfirst\b[^\u00ab]*$/i.test(before)) {
        return 'first';
    }

    return null;
}

/**
 * Resolves the target of a click/hover/check style clause.
 * `text` is the clause with parentheticals still present.
 */
export function clauseTarget(text, tok) {
    let work = text;
    const leadScopes = [];
    const trailingScopes = [];
    let scopePrev = false;

    // leading scope: "In [x] click ..." / "In [x], click ..."
    const lead = /^in(?:side)?\s+\u00abS(\d+)\u00bb,?\s+/i.exec(work);

    if (lead != null) {
        leadScopes.push({kind: 'css', css: tok.sel[Number(lead[1])]});
        work = work.slice(lead[0].length);
    }

    if (/\b(its|inside that item|in that item|inside it|within it|of that item|inside that row)\b/i.test(work)) {
        scopePrev = true;
        work = work.replace(/\b(inside that item|in that item|inside it|within it|of that item|inside that row)\b/ig, '');
    }

    // inner/trailing scope: "... in [x]" / "... inside [x]"; a later one encloses an earlier one
    work = work.replace(/\s+(?:in|inside|within|from)\s+(?:the\s+)?\u00abS(\d+)\u00bb/ig, (m, si) => {
        trailingScopes.unshift({kind: 'css', css: tok.sel[Number(si)]});

        return '';
    });

    const within = [...leadScopes, ...trailingScopes];

    const main = stripParens(work);
    let target = null;

    const roleName = /role\s*=?\s*(\w+)\s+(?:and\s+)?name\s+\u00abQ(\d+)\u00bb/i.exec(main);

    if (roleName != null) {
        target = {kind: 'role', role: roleName[1].toLowerCase(), name: tok.quotes[Number(roleName[2])]};
    }

    if (target == null) {
        const sels = placeholders(main, 'S');
        const promoted = sels.length > 0 ? sels : parenSelectors(work, tok);

        if (promoted.length > 0) {
            const si = promoted[0];

            target = {kind: 'css', css: tok.sel[si]};

            const ord = ordinalBefore(main, si);

            if (ord != null) {
                target.nth = ord;
            }

            const textQ = /(?:with (?:the )?text|containing|labelled|labeled|named|with)\s+\u00abQ(\d+)\u00bb/i.exec(main);

            if (textQ != null) {
                target.hasText = tok.quotes[Number(textQ[1])];
            }
        }
    }

    if (target == null) {
        const qs = placeholders(main, 'Q');

        if (qs.length > 0) {
            const role = roleHintNear(main, qs[0]);
            const value = tok.quotes[qs[0]];

            if (role === 'switch') {
                target = {kind: 'label', text: value, hint: 'switch'};
            } else if (role != null) {
                target = {kind: 'role', role, name: value};
            } else {
                target = {kind: 'label', text: value};
            }
        }
    }

    if (target == null && /^\s*(?:\w+\s+)?(it|that|that item|this)\s*$/i.test(main)) {
        target = {kind: 'prev'};
        scopePrev = false;
    }

    if (target == null && within.length > 0) {
        target = within.pop();
    }

    if (target == null) {
        const words = main.replace(/^\s*\w+(\s+on)?\s+/, '');
        const phrase = phraseTarget(words);

        if (phrase != null) {
            target = phrase;
        }
    }

    if (target == null) {
        return null;
    }

    if (within.length > 0) {
        target.within = within;
    }

    if (scopePrev) {
        target.scopePrev = true;
    }

    return target;
}

// ---------------------------------------------------------------------------
// Clause grammar
// ---------------------------------------------------------------------------

function action(shape, fields) {
    return {shape, ...fields};
}

function waitAction(text, tok, state) {
    const main = stripParens(text);
    const sels = placeholders(main, 'S');
    const promoted = sels.length > 0 ? sels : parenSelectors(text, tok);
    const targets = [];
    const texts = [];

    const contains = /\u00abS(\d+)\u00bb\s+contains?\s+(?:at least one|an?|one|some)?\s*\u00abS(\d+)\u00bb/i.exec(main);

    if (contains != null) {
        targets.push({kind: 'css', css: `${tok.sel[Number(contains[1])]} ${tok.sel[Number(contains[2])]}`});
    } else {
        for (const si of promoted) {
            targets.push({kind: 'css', css: tok.sel[si]});
        }
    }

    const container = targets[0] ?? null;
    const firstSelPos = promoted.length > 0 ? main.indexOf(PH('S', promoted[0])) : -1;

    for (const qi of placeholders(main, 'Q')) {
        const qPos = main.indexOf(PH('Q', qi));
        const between = firstSelPos >= 0 && qPos > firstSelPos ? main.slice(firstSelPos, qPos) : '';
        const inside = container != null && qPos > firstSelPos && !/\s(and|or)\s/i.test(between);

        texts.push({text: tok.quotes[qi], inContainer: inside});
    }

    if (targets.length === 0 && texts.length === 0) {
        return action('wait-settle', {type: 'settle'});
    }

    return action('wait', {type: 'wait', targets, texts, state});
}

function parseSetPairs(text, tok) {
    const pairs = [];
    const re = /\b(date|time)\s*(\u00abS(\d+)\u00bb)?\s*to\s+(tomorrow|today|in \d+ days?|\u00abQ(\d+)\u00bb|[\d:/.-]+)/ig;

    for (const m of text.matchAll(re)) {
        const field = m[1].toLowerCase();
        const css = m[3] != null
            ? tok.sel[Number(m[3])]
            : `[data-test-id="${field === 'date' ? 'date-input' : 'time-input'}"]`;
        const value = m[5] != null ? tok.quotes[Number(m[5])] : m[4];

        pairs.push({field, css, value});
    }

    return pairs;
}

/**
 * Parses one clause (a template string from tokenize) into an action.
 * Returns an action object with `shape`; shape 'generic' means no known shape matched.
 */
export function parseClause(text, tok) {
    let clause = text.trim().replace(/[.;]+$/, '');
    let optional = false;

    const opt = /^(optionally|if possible|if needed)[,:]?\s+/i.exec(clause);

    if (opt != null) {
        optional = true;
        clause = clause.slice(opt[0].length);
    }

    // trailing purpose: "so its tooltip shows", "so no row is hovered"
    clause = clause.replace(/\s+so\s+(that\s+)?.*$/i, '').trim();

    const result = parseClauseInner(clause, tok);

    if (optional) {
        result.optional = true;
    }

    result.source = detokenize(clause, tok);

    return result;
}

const PROSE_LOCATION_RE = new RegExp(`^(?:in|on|inside|from)\\s+(?:the\\s+)?[^\\u00ab,]{1,60}?\\s+(?=(?:${VERB_ALT})\\b)`, 'i');

function parseClauseInner(input, tok) {
    // "in the second toolbar row click ..." names a location in prose only; the verb follows
    const prose = PROSE_LOCATION_RE.exec(input);
    const clause = prose != null ? input.slice(prose[0].length) : input;
    const fullMain = stripParens(clause);
    const leadScope = /^in(?:side)?\s+\u00abS(\d+)\u00bb,?\s+/i.exec(fullMain);
    const main = leadScope != null ? fullMain.slice(leadScope[0].length) : fullMain;
    const routes = placeholders(main, 'R');
    const quotes = placeholders(main, 'Q');

    // notes to the human operator, nothing to do
    if (/^(do not|don't|never|keep|leave|note|remember)\b/i.test(main)) {
        return action('note', {type: 'noop'});
    }

    if (routes.length > 0 && /^(open|go to|navigate to|visit|load|navigate)\b/i.test(main)) {
        return action('goto', {type: 'goto', route: tok.routes[routes[0]]});
    }

    if (/\bview switcher\b/i.test(main) && /\b(open|click|tap)\b/i.test(main)) {
        return action('open-view-switcher', {type: 'openViewSwitcher'});
    }

    if (/^select\s+(?:the\s+)?desk\b/i.test(main) && quotes.length > 0) {
        return action('select-desk', {type: 'selectDesk', name: tok.quotes[quotes[0]]});
    }

    const openItem = /^open\s+(?:item\s+|the item\s+|article\s+)?\u00abQ(\d+)\u00bb(.*)$/i.exec(main);

    const tailSaysEdit = openItem != null && (
        /\b(edit|editing|authoring)\b/i.test(openItem[2])
        || placeholders(openItem[2], 'Q').some((qi) => /^edit$/i.test(tok.quotes[qi]))
    );

    if (openItem != null && (tailSaysEdit || /^open\s+(item|article)\b/i.test(main))) {
        const desk = /\bdesk\s+\u00abQ(\d+)\u00bb/i.exec(openItem[2]);

        return action('open-item', {
            type: 'openItem',
            name: tok.quotes[Number(openItem[1])],
            desk: desk != null ? tok.quotes[Number(desk[1])] : null,
        });
    }

    if (/^open\s+(?:the\s+)?send\s*to\s*\/\s*publish\s+(?:panel|pane)/i.test(main)) {
        const tab = /\u00abQ(\d+)\u00bb\s+tab/i.exec(main);

        return action('open-send-publish', {
            type: 'openSendPublish',
            tab: tab != null ? tok.quotes[Number(tab[1])] : null,
        });
    }

    if (/^move\s+the\s+mouse\b/i.test(main)) {
        return action('mouse-away', {type: 'mouseAway'});
    }

    if (/^close\s+(?:the\s+)?(menu|dropdown|popover|dialog|popup)\b/i.test(main) || /^press\s+escape\b/i.test(main)) {
        return action('press', {type: 'press', key: 'Escape'});
    }

    const press = /^press\s+(?:the\s+)?([A-Za-z0-9+]+)(?:\s+key)?\s*$/i.exec(main);

    if (press != null) {
        const raw = press[1];
        const key = raw.includes('+') ? raw : (KEY_NAMES[raw.toLowerCase()] ?? (raw.length === 1 ? raw : null));

        if (key != null) {
            return action('press', {type: 'press', key});
        }
    }

    if (/^wait\b/i.test(main) && /\b(thumbnails?|images?|pictures?)\b/i.test(main) && /\bload/i.test(main)) {
        return action('wait-images', {type: 'waitImages'});
    }

    if (/^(wait|confirm|verify|check that|ensure that)\b/i.test(main)) {
        let state = 'visible';

        if (/\b(is|are|be)\s+enabled\b/i.test(main)) {
            state = 'enabled';
        } else if (/\b(hidden|disappear|disappears|closes|gone)\b/i.test(main)) {
            state = 'hidden';
        }

        return waitAction(clause, tok, state);
    }

    if (/^(make sure|ensure)\b/i.test(main) && quotes.length > 0 && /\b(selected|active|on|checked|chosen)\b/i.test(main)) {
        const tok2 = clauseTarget(clause.replace(/^(make sure|ensure)\s+/i, 'click '), tok);
        const role = roleHintNear(main, quotes[0]);

        return action('ensure-selected', {
            type: 'ensureSelected',
            text: tok.quotes[quotes[0]],
            role: role === 'tab' || role === 'radio' || role === 'button' ? role : null,
            within: tok2?.within ?? [],
        });
    }

    if (/^scroll\b/i.test(main)) {
        const target = clauseTarget(clause.replace(/^scroll\s+(?:down\s+|up\s+)?(?:to\s+)?/i, 'scroll '), tok);

        return target != null
            ? action('scroll', {type: 'scroll', target})
            : action('generic', {type: 'generic', verb: 'scroll', words: main});
    }

    const turn = /^turn\s+(on|off)\s+(?:the\s+)?switch(?:es)?\s+(?:for\s+)?(.+)$/i.exec(main);

    if (turn != null) {
        const names = [];
        const body = turn[2];
        const qs = placeholders(body, 'Q');

        if (qs.length > 0) {
            for (const qi of qs) {
                names.push(tok.quotes[qi]);
            }
        } else {
            for (const part of body.split(/\s*,\s*|\s+and\s+/)) {
                const name = part.replace(/^(the|desk|desks)\s+/i, '').trim();

                if (name.length > 0) {
                    names.push(name);
                }
            }
        }

        return action('switches', {type: 'switches', on: turn[1].toLowerCase() === 'on', names});
    }

    if (/^set\b/i.test(main)) {
        const pairs = parseSetPairs(main, tok);

        if (pairs.length > 0) {
            const within = leadScope != null ? [{kind: 'css', css: tok.sel[Number(leadScope[1])]}] : [];

            return action('set-datetime', {type: 'setDateTime', pairs, within});
        }
    }

    // "In [x] set the date ..." / "In [x] select 'A', 'B'"
    const leadIn = /^in(?:side)?\s+\u00abS(\d+)\u00bb,?\s+(.*)$/i.exec(fullMain);

    if (leadIn != null) {
        const scopeCss = tok.sel[Number(leadIn[1])];
        const rest = leadIn[2];

        if (/^set\b/i.test(rest)) {
            const pairs = parseSetPairs(rest, tok);

            if (pairs.length > 0) {
                return action('set-datetime', {type: 'setDateTime', pairs, within: [{kind: 'css', css: scopeCss}]});
            }
        }

        if (/^(select|choose|pick)\b/i.test(rest)) {
            const qs = placeholders(rest, 'Q');

            if (qs.length > 0) {
                return action('tree-select', {
                    type: 'treeSelect',
                    target: {kind: 'css', css: scopeCss},
                    values: qs.map((qi) => tok.quotes[qi]),
                });
            }

            return action('generic', {type: 'generic', verb: 'select', words: rest, reason: 'no quoted values to select'});
        }
    }

    if (/^(change|edit|replace)\b/i.test(main)) {
        const m = /\u00abS(\d+)\u00bb.*?\bto\s+\u00abQ(\d+)\u00bb/i.exec(main);

        if (m != null) {
            return action('fill', {
                type: 'fill',
                target: {kind: 'css', css: tok.sel[Number(m[1])]},
                value: tok.quotes[Number(m[2])],
            });
        }
    }

    const typeIn = /^(?:type|enter|input|write)\s+\u00abQ(\d+)\u00bb\s+(?:in|into|in to)\s+(.*)$/i.exec(clause);

    if (typeIn != null) {
        const target = clauseTarget(`fill ${typeIn[2]}`, tok);

        if (target != null) {
            return action('fill', {type: 'fill', target, value: tok.quotes[Number(typeIn[1])]});
        }
    }

    const fillWith = /^fill(?:\s+in)?\s+(.*?)\s+with\s+\u00abQ(\d+)\u00bb\s*$/i.exec(main);

    if (fillWith != null) {
        const target = clauseTarget(`fill ${fillWith[1]}`, tok);

        if (target != null) {
            return action('fill', {type: 'fill', target, value: tok.quotes[Number(fillWith[2])]});
        }
    }

    if (/^(check|tick|uncheck|untick)\b/i.test(main)) {
        const target = clauseTarget(clause, tok);
        const on = /^(check|tick)\b/i.test(main);

        if (target != null) {
            if (target.kind === 'label' && /\bradio\b/i.test(main)) {
                target.kind = 'role';
                target.role = 'radio';
                target.name = target.text;
                delete target.text;
            }

            return action('check', {type: 'check', target, on});
        }
    }

    if (/^hover\b/i.test(main)) {
        const target = clauseTarget(clause.replace(/^hover\s+(?:over\s+)?/i, 'hover '), tok);

        if (target != null) {
            return action('hover', {type: 'hover', target});
        }
    }

    if (/^(choose|pick|select)\b/i.test(main) && quotes.length > 0) {
        const target = clauseTarget(clause, tok);

        return action('choose', {
            type: 'choose',
            text: tok.quotes[quotes[0]],
            within: target?.within ?? [],
        });
    }

    if (/^open\b/i.test(main) && placeholders(main, 'S').length > 0) {
        const target = clauseTarget(clause, tok);

        return action('open-target', {type: 'openTarget', target});
    }

    if (/^(click|tap|double-click|dblclick|double click|press)\b/i.test(main)) {
        const dbl = /^(double-click|dblclick|double click)\b/i.test(main);
        const target = clauseTarget(clause, tok);

        if (target != null) {
            return action(dbl ? 'dblclick' : 'click', {type: dbl ? 'dblclick' : 'click', target});
        }
    }

    // Unknown shape: keep enough to make a generic attempt
    const verb = /^(\w+)/.exec(main)?.[1]?.toLowerCase() ?? null;
    const target = clauseTarget(clause, tok);

    return action('generic', {type: 'generic', verb, target, words: detokenize(main, tok)});
}

/**
 * Parses one manifest step (string) into a list of actions.
 * `previous` is the raw text of the previous step, for "do the same for 'x'".
 */
export function parseStep(raw, previous = null) {
    const repeat = /^\s*(?:and\s+)?do the same for\s+['"\u2018\u201c](.+?)['"\u2019\u201d]\s*\.?\s*$/i.exec(raw);

    if (repeat != null && previous != null) {
        // the item's own value, not an enclosing group's: prefer the one on article-item, else the last
        const values = [...previous.matchAll(/(\[data-test-id="([^"]+)"\])?\[data-test-value="([^"]+)"\]/g)];
        const itemValue = values.find((m) => m[2] === 'article-item') ?? values[values.length - 1];
        const oldValue = itemValue?.[3]
            ?? /['\u2018]([^'\u2019]+)['\u2019]/.exec(previous)?.[1]
            ?? null;

        if (oldValue != null) {
            const replayed = previous.split(oldValue).join(repeat[1]);
            const actions = parseStep(replayed, null);

            return actions.map((a) => ({...a, shape: `repeat:${a.shape}`}));
        }
    }

    const tok = tokenize(raw);
    const condition = /^if\s+(.+?)\s+(?:does not|doesn't|is not|isn't)\s+(?:show|contain|include|display|showing)\s+(.+?),\s*(.+)$/i.exec(tok.template);

    if (condition != null) {
        const target = clauseTarget(`check ${condition[1]}`, tok);
        const expected = condition[2].replace(/\u00abQ(\d+)\u00bb/, (m, qi) => tok.quotes[Number(qi)]).trim();
        const then = splitClauses(condition[3]).map((c) => parseClause(c, tok));

        return [{
            shape: 'if-not-text',
            type: 'ifNotText',
            target,
            expected,
            then,
            source: detokenize(tok.template, tok),
        }];
    }

    return splitClauses(tok.template).map((c) => parseClause(c, tok));
}

/**
 * Parses all steps of an entry; objects are passed through as structured actions.
 */
export function parseSteps(steps) {
    const result = [];
    let previous = null;

    for (const step of steps ?? []) {
        if (typeof step === 'string') {
            result.push({raw: step, actions: parseStep(step, previous)});
            previous = step;
        } else if (step != null && typeof step === 'object') {
            result.push({raw: JSON.stringify(step), actions: [structuredAction(step)]});
        }
    }

    return result;
}

/**
 * Structured step: {"action": "click", "target": "<selector>", "value": "...", "optional": true}
 */
export function structuredAction(step) {
    const type = step.action ?? step.type;
    const target = step.target != null ? selectorTarget(step.target) : null;
    const base = {shape: `structured:${type}`, optional: step.optional === true, source: JSON.stringify(step)};

    if (target != null && step.text != null) {
        target.hasText = step.text;
    }

    if (target != null && step.nth != null) {
        target.nth = step.nth;
    }

    switch (type) {
    case 'goto': return {...base, type: 'goto', route: step.route};
    case 'click': return {...base, type: 'click', target};
    case 'dblclick': return {...base, type: 'dblclick', target};
    case 'hover': return {...base, type: 'hover', target};
    case 'check': return {...base, type: 'check', target, on: step.value !== false};
    case 'fill': return {...base, type: 'fill', target, value: String(step.value ?? '')};
    case 'press': return {...base, type: 'press', key: step.key ?? step.value};
    case 'wait': return {
        ...base,
        type: 'wait',
        targets: target != null ? [target] : [],
        texts: step.text != null && target == null ? [{text: step.text, inContainer: false}] : [],
        state: step.state ?? 'visible',
    };
    case 'selectDesk': return {...base, type: 'selectDesk', name: step.value ?? step.name};
    case 'openItem': return {...base, type: 'openItem', name: step.value ?? step.name, desk: step.desk ?? null};
    case 'openSendPublish': return {...base, type: 'openSendPublish', tab: step.tab ?? null};
    case 'openViewSwitcher': return {...base, type: 'openViewSwitcher'};
    case 'choose': return {...base, type: 'choose', text: step.value, within: target != null ? [target] : []};
    case 'treeSelect': return {...base, type: 'treeSelect', target, values: [].concat(step.value ?? step.values)};
    case 'switches': return {...base, type: 'switches', on: step.on !== false, names: [].concat(step.value ?? step.names)};
    case 'scroll': return {...base, type: 'scroll', target};
    case 'mouseAway': return {...base, type: 'mouseAway'};
    case 'waitImages': return {...base, type: 'waitImages'};
    case 'settle': return {...base, type: 'settle'};
    case 'sleep': return {...base, type: 'sleep', ms: Number(step.ms ?? step.value ?? 500)};
    case 'evaluate': return {...base, type: 'evaluate', script: step.script};
    default: return {...base, shape: 'generic', type: 'generic', verb: type, target, words: base.source};
    }
}

/**
 * A selector string from a manifest (crop, highlight, mask, structured step).
 * `data-test-id=x` or a bare id go through test id first, then CSS, then text.
 */
export function selectorTarget(value) {
    const s = String(value).trim();
    const testIdEq = /^data-test-id\s*=\s*["']?([^"'\]]+)["']?$/.exec(s);

    if (testIdEq != null) {
        return {kind: 'bare', value: testIdEq[1]};
    }

    if (/^[\w-]+$/.test(s)) {
        return {kind: 'bare', value: s};
    }

    if (/^(text|role)=/.test(s)) {
        const [kind, rest] = [s.slice(0, 4), s.slice(5)];

        if (kind === 'text') {
            return {kind: 'text', text: rest};
        }

        const [role, ...name] = rest.split(':');

        return {kind: 'role', role, name: name.join(':') || undefined};
    }

    if (/[[\].#>:]/.test(s)) {
        return {kind: 'css', css: s};
    }

    return {kind: 'bare', value: s};
}

// ---------------------------------------------------------------------------
// Crop, highlight, route, viewport
// ---------------------------------------------------------------------------

function partTarget(input, tok) {
    // "X in [scope]" -> X searched inside scope; the later scope is the outer one
    const scopes = [];
    const part = input.replace(/\s+(?:in|inside|within)\s+(?:the\s+)?\u00abS(\d+)\u00bb/ig, (m, si) => {
        scopes.unshift({kind: 'css', css: tok.sel[Number(si)]});

        return '';
    });
    const withScopes = (target) => {
        if (target != null && scopes.length > 0) {
            target.within = [...scopes, ...(target.within ?? [])];
        }

        return target;
    };

    const main = stripParens(part);
    const sels = placeholders(main, 'S');
    const promoted = sels.length > 0 ? sels : parenSelectors(part, tok);

    if (promoted.length > 0) {
        const target = {kind: 'css', css: tok.sel[promoted[0]]};

        if (sels.length > 0) {
            const qs = placeholders(main, 'Q');

            if (qs.length > 0) {
                target.hasText = tok.quotes[qs[0]];
            } else {
                const before = main.slice(0, main.indexOf(PH('S', sels[0])));
                const words = phraseWords(before).filter((w) => !STOP_WORDS.has(w.toLowerCase()));

                if (words.length > 0 && /^[A-Z]/.test(words[0])) {
                    target.hasText = words.join(' ');
                }
            }
        }

        return withScopes(target);
    }

    const qs = placeholders(main, 'Q');

    if (qs.length > 0) {
        const role = roleHintNear(main, qs[0]);
        const value = tok.quotes[qs[0]];

        if (role === 'switch' || /\bswitch\b/i.test(main)) {
            return withScopes({kind: 'label', text: value, hint: 'switch'});
        }

        if (role != null) {
            return withScopes({kind: 'role', role, name: value});
        }

        const after = main.slice(main.indexOf(PH('Q', qs[0])) + PH('Q', qs[0]).length);
        const hint = singular(phraseWords(after)[0]?.toLowerCase());

        return withScopes({kind: 'label', text: value, hint: NOUN_HINTS.includes(hint) || NOUN_HINTS.includes(`${hint}s`) ? hint : null});
    }

    const genericPlural = /\b(buttons|switches|tabs|items|actions|controls|icons|fields|rows)\b/i.test(main);

    if ((main.trim().length === 0 || genericPlural) && scopes.length > 0) {
        return scopes.length === 1 ? scopes[0] : {...scopes[scopes.length - 1], within: scopes.slice(0, -1)};
    }

    return withScopes(phraseTarget(detokenize(main, tok)));
}

/**
 * crop: "full" | "element: <selector> [plus <selector>]* [top Npx] [plus about Npx ... to its left]"
 * or a structured object {element, plus, expand, maxHeight, region}.
 */
export function parseCrop(crop) {
    if (crop == null) {
        return {kind: 'full', targets: [], expand: {}, notes: ['no crop given, using full']};
    }

    if (typeof crop === 'object') {
        if (crop.region != null) {
            return {kind: 'region', region: crop.region, targets: [], expand: {}, notes: []};
        }

        const elements = [].concat(crop.element ?? [], crop.plus ?? []);

        return {
            kind: elements.length > 0 ? 'element' : 'full',
            targets: elements.map((e) => selectorTarget(e)),
            expand: crop.expand ?? {},
            maxHeight: crop.maxHeight ?? null,
            clipAbove: crop.clipAbove ?? null,
            notes: [],
        };
    }

    const s = String(crop).trim();

    if (/^(full|full ?page|viewport|whole page|page)$/i.test(s)) {
        return {kind: 'full', targets: [], expand: {}, notes: []};
    }

    const body = s.replace(/^element\s*:\s*/i, '');
    const tok = tokenize(body);
    const notes = [];
    let template = tok.template;
    const expand = {};
    let maxHeight = null;

    for (const pi of placeholders(template, 'P')) {
        notes.push(`ignored crop remark: (${detokenize(tok.parens[pi], tok)})`);
    }

    template = stripParens(template);

    template = template.replace(/\s*plus\s+(?:about\s+|roughly\s+|~)?(\d+)\s*px\b[^,]*?\bto\s+(?:its|the)\s+(left|right)\b/ig, (m, px, side) => {
        expand[side.toLowerCase()] = Number(px);

        return '';
    });

    template = template.replace(/\s*plus\s+(?:about\s+|roughly\s+|~)?(\d+)\s*px\b[^,]*?\b(above|below)\b/ig, (m, px, side) => {
        expand[side === 'above' ? 'top' : 'bottom'] = Number(px);

        return '';
    });

    template = template.replace(/\s*\b(?:the\s+)?(top|first)\s+(\d+)\s*px\b/ig, (m, w, px) => {
        maxHeight = Number(px);

        return '';
    });

    const parts = template.split(/\s+plus\s+|\s*\+\s*/i).map((p) => p.trim()).filter(Boolean);
    const targets = [];

    for (const part of parts) {
        const t = partTarget(part, tok);

        if (t != null) {
            targets.push(t);
        } else {
            notes.push(`could not interpret crop part "${detokenize(part, tok)}"`);
        }
    }

    if (targets.length === 0) {
        return {kind: 'full', targets: [], expand: {}, notes: [...notes, `crop "${s}" has no resolvable element, using full`]};
    }

    return {kind: 'element', targets, expand, maxHeight, notes};
}

/**
 * highlight: "none" | free text listing elements | array of selectors.
 * Returns {style, items: [{label, target, raw}]}. label is the 1-based position for badges.
 */
export function parseHighlight(highlight, styleOverride = null) {
    if (highlight == null) {
        return {style: styleOverride ?? 'outline', items: [], notes: []};
    }

    if (Array.isArray(highlight)) {
        const style = styleOverride ?? 'outline';

        return {
            style,
            items: highlight.map((h, i) => {
                let target;

                if (Array.isArray(h)) {
                    // one box around several elements
                    target = {kind: 'union', parts: h.map((x) => selectorTarget(x))};
                } else if (typeof h === 'object') {
                    target = selectorTarget(h.selector ?? h.target);
                } else {
                    target = selectorTarget(h);
                }

                return {position: i + 1, target, raw: typeof h === 'object' ? JSON.stringify(h) : String(h)};
            }),
            notes: [],
        };
    }

    const s = String(highlight).trim();

    if (/^(none|no|-|n\/a)\.?$/i.test(s) || s.length === 0) {
        return {style: styleOverride ?? 'outline', items: [], notes: ['highlight is none']};
    }

    const style = styleOverride ?? (/\b(callouts?)\b/i.test(s) ? 'callout' : /\b(number|numbered|numbers|badge|badges)\b/i.test(s) ? 'badge' : 'outline');
    const tok = tokenize(s);
    let template = tok.template;

    // "number or outline: a, b, c" -> drop the instruction prefix
    const colon = /^([^:\u00ab]{0,40}):\s+/.exec(template);

    if (colon != null && colon[1].split(/\s+/).length <= 5) {
        template = template.slice(colon[0].length);
    }

    template = template.replace(/^(?:a\s+)?(?:box|boxes|outline|outlines|circle|circles|highlight|highlights|frame)\s+(?:around|on|of)\s+/i, '');

    const parts = template
        .split(/\s*,\s*(?:and\s+)?|\s+and\s+/i)
        .map((p) => p.trim())
        .filter(Boolean);

    const items = [];
    const notes = [];

    parts.forEach((part, i) => {
        const target = partTarget(part, tok);

        items.push({position: i + 1, target, raw: detokenize(part, tok)});

        if (target == null) {
            notes.push(`could not interpret highlight "${detokenize(part, tok)}"`);
        }
    });

    return {style, items, notes};
}

/**
 * route -> {kind: 'hash', hash} | {kind: 'url', url} | {kind: 'menu', hash, warning}
 */
export function parseRoute(route, fallback = '#/workspace/monitoring') {
    if (route == null || String(route).trim() === '') {
        return {kind: 'hash', hash: fallback, warning: 'no route given, using monitoring'};
    }

    const r = String(route).trim();

    if (/^https?:\/\//i.test(r)) {
        return {kind: 'url', url: r};
    }

    const m = /^\/?(#\/.*)$/.exec(r);

    if (m != null) {
        return {kind: 'hash', hash: m[1]};
    }

    if (/^\/[\w-]/.test(r) && !/\s/.test(r)) {
        return {kind: 'hash', hash: `#${r}`};
    }

    return {kind: 'menu', hash: fallback, warning: `route "${r}" looks like a menu path; falling back to ${fallback}`};
}

export function parseViewport(viewport) {
    if (viewport != null && typeof viewport === 'object') {
        return {width: Number(viewport.width), height: Number(viewport.height)};
    }

    const m = /^(\d+)\s*[x\u00d7]\s*(\d+)$/i.exec(String(viewport ?? '').trim());

    return m != null ? {width: Number(m[1]), height: Number(m[2])} : {width: 1440, height: 900};
}

/**
 * file "master-desk/overview-tab.png" -> {page: "master-desk", shot: "overview-tab"}
 */
export function shotId(file, manifestName) {
    const clean = String(file ?? '').replace(/\\/g, '/').replace(/^\.?\//, '');
    const parts = clean.split('/').filter(Boolean);
    const base = (parts[parts.length - 1] ?? 'shot').replace(/\.(png|jpe?g|webp)$/i, '');
    const page = parts.length > 1 ? parts[parts.length - 2] : manifestName;

    return {page, shot: base};
}

/** Formats a date for the app's `view.dateformat` (YYYY, MM, DD with any separator). */
export function formatDate(date, format = 'MM/DD/YYYY') {
    const pad = (n) => String(n).padStart(2, '0');

    return format
        .replace('YYYY', String(date.getFullYear()))
        .replace('MM', pad(date.getMonth() + 1))
        .replace('DD', pad(date.getDate()));
}

/** "tomorrow" / "today" / "in 3 days" / literal -> string for the date input. */
export function resolveDateValue(value, format, now = new Date()) {
    const v = String(value).trim().toLowerCase();
    const d = new Date(now.getTime());

    if (v === 'today') {
        return formatDate(d, format);
    }

    if (v === 'tomorrow') {
        d.setDate(d.getDate() + 1);

        return formatDate(d, format);
    }

    const inDays = /^in (\d+) days?$/.exec(v);

    if (inDays != null) {
        d.setDate(d.getDate() + Number(inDays[1]));

        return formatDate(d, format);
    }

    return String(value);
}

/** Human-readable one-liner for a parsed action, used in logs and --dry-run. */
export function describeAction(a) {
    const t = (target) => {
        if (target == null) {
            return '<none>';
        }

        const scope = [
            target.scopePrev ? 'prev' : null,
            ...(target.within ?? []).map((w) => t(w)),
        ].filter(Boolean);
        const prefix = scope.length > 0 ? `${scope.join(' > ')} > ` : '';
        let core;

        switch (target.kind) {
        case 'css': core = `css(${target.css})`; break;
        case 'bare': core = `bare(${target.value})`; break;
        case 'role': core = `role(${target.role}${target.name != null ? `, "${target.name}"` : ''})`; break;
        case 'label': core = `label("${target.text}"${target.hint ? `, ${target.hint}` : ''})`; break;
        case 'phrase': core = `phrase("${target.text}"${target.hint ? `, ${target.hint}` : ''})`; break;
        case 'text': core = `text("${target.text}")`; break;
        case 'alias': core = `alias(${target.name})`; break;
        case 'prev': core = 'prev'; break;
        case 'union': core = `union(${target.parts.map((x) => t(x)).join(' + ')})`; break;
        default: core = JSON.stringify(target);
        }

        return `${prefix}${core}${target.hasText != null ? ` hasText("${target.hasText}")` : ''}${target.nth != null ? ` [${target.nth}]` : ''}`;
    };

    switch (a.type) {
    case 'goto': return `goto ${a.route}`;
    case 'click': case 'dblclick': case 'hover': case 'scroll': return `${a.type} ${t(a.target)}`;
    case 'check': return `${a.on ? 'check' : 'uncheck'} ${t(a.target)}`;
    case 'fill': return `fill ${t(a.target)} with "${a.value}"`;
    case 'press': return `press ${a.key}`;
    case 'wait': return `wait ${a.state}: ${a.targets.map(t).join(', ') || '-'}${a.texts.length > 0 ? ` texts: ${a.texts.map((x) => `"${x.text}"${x.inContainer ? ' (in first)' : ''}`).join(', ')}` : ''}`;
    case 'settle': return 'settle (network idle + short pause)';
    case 'waitImages': return 'wait for all visible images to load';
    case 'selectDesk': return `select desk "${a.name}"`;
    case 'openItem': return `open item "${a.name}" for editing${a.desk ? ` from desk "${a.desk}"` : ''}`;
    case 'openSendPublish': return `open Send to / Publish panel${a.tab ? ` on tab "${a.tab}"` : ''}`;
    case 'openViewSwitcher': return 'open the monitoring view switcher';
    case 'openTarget': return `open ${t(a.target)} (popover trigger or click)`;
    case 'mouseAway': return 'move mouse off the page';
    case 'ensureSelected': return `ensure "${a.text}" ${a.role ?? 'tab/radio/button'} is selected`;
    case 'choose': return `choose "${a.text}"${a.within?.length ? ` within ${a.within.map(t).join(' > ')}` : ''}`;
    case 'treeSelect': return `tree-select ${t(a.target)} values ${a.values.map((v) => `"${v}"`).join(', ')}`;
    case 'switches': return `turn ${a.on ? 'on' : 'off'} switches ${a.names.map((n) => `"${n}"`).join(', ')}`;
    case 'setDateTime': return `set ${a.pairs.map((p) => `${p.field} ${p.css} = ${p.value}`).join('; ')}${a.within?.length ? ` within ${a.within.map(t).join(' > ')}` : ''}`;
    case 'ifNotText': return `if ${t(a.target)} does not show "${a.expected}": ${a.then.map(describeAction).join(' ; ')}`;
    case 'noop': return 'note only, nothing to do';
    case 'sleep': return `sleep ${a.ms}ms`;
    case 'evaluate': return 'evaluate script';
    case 'generic': return `GENERIC verb=${a.verb ?? '?'} target=${t(a.target)}${a.reason ? ` (${a.reason})` : ''}`;
    default: return JSON.stringify(a);
    }
}
