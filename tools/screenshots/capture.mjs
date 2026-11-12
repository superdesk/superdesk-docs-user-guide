#!/usr/bin/env node
// Captures raw documentation screenshots of the Superdesk web client from JSON manifests.
// See CAPTURE.md for usage, the manifest fields and the step grammar.

import fs from 'node:fs';
import path from 'node:path';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
import {parseArgs} from 'node:util';
import {
    ALIASES,
    describeAction,
    parseCrop,
    parseHighlight,
    parseRoute,
    parseSteps,
    parseViewport,
    resolveDateValue,
    selectorTarget,
    shotId,
} from './steps.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const DEFAULT_E2E_CLIENT = path.resolve(HERE, '../../../superdesk-client-core/e2e/client');
const DPR = 2;
const DEFAULT_VIEWPORT = {width: 1440, height: 900};
const MONITORING_ROUTE = '#/workspace/monitoring';
// `.sd-page` covers the settings pages, which have no workspace navigation when superdesk-planning is installed.
const APP_SHELL = '[data-test-id="workspace-navigation"], [data-test-id="top-menu"], [data-test-id="dashboard"], [data-test-id="monitoring-view"], .sd-main-content-grid, .sd-page';

const DEFAULT_USERS = {
    admin: {username: 'admin', password: 'admin'},
    editor: {username: 'samgamgee', password: 'samgamgee'},
    journalist: {username: 'frodobaggins', password: 'frodobaggins'},
    samgamgee: {username: 'samgamgee', password: 'samgamgee'},
    frodobaggins: {username: 'frodobaggins', password: 'frodobaggins'},
};

// ---------------------------------------------------------------------------
// CLI
// ---------------------------------------------------------------------------

const USAGE = `Usage: node capture.mjs --manifests <dir> --out <raw-dir> [options]

  --manifests <dir>        folder with one JSON manifest per docs page (required)
  --out <dir>              output folder for raw shots (required unless --dry-run)
  --only <slug[/shot]>     only these shots; comma-separated list allowed
  --base-url <url>         client URL (default http://localhost:9000)
  --api-url <url>          backend API URL (default http://localhost:5002/api)
  --restore                restore a database snapshot before the first shot
  --snapshot <name>        snapshot for --restore (default main)
  --users <file>           user map (default: users.json next to this script, if present)
  --timeout <ms>           per-action timeout (default 15000)
  --timezone <tz>          browser time zone (default Europe/Prague); use the newsroom's
                           DEFAULT_TIMEZONE so entered and displayed times agree
  --playwright-from <dir>  folder whose node_modules has playwright
                           (default ${DEFAULT_E2E_CLIENT}, or $SUPERDESK_E2E_CLIENT)
  --executable-path <file> Chromium binary to launch instead of Playwright's own
                           (also $CHROMIUM_PATH)
  --headed                 show the browser
  --slow-mo <ms>           slow every Playwright action down (debugging)
  --dry-run                parse manifests and print the interpreted steps, no browser
  -h, --help               this text
`;

function parseCli(argv) {
    const {values} = parseArgs({
        args: argv,
        options: {
            'manifests': {type: 'string'},
            'out': {type: 'string'},
            'only': {type: 'string'},
            'base-url': {type: 'string', default: 'http://localhost:9000'},
            'api-url': {type: 'string', default: 'http://localhost:5002/api'},
            'restore': {type: 'boolean', default: false},
            'snapshot': {type: 'string', default: 'main'},
            'users': {type: 'string'},
            'timeout': {type: 'string', default: '15000'},
            'timezone': {type: 'string', default: 'Europe/Prague'},
            'playwright-from': {type: 'string'},
            'executable-path': {type: 'string'},
            'headed': {type: 'boolean', default: false},
            'slow-mo': {type: 'string', default: '0'},
            'dry-run': {type: 'boolean', default: false},
            'help': {type: 'boolean', short: 'h', default: false},
        },
        strict: true,
    });

    if (values.help) {
        process.stdout.write(USAGE);
        process.exit(0);
    }

    if (values.manifests == null || (values.out == null && !values['dry-run'])) {
        process.stderr.write(`--manifests and --out are required\n\n${USAGE}`);
        process.exit(2);
    }

    return {
        manifests: path.resolve(values.manifests),
        out: values.out != null ? path.resolve(values.out) : null,
        only: values.only != null ? values.only.split(',').map((s) => s.trim()).filter(Boolean) : null,
        baseUrl: values['base-url'].replace(/\/+$/, ''),
        apiUrl: values['api-url'].replace(/\/+$/, ''),
        restore: values.restore,
        snapshot: values.snapshot,
        usersFile: values.users ?? path.join(HERE, 'users.json'),
        timeout: Number(values.timeout),
        timezone: values.timezone,
        playwrightFrom: values['playwright-from'] ?? process.env.SUPERDESK_E2E_CLIENT ?? DEFAULT_E2E_CLIENT,
        executablePath: values['executable-path'] ?? process.env.CHROMIUM_PATH ?? null,
        headed: values.headed,
        slowMo: Number(values['slow-mo']),
        dryRun: values['dry-run'],
    };
}

function loadPlaywright(dir) {
    const require = createRequire(path.join(dir, 'package.json'));

    try {
        return require('playwright');
    } catch (e) {
        throw new Error(
            `Cannot load playwright from ${dir}/node_modules (${e.message}).\n`
            + 'Run `npm ci` and `npx playwright install chromium` in superdesk-client-core/e2e/client, '
            + 'or point --playwright-from / $SUPERDESK_E2E_CLIENT at a folder that has playwright installed.',
        );
    }
}

function loadUsers(file) {
    const users = {...DEFAULT_USERS};

    if (fs.existsSync(file)) {
        const extra = JSON.parse(fs.readFileSync(file, 'utf8'));

        for (const [key, value] of Object.entries(extra)) {
            users[key] = typeof value === 'string' ? {username: value, password: value} : value;
        }
    }

    return users;
}

function loadShots(dir, only) {
    const files = fs.readdirSync(dir).filter((f) => f.endsWith('.json') && f !== 'users.json').sort();
    const shots = [];

    for (const file of files) {
        const manifestName = file.replace(/\.json$/, '');
        const entries = JSON.parse(fs.readFileSync(path.join(dir, file), 'utf8'));

        if (!Array.isArray(entries)) {
            throw new Error(`${file}: expected a JSON array`);
        }

        for (const entry of entries) {
            const id = shotId(entry.file, manifestName);

            shots.push({...id, manifest: file, entry});
        }
    }

    if (only == null) {
        return shots;
    }

    return shots.filter((s) => only.some((o) => {
        const [page, shot] = o.split('/');

        return s.page === page && (shot == null || shot === s.shot || `${shot}.png` === `${s.shot}.png`);
    }));
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function escapeRegex(s) {
    return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function exactText(s) {
    return new RegExp(`^\\s*${escapeRegex(s)}\\s*$`, 'i');
}

class StepError extends Error {}

function describeTarget(target) {
    return describeAction({type: 'click', target}).replace(/^click /, '');
}

async function firstVisible(candidates, timeout) {
    const deadline = Date.now() + timeout;

    for (;;) {
        for (const c of candidates) {
            try {
                const visible = c.locator.filter({visible: true});

                if (await visible.count() > 0) {
                    let picked = visible.first();

                    if (c.nth === 'last') {
                        picked = visible.last();
                    } else if (typeof c.nth === 'number') {
                        picked = visible.nth(c.nth);
                    }

                    return {locator: picked, how: c.how};
                }
            } catch {
                // an invalid CSS candidate (a bare word tried as CSS) is just a miss
            }
        }

        if (Date.now() >= deadline) {
            return null;
        }

        await sleep(200);
    }
}

async function waitForAny(locators, timeout) {
    const deadline = Date.now() + timeout;

    for (;;) {
        for (let i = 0; i < locators.length; i++) {
            if (await locators[i].first().isVisible().catch(() => false)) {
                return i;
            }
        }

        if (Date.now() >= deadline) {
            return -1;
        }

        await sleep(250);
    }
}

async function waitStable(locator, timeout = 3000) {
    const deadline = Date.now() + timeout;
    let last = null;
    let same = 0;

    while (Date.now() < deadline) {
        const box = await locator.boundingBox().catch(() => null);
        const key = box == null ? null : [box.x, box.y, box.width, box.height].map((n) => Math.round(n)).join(',');

        if (key != null && key === last) {
            same++;

            if (same >= 2) {
                return box;
            }
        } else {
            same = 0;
        }

        last = key;
        await sleep(100);
    }

    return locator.boundingBox();
}

// ---------------------------------------------------------------------------
// Sessions (one browser context per user)
// ---------------------------------------------------------------------------

class Sessions {
    constructor(browser, opts, users) {
        this.browser = browser;
        this.opts = opts;
        this.users = users;
        this.map = new Map();
    }

    credentials(userKey) {
        const key = userKey ?? 'admin';
        const creds = this.users[key];

        if (creds != null) {
            return {key, ...creds};
        }

        return {key, username: key, password: key, guessed: true};
    }

    async get(userKey, log) {
        const creds = this.credentials(userKey);

        if (creds.guessed) {
            log(`WARN user "${creds.key}" is not in the user map; trying username=password="${creds.key}"`);
        }

        const existing = this.map.get(creds.key);

        if (existing != null) {
            return existing;
        }

        const context = await this.browser.newContext({
            baseURL: this.opts.baseUrl,
            viewport: DEFAULT_VIEWPORT,
            deviceScaleFactor: DPR,
            colorScheme: 'light',
            reducedMotion: 'reduce',
            locale: 'en-US',
            timezoneId: this.opts.timezone,
        });

        await context.addInitScript(removeTestFontStyleOnInsert);

        const page = await context.newPage();
        const session = {context, page, creds, sink: []};

        page.setDefaultTimeout(this.opts.timeout);
        page.setDefaultNavigationTimeout(60000);
        page.on('console', (m) => session.sink.push(`[console.${m.type()}] ${m.text()}`));
        page.on('pageerror', (e) => session.sink.push(`[pageerror] ${e.message}`));
        page.on('dialog', (d) => {
            session.sink.push(`[dialog.${d.type()}] ${d.message()} (accepted)`);
            d.accept().catch(() => {});
        });

        log(`logging in as ${creds.username} (manifest user "${creds.key}")`);

        try {
            await login(page, creds, this.opts.baseUrl, loginTimeout(this.opts.timeout));
        } catch (e) {
            e.debugPage = page;
            e.debugContext = context;
            e.debugSink = session.sink;
            throw e;
        }

        this.map.set(creds.key, session);

        return session;
    }

    async closeAll() {
        for (const s of this.map.values()) {
            await s.context.close().catch(() => {});
        }

        this.map.clear();
    }
}

// Runs in the page before any app script. The e2e client entry appends a <style> that forces
// Arial and disables font smoothing so visual tests are deterministic; documentation needs the
// real fonts, so drop that element as soon as it is inserted.
function removeTestFontStyleOnInsert() {
    const isTestFontStyle = (n) => n.nodeName === 'STYLE' && (n.textContent ?? '').includes('Arial!important');
    const observer = new MutationObserver((mutations) => {
        for (const m of mutations) {
            for (const n of m.addedNodes) {
                if (isTestFontStyle(n)) {
                    n.remove();
                    observer.disconnect();
                }
            }
        }
    });

    observer.observe(document, {childList: true, subtree: true});
}

async function removeTestFontStyle(page) {
    return page.evaluate(() => {
        let removed = 0;

        for (const s of document.querySelectorAll('style')) {
            if ((s.textContent ?? '').includes('Arial!important')) {
                s.remove();
                removed++;
            }
        }

        return removed;
    });
}

async function waitForFonts(page) {
    await page.evaluate(async () => {
        void document.body?.offsetHeight;
        await document.fonts.ready;
        await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
    });
}

async function fillLoginForm(page, creds) {
    const form = page.getByTestId('login-page');

    await form.getByTestId('username').fill(creds.username);
    await form.getByTestId('password').fill(creds.password);
    await form.getByTestId('submit').click();
}

// Loading the app after login takes longer on a remote instance than on a local stack, so the login
// waits stretch with --timeout but never go below the 60 s a local stack is tuned for.
function loginTimeout(timeout) {
    return Math.max(60000, timeout ?? 0);
}

async function login(page, creds, baseUrl, timeout = 60000) {
    await page.goto(`${baseUrl}/`, {waitUntil: 'domcontentloaded'});

    const username = page.getByTestId('login-page').getByTestId('username');
    const shell = page.locator(APP_SHELL);
    const first = await waitForAny([username, shell], timeout);

    if (first === -1) {
        throw new Error(`neither the login form nor the app shell appeared at ${baseUrl}`);
    }

    if (first === 0) {
        await fillLoginForm(page, creds);

        const result = await waitForAny([shell, page.getByTestId('login-error-401')], timeout);

        if (result !== 0) {
            throw new Error(`login failed for ${creds.username}`);
        }
    }

    await dismissInterruptions(page, creds);
}

// The first-run "Welcome to Superdesk" modal and the mid-session "session has expired"
// overlay both swallow clicks; see Monitoring.waitUntilReady in the e2e page objects.
async function dismissInterruptions(page, creds) {
    const expired = page.locator('.login-screen .session-error');

    if (await expired.isVisible().catch(() => false)) {
        await fillLoginForm(page, creds);
        await page.locator('.login-screen').waitFor({state: 'hidden', timeout: 30000}).catch(() => {});
    }

    const skip = page.getByRole('button', {name: 'Skip', exact: true});

    if (await skip.isVisible().catch(() => false)) {
        await skip.click().catch(() => {});
    }

    // Administrators get "There are issues with instance configuration" once per session when an
    // extension cannot start (a vocabulary it needs is missing); its mask swallows every click.
    const configIssue = page.locator('.p-dialog').filter({hasText: /issues with instance configuration/i})
        .filter({visible: true}).first();

    if (await configIssue.count() > 0) {
        const close = configIssue.locator('button[aria-label="Close"], .p-dialog-header-close').first();

        if (await close.count() > 0) {
            await close.click().catch(() => {});
        } else {
            await page.keyboard.press('Escape').catch(() => {});
        }

        await sleep(300);
    }

    // "Item Unlocked: This item was unlocked by ..." shows when another session of the same
    // user held the lock; its modal mask swallows every click until acknowledged.
    for (let i = 0; i < 10; i++) {
        const notice = page.locator('.p-dialog').filter({hasText: /unlocked by/i}).filter({visible: true}).first();

        if (await notice.count() === 0) {
            break;
        }

        await notice.getByRole('button', {name: 'OK', exact: true}).click().catch(() => {});
        await sleep(300);
    }
}

const LOADERS = '[data-test-id="list-item-placeholder"], .sd-loader, .sd-loader--dark, .loading-indicator';

async function waitForNoLoaders(ctx, timeout = 30000) {
    const deadline = Date.now() + timeout;

    while (await ctx.page.locator(LOADERS).filter({visible: true}).count() > 0) {
        if (Date.now() > deadline) {
            ctx.warn('loading placeholders were still visible when the shot was taken');

            return;
        }

        await sleep(250);
    }
}

// Items the user has open for editing sit in the opened-articles bar at the bottom of every
// page. Closing them keeps unrelated item titles out of the shots.
async function closeOpenItems(ctx) {
    const bar = ctx.page.getByTestId('opened-articles-bar');
    let closed = 0;

    for (let i = 0; i < 25; i++) {
        const close = bar.getByTestId('close').filter({visible: true}).first();

        if (await close.count() === 0) {
            break;
        }

        const before = await bar.getByTestId('item').count();

        await dismissInterruptions(ctx.page, ctx.creds);
        await close.click();
        await sleep(300);
        await dismissInterruptions(ctx.page, ctx.creds);

        const unsaved = ctx.page.getByTestId('unsaved-changes-dialog');

        if (await unsaved.isVisible().catch(() => false)) {
            await unsaved.getByRole('button', {name: 'Ignore', exact: true}).click();
        }

        const deadline = Date.now() + 10000;

        while (await bar.getByTestId('item').count() >= before && Date.now() < deadline) {
            await sleep(200);
        }

        closed++;
    }

    await dismissInterruptions(ctx.page, ctx.creds);

    if (closed > 0) {
        ctx.log(`  closed ${closed} item(s) in the opened-articles bar`);
    }
}

async function settle(page, ms = 300) {
    await page.waitForLoadState('networkidle', {timeout: 5000}).catch(() => {});
    await sleep(ms);
}

// ---------------------------------------------------------------------------
// Target resolution
// ---------------------------------------------------------------------------

function baseFor(ctx, target) {
    let base = ctx.page;

    if (target.scopePrev && ctx.prev != null) {
        base = ctx.prev;
    }

    for (const w of target.within ?? []) {
        base = chainOne(ctx, base, w);
    }

    return base;
}

// Single chained locator for scope elements: css directly, others by their first candidate.
function chainOne(ctx, base, target) {
    if (target.kind === 'css') {
        let loc = base.locator(target.css);

        if (target.hasText != null) {
            loc = loc.filter({hasText: target.hasText});
        }

        return loc;
    }

    const cands = candidates(ctx, {...target, within: undefined, scopePrev: false}, base);

    return cands[0]?.locator ?? base;
}

function labelCandidates(ctx, base, text, hint) {
    const page = ctx.page;
    const out = [];
    const add = (how, locator) => out.push({how, locator});

    if (hint === 'switch') {
        add('switch by name', base.getByRole('checkbox', {name: text, exact: true}));
        add('switch in labelled row', base.locator('li, .sd-line-input, .form__row')
            .filter({has: page.locator('label', {hasText: exactText(text)})})
            .locator('[role="checkbox"], [role="switch"], input[type="checkbox"]'));

        return out;
    }

    const byHint = {
        tab: ['tab'],
        radio: ['radio'],
        button: ['button'],
        link: ['link'],
        option: ['option', 'treeitem'],
        checkbox: ['checkbox'],
    }[hint] ?? [];

    if (hint === 'field' || hint === 'input') {
        add('label', base.getByLabel(text, {exact: true}));
        add('placeholder', base.getByPlaceholder(text));
    }

    for (const role of [...byHint, 'button', 'tab', 'radio', 'link', 'menuitem', 'option', 'treeitem', 'checkbox']) {
        add(`role ${role}`, base.getByRole(role, {name: text, exact: true}));
    }

    add('exact text', base.getByText(text, {exact: true}));
    add('button (substring)', base.getByRole('button', {name: text}));
    add('text (substring)', base.getByText(text));

    return out;
}

function aliasCss(ctx, name) {
    const alias = ALIASES[name];

    if (alias == null) {
        return [];
    }

    if (alias.lastItem) {
        return [];
    }

    return [].concat(alias.css);
}

function candidates(ctx, target, explicitBase = null) {
    const base = explicitBase ?? baseFor(ctx, target);
    const withText = (loc) => (target.hasText != null ? loc.filter({hasText: target.hasText}) : loc);
    const nth = target.nth ?? null;
    const out = [];

    switch (target.kind) {
    case 'css':
        out.push({how: 'css', locator: withText(base.locator(target.css))});
        break;
    case 'bare':
        out.push({how: 'test id', locator: withText(base.getByTestId(target.value))});
        out.push({how: 'css', locator: withText(base.locator(target.value))});
        out.push({how: 'text', locator: base.getByText(target.value, {exact: true})});
        out.push({how: 'text (substring)', locator: base.getByText(target.value)});
        break;
    case 'role':
        out.push({how: `role ${target.role}`, locator: withText(base.getByRole(target.role, target.name != null ? {name: target.name, exact: true} : {}))});

        if (target.name != null) {
            out.push({how: `role ${target.role} (substring)`, locator: base.getByRole(target.role, {name: target.name})});
            out.push({how: 'exact text', locator: base.getByText(target.name, {exact: true})});
        }

        break;
    case 'text':
        out.push({how: 'text', locator: base.getByText(target.text)});
        break;
    case 'label':
        out.push(...labelCandidates(ctx, base, target.text, target.hint));
        break;
    case 'phrase':
        if (!/\s/.test(target.text)) {
            out.push({how: 'test id', locator: base.getByTestId(target.text)});
        }

        out.push(...labelCandidates(ctx, base, target.text, target.hint));
        break;
    case 'alias':
        if (ALIASES[target.name]?.lastItem) {
            if (ctx.lastItem != null) {
                out.push({how: 'last item', locator: ctx.lastItem});
            }
        } else {
            for (const css of aliasCss(ctx, target.name)) {
                out.push({how: `alias ${target.name}`, locator: withText(base.locator(css))});
            }
        }

        break;
    case 'prev':
        if (ctx.prev != null) {
            out.push({how: 'previous element', locator: ctx.prev});
        }

        break;
    default:
        break;
    }

    return out.map((c) => ({...c, nth}));
}

async function resolveTarget(ctx, target, timeout = ctx.timeout) {
    if (target == null) {
        throw new StepError('no target could be read from the step');
    }

    const found = await firstVisible(candidates(ctx, target), timeout);

    if (found == null) {
        throw new StepError(`nothing visible matches ${describeTarget(target)}`);
    }

    ctx.log(`      resolved ${describeTarget(target)} via ${found.how}`);

    return found.locator;
}

async function rememberItem(ctx, locator) {
    const item = locator.locator('xpath=ancestor-or-self::*[@data-test-id="article-item"][1]');

    if (await item.count().catch(() => 0) > 0) {
        ctx.lastItem = item.first();
    }
}

// ---------------------------------------------------------------------------
// Actions
// ---------------------------------------------------------------------------

async function loadRoute(ctx, hash) {
    const url = `${ctx.baseUrl}/${hash.replace(/^\//, '')}`;

    await ctx.page.goto('about:blank');
    await ctx.page.goto(url, {waitUntil: 'domcontentloaded'});

    const username = ctx.page.getByTestId('login-page').getByTestId('username');
    const shell = ctx.page.locator(APP_SHELL);
    const timeout = loginTimeout(ctx.timeout);
    let first = await waitForAny([shell, username], timeout);

    if (first !== -1) {
        await sleep(1000);

        if (await username.isVisible().catch(() => false)) {
            first = 1;
        }
    }

    if (first === 1) {
        ctx.log('    session was logged out; logging in again');
        await fillLoginForm(ctx.page, ctx.creds);
        await username.waitFor({state: 'hidden', timeout});

        if (await waitForAny([shell], timeout) !== 0) {
            throw new StepError('re-login did not reach the app');
        }

        await ctx.page.goto(url, {waitUntil: 'domcontentloaded'});
        await ctx.page.locator(APP_SHELL).first().waitFor({state: 'visible', timeout});
    } else if (first === -1) {
        throw new StepError(`the app did not render at ${url}`);
    }

    await dismissInterruptions(ctx.page, ctx.creds);

    const removed = await removeTestFontStyle(ctx.page);

    if (removed > 0) {
        ctx.log(`    removed ${removed} test font override style element(s)`);
    }

    await waitForFonts(ctx.page);
    await settle(ctx.page);
}

function currentHash(page) {
    const url = page.url();
    const i = url.indexOf('#');

    return i < 0 ? '' : url.slice(i).replace(/\/+$/, '');
}

async function waitMonitoringReady(ctx) {
    const deadline = Date.now() + 90000;
    const selected = ctx.page.getByTestId('monitoring--selected-desk');

    for (;;) {
        await dismissInterruptions(ctx.page, ctx.creds);

        const noBackdrop = await ctx.page.locator('.modal__backdrop').count() === 0;

        if (noBackdrop && await selected.isVisible().catch(() => false)) {
            return;
        }

        if (Date.now() > deadline) {
            throw new StepError('monitoring did not become ready (no desk selector visible)');
        }

        await sleep(500);
    }
}

async function selectDesk(ctx, name) {
    if (!await ctx.page.getByTestId('monitoring--selected-desk').isVisible().catch(() => false)) {
        ctx.log('    not on monitoring; loading it first');
        await loadRoute(ctx, MONITORING_ROUTE);
    }

    await waitMonitoringReady(ctx);

    const dropdown = ctx.page.getByTestId('monitoring--selected-desk');
    const text = (await dropdown.textContent()) ?? '';

    if (!text.toLowerCase().includes(name.toLowerCase())) {
        await dropdown.click();

        const options = ctx.page.getByTestId('monitoring--select-desk-options');
        const found = await firstVisible([
            {how: 'exact button', locator: options.getByRole('button', {name, exact: true})},
            {how: 'button containing text', locator: options.locator('button', {hasText: name})},
        ], ctx.timeout);

        if (found == null) {
            throw new StepError(`desk "${name}" is not in the desk selector`);
        }

        await found.locator.click();
    }

    const deadline = Date.now() + ctx.timeout;

    while (!((await dropdown.textContent()) ?? '').toLowerCase().includes(name.toLowerCase())) {
        if (Date.now() > deadline) {
            throw new StepError(`desk "${name}" did not become the selected desk`);
        }

        await sleep(200);
    }

    ctx.lastDesk = name;
    await settle(ctx.page);
}

async function openItem(ctx, name, desk) {
    if (!await ctx.page.getByTestId('monitoring--selected-desk').isVisible().catch(() => false)) {
        await loadRoute(ctx, MONITORING_ROUTE);
    }

    await waitMonitoringReady(ctx);

    if (desk != null) {
        await selectDesk(ctx, desk);
    }

    // the list is rebuilt after a snapshot restore, so give the item time to show up
    const found = await firstVisible([
        {how: 'data-test-value', locator: ctx.page.locator(`[data-test-id="article-item"][data-test-value="${name.replace(/"/g, '\\"')}"]`)},
        {how: 'item text', locator: ctx.page.getByTestId('article-item').filter({hasText: name})},
    ], Math.max(ctx.timeout, 30000));

    if (found == null) {
        throw new StepError(`article "${name}" is not in the monitoring list${ctx.lastDesk != null ? ` of ${ctx.lastDesk}` : ''}`);
    }

    const item = found.locator;
    const authoring = ctx.page.getByTestId('authoring');

    ctx.lastItem = item;

    try {
        await item.hover();
        await item.getByTestId('context-menu-button').click({timeout: 5000});
        await ctx.page.getByTestId('context-menu').getByRole('button', {name: 'Edit', exact: true}).click({timeout: 5000});
    } catch (e) {
        ctx.log(`    actions menu > Edit failed (${e.message.split('\n')[0]}); falling back to double-click`);
        await ctx.page.keyboard.press('Escape').catch(() => {});
        await item.dblclick();
    }

    await authoring.first().waitFor({state: 'visible', timeout: 30000});
    await ctx.page.getByTestId('authoring-topbar').first().waitFor({state: 'visible', timeout: 30000});
    ctx.prev = authoring.first();
    await settle(ctx.page, 800);
}

async function ensureSelected(ctx, text, role, within) {
    const base = baseFor(ctx, {within});
    const roles = role != null ? [role] : ['tab', 'radio', 'button'];
    const cands = roles.map((r) => ({how: `role ${r}`, locator: base.getByRole(r, {name: text, exact: true})}));

    cands.push({how: 'exact text', locator: base.getByText(text, {exact: true})});

    const found = await firstVisible(cands, ctx.timeout);

    if (found == null) {
        throw new StepError(`no tab, radio or button "${text}" to select`);
    }

    const selected = await found.locator.evaluate((el) => el.getAttribute('aria-selected') === 'true'
        || el.getAttribute('aria-checked') === 'true'
        || el.getAttribute('aria-pressed') === 'true'
        || el.checked === true
        || el.classList.contains('active')
        || el.classList.contains('sd-nav-tabs__tab--active'));

    if (selected) {
        ctx.log(`    "${text}" already selected (${found.how})`);
    } else if (found.how === 'role radio') {
        await found.locator.check({force: true});
    } else {
        await found.locator.click();
    }

    ctx.prev = found.locator;
}

async function choose(ctx, text, within) {
    const base = baseFor(ctx, {within});
    const page = ctx.page;
    const treePopover = page.getByTestId('tree-select-popover');
    const cands = [
        {how: 'tree-select option', locator: treePopover.getByRole('treeitem', {name: text, exact: true})},
        {how: 'role option', locator: base.getByRole('option', {name: text, exact: true})},
        {how: 'role treeitem', locator: base.getByRole('treeitem', {name: text, exact: true})},
        {how: 'role menuitem', locator: base.getByRole('menuitem', {name: text, exact: true})},
        {how: 'native select', locator: base.locator('select').filter({has: page.locator('option', {hasText: exactText(text)})})},
        {how: 'role radio', locator: base.getByRole('radio', {name: text, exact: true})},
        {how: 'role button', locator: base.getByRole('button', {name: text, exact: true})},
        {how: 'exact text', locator: base.getByText(text, {exact: true})},
    ];
    const found = await firstVisible(cands, ctx.timeout);

    if (found == null) {
        throw new StepError(`no visible option "${text}" to choose`);
    }

    ctx.log(`      choosing via ${found.how}`);

    if (found.how === 'native select') {
        await found.locator.selectOption({label: text});
    } else if (found.how === 'role radio') {
        await found.locator.check();
    } else {
        await found.locator.click();

        const entire = treePopover.getByRole('button', {name: 'Choose entire category'});

        if (await entire.isVisible().catch(() => false)) {
            await entire.click();
        }
    }

    ctx.prev = found.locator;
}

async function treeSelect(ctx, target, values) {
    const field = await resolveTarget(ctx, target);

    for (const value of values) {
        const opener = field.getByTestId('open-popover');

        if (await opener.isVisible().catch(() => false)) {
            await opener.click();
        } else {
            await field.click();
        }

        await ctx.page.getByTestId('tree-select-popover').getByTestId('options')
            .getByRole('treeitem', {name: value, exact: true}).click();

        const entire = ctx.page.getByTestId('tree-select-popover').getByRole('button', {name: 'Choose entire category'});

        if (await entire.isVisible().catch(() => false)) {
            await entire.click();
        }
    }

    ctx.prev = field;
}

async function setSwitches(ctx, on, names) {
    for (const name of names) {
        const found = await firstVisible(labelCandidates(ctx, ctx.page, name, 'switch'), ctx.timeout);

        if (found == null) {
            throw new StepError(`no visible switch for "${name}"`);
        }

        const checked = await found.locator.evaluate((el) => el.getAttribute('aria-checked') === 'true' || el.checked === true);

        if (checked !== on) {
            await found.locator.click();
            await sleep(300);
        } else {
            ctx.log(`    switch "${name}" already ${on ? 'on' : 'off'}`);
        }
    }
}

async function setDateTime(ctx, pairs, within) {
    const format = await ctx.page.evaluate(() => window.appConfigLoaded?.view?.dateformat ?? null).catch(() => null)
        ?? 'DD/MM/YYYY';
    const base = baseFor(ctx, {within: within ?? []});

    for (const pair of pairs) {
        const found = await firstVisible([{how: 'css', locator: base.locator(pair.css)}], ctx.timeout);

        if (found == null) {
            throw new StepError(`no visible ${pair.field} input ${pair.css}`);
        }

        const value = pair.field === 'date' ? resolveDateValue(pair.value, format) : String(pair.value);

        ctx.log(`      setting ${pair.field} "${value}"${pair.field === 'date' ? ` (format ${format})` : ''}`);

        // The time field is a native <input type="time">: fill takes HH:MM, while typing lands
        // digits in the wrong segments. The date field is masked: fill shows the text but the
        // component keeps today's date, so it has to be typed.
        const isNativeTime = await found.locator.evaluate((el) => el.type === 'time');

        if (isNativeTime) {
            await found.locator.fill(value);
        } else {
            await found.locator.click();
            await found.locator.clear().catch(() => {});
            await found.locator.pressSequentially(value, {delay: 40});
        }

        if ((await found.locator.inputValue()) !== value) {
            ctx.warn(`${pair.field} field shows "${await found.locator.inputValue()}" instead of "${value}"`);
        }

        // close the date/time picker popup, which otherwise covers the next field
        await ctx.page.keyboard.press('Escape');
        await sleep(200);
    }

    await ctx.page.evaluate(() => document.activeElement?.blur());

    await settle(ctx.page);
}

async function fillTarget(ctx, target, value) {
    const loc = await resolveTarget(ctx, target);
    const editable = await loc.evaluate((el) => el.matches('input, textarea, select, [contenteditable=""], [contenteditable="true"]'));
    let field = loc;

    if (!editable) {
        const inner = await firstVisible([{how: 'textbox inside', locator: loc.getByRole('textbox')}], ctx.timeout);

        if (inner == null) {
            throw new StepError(`no text box inside ${describeTarget(target)}`);
        }

        field = inner.locator;
    }

    // editor3 (Draft.js) sometimes applies only part of a fill; retry until it holds the value
    for (let attempt = 1; attempt <= 5; attempt++) {
        await field.fill(value);
        await sleep(200);

        const current = await field.evaluate((el) => ('value' in el && el.tagName !== 'DIV' ? el.value : el.innerText));

        if (String(current).trim() === value.trim()) {
            break;
        }

        if (attempt === 5) {
            throw new StepError(`field kept "${current}" instead of "${value}"`);
        }
    }

    ctx.prev = field;
}

async function waitAction(ctx, a) {
    let container = null;

    if (a.state === 'hidden') {
        for (const target of a.targets) {
            await candidates(ctx, target)[0].locator.first().waitFor({state: 'hidden'});
        }

        return;
    }

    for (const target of a.targets) {
        const loc = await resolveTarget(ctx, target);

        if (a.state === 'enabled') {
            const deadline = Date.now() + ctx.timeout;

            while (!await loc.isEnabled()) {
                if (Date.now() > deadline) {
                    throw new StepError(`${describeTarget(target)} did not become enabled`);
                }

                await sleep(200);
            }
        }

        container ??= loc;
    }

    for (const t of a.texts) {
        const cands = t.inContainer && container != null
            ? [{how: 'container text', locator: container.filter({hasText: t.text})},
                {how: 'text inside container', locator: container.getByText(t.text)}]
            : [{how: 'text', locator: ctx.page.getByText(t.text)}];
        const found = await firstVisible(cands, ctx.timeout);

        if (found == null) {
            throw new StepError(`text "${t.text}" did not appear${t.inContainer ? ' in the waited element' : ''}`);
        }
    }

    if (container != null) {
        ctx.prev = container;
    }
}

async function genericAction(ctx, a) {
    if (a.reason != null) {
        throw new StepError(`cannot interpret: ${a.reason}`);
    }

    if (a.target == null) {
        throw new StepError('no known step shape and no element named in the step');
    }

    const loc = await resolveTarget(ctx, a.target);

    if (a.verb === 'hover') {
        await loc.hover();
    } else {
        ctx.log(`      generic attempt: clicking ${describeTarget(a.target)}`);
        await loc.click();
    }

    ctx.prev = loc;
}

async function runAction(ctx, a) {
    switch (a.type) {
    case 'noop':
        return;
    case 'goto': {
        const route = parseRoute(a.route);
        const hash = route.kind === 'url' ? null : route.hash;

        if (hash != null && currentHash(ctx.page) === hash.replace(/\/+$/, '')) {
            ctx.log('    already on this route, not reloading');

            return;
        }

        if (route.kind === 'url') {
            await ctx.page.goto(route.url, {waitUntil: 'domcontentloaded'});
            await settle(ctx.page);
        } else {
            await loadRoute(ctx, hash);
        }

        return;
    }
    case 'click':
    case 'dblclick': {
        const loc = await resolveTarget(ctx, a.target);

        const isToggleInput = await loc.evaluate((el) => el.matches('input[type="radio"], input[type="checkbox"]'));

        if (a.type === 'dblclick') {
            await loc.dblclick();
        } else if (isToggleInput) {
            // styled radio/checkbox inputs sit under their label, which intercepts a real click
            await loc.setChecked(true, {force: true});
        } else {
            await loc.click();
        }

        await rememberItem(ctx, loc);
        ctx.prev = loc;
        await sleep(150);

        return;
    }
    case 'hover': {
        const loc = await resolveTarget(ctx, a.target);

        await loc.hover();
        await rememberItem(ctx, loc);
        ctx.prev = loc;
        await sleep(250);

        return;
    }
    case 'check': {
        const loc = await resolveTarget(ctx, a.target);

        try {
            const isInput = await loc.evaluate((el) => el.tagName === 'INPUT');

            // styled inputs sit under their label, which intercepts a real click
            await loc.setChecked(a.on, isInput ? {force: true} : {});
        } catch (e) {
            ctx.log(`      setChecked failed (${e.message.split('\n')[0]}); clicking instead`);
            await loc.click();
        }

        await rememberItem(ctx, loc);
        ctx.prev = loc;

        return;
    }
    case 'fill':
        return fillTarget(ctx, a.target, a.value);
    case 'press':
        await ctx.page.keyboard.press(a.key);
        await sleep(150);

        return;
    case 'wait':
        return waitAction(ctx, a);
    case 'settle':
        return settle(ctx.page, 600);
    case 'sleep':
        return sleep(a.ms);
    case 'waitImages': {
        await ctx.page.waitForFunction(() => [...document.images]
            .filter((img) => img.offsetParent != null)
            .every((img) => img.complete), null, {timeout: Math.max(ctx.timeout, 30000)});

        const broken = await ctx.page.evaluate(() => [...document.images]
            .filter((img) => img.offsetParent != null && img.naturalWidth === 0).length);

        if (broken > 0) {
            ctx.warn(`${broken} visible image(s) failed to load`);
        }

        return;
    }
    case 'selectDesk':
        return selectDesk(ctx, a.name);
    case 'openItem':
        return openItem(ctx, a.name, a.desk);
    case 'openSendPublish': {
        const button = await resolveTarget(ctx, {kind: 'css', css: '[data-test-id="authoring"] [data-test-id="open-send-publish-pane"]'});

        await button.click();

        const panel = ctx.page.getByTestId('interactive-actions-panel').first();

        await panel.waitFor({state: 'visible'});

        if (a.tab != null) {
            await ensureSelected(ctx, a.tab, 'tab', [{kind: 'css', css: '[data-test-id="interactive-actions-panel"] [data-test-id="tabs"]'}]);
        }

        ctx.prev = panel;
        await settle(ctx.page);

        return;
    }
    case 'openViewSwitcher': {
        const toggle = await resolveTarget(ctx, {kind: 'alias', name: 'view switcher'});

        await toggle.click();

        const menu = ctx.page.locator('.dropdown:has(> button.dropdown__toggle[aria-label$=" View"]) > .dropdown__menu');
        const found = await firstVisible([{how: 'menu', locator: menu}, {how: 'option', locator: ctx.page.getByRole('button', {name: 'List view', exact: true})}], ctx.timeout);

        if (found == null) {
            throw new StepError('the view switcher menu did not open');
        }

        ctx.prev = found.how === 'menu' ? found.locator : toggle;

        return;
    }
    case 'openTarget': {
        const loc = await resolveTarget(ctx, a.target);
        const opener = loc.getByTestId('open-popover');

        if (await opener.isVisible().catch(() => false)) {
            await opener.click();
        } else {
            await loc.click();
        }

        ctx.prev = loc;
        await sleep(200);

        return;
    }
    case 'mouseAway':
        try {
            await ctx.page.mouse.move(-10, -10);
        } catch {
            const vp = ctx.page.viewportSize();

            await ctx.page.mouse.move(vp.width - 1, 0);
        }

        await sleep(250);

        return;
    case 'scroll': {
        const loc = await resolveTarget(ctx, a.target);

        await loc.scrollIntoViewIfNeeded();
        ctx.prev = loc;

        return;
    }
    case 'ensureSelected':
        return ensureSelected(ctx, a.text, a.role, a.within ?? []);
    case 'choose':
        return choose(ctx, a.text, a.within ?? []);
    case 'treeSelect':
        return treeSelect(ctx, a.target, a.values);
    case 'switches':
        return setSwitches(ctx, a.on, a.names);
    case 'setDateTime':
        return setDateTime(ctx, a.pairs, a.within);
    case 'ifNotText': {
        const loc = await resolveTarget(ctx, a.target);
        const text = ((await loc.innerText()) ?? '').toLowerCase();

        if (text.includes(String(a.expected).toLowerCase())) {
            ctx.log(`    condition not met ("${a.expected}" already shown); skipping nested actions`);

            return;
        }

        ctx.prev = loc;

        for (const inner of a.then) {
            await runOne(ctx, inner, '    ');
        }

        return;
    }
    case 'evaluate':
        await ctx.page.evaluate(a.script);

        return;
    case 'generic':
        return genericAction(ctx, a);
    default:
        throw new StepError(`unsupported action type ${a.type}`);
    }
}

async function runOne(ctx, a, indent = '  ') {
    const known = a.shape !== 'generic';
    const started = Date.now();

    ctx.log(`${indent}-> [${known ? a.shape : 'NO KNOWN SHAPE'}${a.optional ? ', optional' : ''}] ${describeAction(a)}`);

    if (!known) {
        ctx.warn(`step "${a.source ?? a.words}" matched no known shape; trying a generic interpretation`);
    }

    try {
        await runAction(ctx, a);
        ctx.log(`${indent}   ok (${Date.now() - started} ms)`);
    } catch (e) {
        const msg = e.message.split('\n')[0];

        if (a.optional) {
            ctx.warn(`optional step failed and was skipped: ${msg}`);
            ctx.log(`${indent}   optional step failed, continuing: ${msg}`);

            return;
        }

        ctx.log(`${indent}   FAILED: ${msg}`);
        throw e;
    }
}

async function runSteps(ctx, steps, label) {
    const parsed = parseSteps(steps);

    for (let i = 0; i < parsed.length; i++) {
        ctx.log(`  ${label} ${i + 1}/${parsed.length}: ${parsed[i].raw}`);

        for (const a of parsed[i].actions) {
            await runOne(ctx, a, '    ');
        }
    }
}

// ---------------------------------------------------------------------------
// Capture
// ---------------------------------------------------------------------------

async function boxesFor(ctx, target, {timeout}) {
    if (target.kind === 'alias' && [].concat(ALIASES[target.name]?.css ?? []).length > 1) {
        const boxes = [];

        for (const css of ALIASES[target.name].css) {
            const found = await firstVisible([{how: 'alias part', locator: ctx.page.locator(css)}], timeout);

            if (found != null) {
                boxes.push({locator: found.locator, box: await waitStable(found.locator)});
            }
        }

        return boxes;
    }

    const found = await firstVisible(candidates(ctx, target), timeout);

    if (found == null) {
        return [];
    }

    return [{locator: found.locator, box: await waitStable(found.locator)}];
}

function union(boxes) {
    const x1 = Math.min(...boxes.map((b) => b.x));
    const y1 = Math.min(...boxes.map((b) => b.y));
    const x2 = Math.max(...boxes.map((b) => b.x + b.width));
    const y2 = Math.max(...boxes.map((b) => b.y + b.height));

    return {x: x1, y: y1, width: x2 - x1, height: y2 - y1};
}

async function computeClip(ctx, crop, entry, vp) {
    if (crop.kind === 'full') {
        return {clip: {x: 0, y: 0, width: vp.width, height: vp.height}, isElement: false};
    }

    if (crop.kind === 'region') {
        const r = crop.region;

        return {clip: {x: r.x ?? 0, y: r.y ?? 0, width: r.width, height: r.height}, isElement: false};
    }

    const [mainTarget, ...extra] = crop.targets;
    const mainLoc = await resolveTarget(ctx, mainTarget);

    await mainLoc.scrollIntoViewIfNeeded().catch(() => {});

    const mainBoxes = await boxesFor(ctx, mainTarget, {timeout: ctx.timeout});

    if (mainBoxes.length === 0 || mainBoxes[0].box == null) {
        throw new StepError(`crop element ${describeTarget(mainTarget)} has no box`);
    }

    const boxes = mainBoxes.map((b) => b.box).filter(Boolean);

    // dialogs and full-height side panels are allowed to be portrait crops
    const isDialog = await mainLoc.evaluate((el) => el.closest('[role="dialog"], .modal, .p-dialog, [data-test-id="modal-confirm"]') != null)
        .catch(() => false);
    const isSidePanel = boxes[0] != null && boxes[0].height >= 0.8 * vp.height;

    for (const t of extra) {
        const more = await boxesFor(ctx, t, {timeout: 3000});

        if (more.length === 0) {
            ctx.warn(`crop part ${describeTarget(t)} not found; cropping without it`);
        }

        boxes.push(...more.map((b) => b.box).filter(Boolean));
    }

    const pad = Number(entry.padding ?? 16);
    const exp = crop.expand ?? {};
    let r = union(boxes);

    // clipAbove: end the crop at the top of an overlay that sits on the element's lower edge
    // (for example the opened-articles bar over the bottom of a side panel)
    for (const sel of [].concat(crop.clipAbove ?? [])) {
        const over = await boxesFor(ctx, selectorTarget(sel), {timeout: 2000});

        for (const {box} of over) {
            if (box != null && box.y > r.y && box.y < r.y + r.height
                && box.x < r.x + r.width && box.x + box.width > r.x) {
                r.height = box.y - r.y;
            }
        }
    }

    if (crop.maxHeight != null) {
        r.height = Math.min(r.height, crop.maxHeight);
    }

    r = {
        x: r.x - pad - (exp.left ?? 0),
        y: r.y - pad - (exp.top ?? 0),
        width: r.width + 2 * pad + (exp.left ?? 0) + (exp.right ?? 0),
        height: r.height + 2 * pad + (exp.top ?? 0) + (exp.bottom ?? 0),
    };

    const x1 = Math.max(0, Math.floor(r.x));
    const y1 = Math.max(0, Math.floor(r.y));
    const x2 = Math.min(vp.width, Math.ceil(r.x + r.width));
    const y2 = Math.min(vp.height, Math.ceil(r.y + r.height));

    if (x2 - x1 < 2 || y2 - y1 < 2) {
        throw new StepError('crop region is empty after clamping to the viewport');
    }

    return {clip: {x: x1, y: y1, width: x2 - x1, height: y2 - y1}, isElement: true, portraitOk: isDialog || isSidePanel};
}

async function computeHighlights(ctx, entry, clip) {
    const hl = parseHighlight(entry.highlight, entry.highlightStyle ?? null);
    const out = [];

    for (const note of hl.notes) {
        ctx.log(`  highlight: ${note}`);
    }

    for (const item of hl.items) {
        if (item.target == null) {
            ctx.warn(`highlight "${item.raw}" could not be interpreted; skipped`);
            continue;
        }

        const boxes = [];

        for (const part of item.target.kind === 'union' ? item.target.parts : [item.target]) {
            boxes.push(...await boxesFor(ctx, part, {timeout: 3000}));
        }

        if (boxes.length === 0) {
            ctx.warn(`highlight "${item.raw}" (${describeTarget(item.target)}) not found; skipped`);
            continue;
        }

        const b = union(boxes.map((x) => x.box).filter(Boolean));
        const x1 = Math.max(b.x, clip.x);
        const y1 = Math.max(b.y, clip.y);
        const x2 = Math.min(b.x + b.width, clip.x + clip.width);
        const y2 = Math.min(b.y + b.height, clip.y + clip.height);

        if (x2 <= x1 || y2 <= y1) {
            ctx.warn(`highlight "${item.raw}" is outside the crop; skipped`);
            continue;
        }

        const box = [
            Math.round((x1 - clip.x) * DPR),
            Math.round((y1 - clip.y) * DPR),
            Math.round((x2 - x1) * DPR),
            Math.round((y2 - y1) * DPR),
        ];

        // style.py puts a badge on the top-left corner of its box unless the entry gives an
        // explicit centre. badgeAnchor "above" / "below" centres the badge just outside the
        // control; "rows" picks above for controls in the upper half of the crop and below for
        // the lower half, which suits a two-row toolbar. "top-right" moves the corner instead.
        // The anchor applies to the badge of a callout too; its outline keeps the full box.
        // An array gives one anchor per highlight item, in highlight order (null keeps the corner).
        let center = null;
        let badgeBox = box;
        const anchor = Array.isArray(entry.badgeAnchor) ? entry.badgeAnchor[item.position - 1] : entry.badgeAnchor;
        const numbered = hl.style === 'badge' || hl.style === 'callout';

        if (numbered && (anchor === 'above' || anchor === 'below' || anchor === 'rows')) {
            const midY = (y1 + y2) / 2;
            const above = anchor === 'above' || (anchor === 'rows' && midY < clip.y + clip.height / 2);
            const cx = (x1 + x2) / 2;
            const cy = above ? y1 - BADGE_GAP - BADGE_OUTER : y2 + BADGE_GAP + BADGE_OUTER;

            center = [Math.round((cx - clip.x) * DPR), Math.round((cy - clip.y) * DPR)];
        } else if (numbered && anchor === 'top-right') {
            badgeBox = [box[0] + box[2] - 2, box[1], 2, box[3]];
        }

        // "callout" is a numbered outline: style.py draws it as an outline plus a badge on the same box
        if (hl.style === 'callout') {
            const badge = {box: badgeBox, label: String(item.position), style: 'badge'};

            if (center != null) {
                badge.center = center;
            }

            out.push({box, label: null, style: 'outline'});
            out.push(badge);
        } else {
            const entryOut = {box: hl.style === 'badge' ? badgeBox : box, label: hl.style === 'badge' ? String(item.position) : null, style: hl.style};

            if (center != null) {
                entryOut.center = center;
            }

            out.push(entryOut);
        }

        ctx.log(`  highlight ${item.position}: "${item.raw}" -> [${out[out.length - 1].box.join(', ')}]`);
    }

    if (hl.items.length > 0 && out.length === 0) {
        ctx.warn('no highlight could be resolved; writing an empty list');
    }

    warnBadgeOverlaps(ctx, out);

    return out;
}

// style.py badge size (BADGE_RADIUS + BADGE_RING) and the gap kept between a badge and its control, CSS px
const BADGE_OUTER = 16;
const BADGE_GAP = 4;

function warnBadgeOverlaps(ctx, highlights) {
    const r = BADGE_OUTER * DPR;
    const badges = highlights.filter((h) => h.style === 'badge' && h.center != null);
    const controls = highlights.map((h) => h.box);

    for (let i = 0; i < badges.length; i++) {
        const [cx, cy] = badges[i].center;

        for (let j = i + 1; j < badges.length; j++) {
            const [ox, oy] = badges[j].center;

            if (Math.hypot(cx - ox, cy - oy) < 2 * r) {
                ctx.warn(`badges ${badges[i].label} and ${badges[j].label} overlap`);
            }
        }

        for (const [bx, by, bw, bh] of controls) {
            const nx = Math.max(bx, Math.min(cx, bx + bw));
            const ny = Math.max(by, Math.min(cy, by + bh));

            if (Math.hypot(cx - nx, cy - ny) < r) {
                ctx.warn(`badge ${badges[i].label} overlaps a highlighted control`);
                break;
            }
        }
    }
}

async function capture(ctx, shot, outDir) {
    const {entry} = shot;
    const vp = ctx.page.viewportSize();
    const crop = parseCrop(entry.crop);

    for (const note of crop.notes) {
        ctx.log(`  crop: ${note}`);
    }

    await waitForNoLoaders(ctx);
    await removeTestFontStyle(ctx.page);
    await waitForFonts(ctx.page);

    const {clip, isElement, portraitOk} = await computeClip(ctx, crop, entry, vp);

    // Shots are shown at their CSS size on the page, so a narrow portrait strip renders tiny.
    if (clip.height > 1.3 * clip.width && !portraitOk && entry.allowPortrait !== true) {
        ctx.warn(`crop is ${clip.width}x${clip.height} CSS px, taller than 1.3x its width; expand it to the right or capture a region so it reads as landscape or square`);
    }
    const highlights = await computeHighlights(ctx, entry, clip);
    const masks = [];

    for (const m of [].concat(entry.mask ?? [])) {
        const found = await firstVisible(candidates(ctx, selectorTarget(m)), 3000);

        if (found == null) {
            ctx.warn(`mask "${m}" not found; nothing masked for it`);
        } else {
            masks.push(found.locator);
        }
    }

    await waitForFonts(ctx.page);

    const dir = path.join(outDir, shot.page);

    fs.mkdirSync(dir, {recursive: true});

    const png = path.join(dir, `${shot.shot}.png`);

    await ctx.page.screenshot({
        path: png,
        clip,
        animations: 'disabled',
        caret: 'hide',
        scale: 'device',
        mask: masks,
        maskColor: entry.maskColor ?? '#D9D9D9',
    });

    let preset = 'default';

    if (crop.kind === 'full') {
        preset = 'wide';
    } else if (isElement && clip.width < 0.6 * vp.width) {
        preset = 'dialog';
    }

    fs.writeFileSync(path.join(dir, `${shot.shot}.highlights.json`), `${JSON.stringify(highlights, null, 2)}\n`);
    fs.writeFileSync(path.join(dir, `${shot.shot}.meta.json`), `${JSON.stringify({preset}, null, 2)}\n`);

    ctx.log(`  saved ${png} (${clip.width}x${clip.height} CSS px at ${DPR}x, preset ${preset}, ${highlights.length} highlight(s))`);
}

// ---------------------------------------------------------------------------
// Run
// ---------------------------------------------------------------------------

async function restoreSnapshot(apiUrl, name, log) {
    log(`restoring database snapshot "${name}" via ${apiUrl}/restore_record`);

    const res = await fetch(`${apiUrl}/restore_record`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({name}),
        signal: AbortSignal.timeout(180000),
    });

    if (!res.ok) {
        throw new Error(`restore_record answered ${res.status}: ${(await res.text()).slice(0, 300)}`);
    }
}

async function prepareStorage(session, entry, baseUrl) {
    const page = session.page;

    if (!page.url().startsWith(baseUrl)) {
        await page.goto(`${baseUrl}/`, {waitUntil: 'domcontentloaded'});
    }

    await page.evaluate(({appConfig, clearPrefixes}) => {
        if (appConfig != null) {
            localStorage.setItem('TEST_APP_CONFIG', JSON.stringify(appConfig));
        } else {
            localStorage.removeItem('TEST_APP_CONFIG');
        }

        for (const prefix of clearPrefixes) {
            for (const key of Object.keys(localStorage)) {
                if (key.startsWith(prefix)) {
                    localStorage.removeItem(key);
                }
            }
        }
    }, {appConfig: entry.appConfig ?? null, clearPrefixes: [].concat(entry.clearLocalStorage ?? [])});
}

async function runShot(shot, sessions, opts) {
    const {entry} = shot;
    const lines = [];
    const warnings = [];
    const log = (line) => {
        lines.push(line);
        process.stdout.write(`${line}\n`);
    };
    const warn = (msg) => {
        warnings.push(msg);
        log(`  WARN ${msg}`);
    };

    log(`\n=== ${shot.page}/${shot.shot} (${shot.manifest})`);

    if (entry.skip != null && entry.skip !== false) {
        const reason = typeof entry.skip === 'string' ? entry.skip : 'skipped in the manifest';

        log(`  skipped: ${reason}`);

        return {status: 'skipped', reason};
    }

    let session = null;
    let mocks = [];

    try {
        if (entry.restore != null && entry.restore !== false) {
            const name = entry.restore === true ? opts.snapshot : String(entry.restore);

            await restoreSnapshot(opts.apiUrl, name, log);
            log('  restore invalidates sessions; logging in again');
            await sessions.closeAll();
        }

        session = await sessions.get(entry.user, log);
        session.sink = [];

        const vp = entry.viewport != null ? parseViewport(entry.viewport) : DEFAULT_VIEWPORT;

        await session.page.setViewportSize(vp);

        const ctx = {
            page: session.page,
            creds: session.creds,
            baseUrl: opts.baseUrl,
            timeout: opts.timeout,
            prev: null,
            lastItem: null,
            lastDesk: null,
            log,
            warn,
        };

        await prepareStorage(session, entry, opts.baseUrl);
        mocks = await installRouteMocks(session.page, entry.mockRoutes, log);

        const route = parseRoute(entry.route);

        if (route.warning != null) {
            warn(route.warning);
        }

        log(`  route ${route.kind === 'url' ? route.url : route.hash}, viewport ${vp.width}x${vp.height}`);

        if (route.kind === 'url') {
            await session.page.goto(route.url, {waitUntil: 'domcontentloaded'});
            await settle(session.page);
        } else {
            await loadRoute(ctx, route.hash);
        }

        if (entry.keepOpenItems !== true) {
            await closeOpenItems(ctx);
        }

        try {
            await runSteps(ctx, entry.steps ?? [], 'step');
            await settle(ctx.page);
            await capture(ctx, shot, opts.out);
        } finally {
            if (Array.isArray(entry.cleanup) && entry.cleanup.length > 0) {
                try {
                    await runSteps(ctx, entry.cleanup, 'cleanup');
                } catch (e) {
                    warn(`cleanup failed: ${e.message.split('\n')[0]}`);
                }
            }
        }

        return {status: 'ok', reason: warnings.length > 0 ? `${warnings.length} warning(s): ${warnings[0]}` : ''};
    } catch (e) {
        const reason = e.message.split('\n')[0];

        log(`  FAILED: ${reason}`);

        const dir = path.join(opts.out, '_failed', shot.page);

        fs.mkdirSync(dir, {recursive: true});

        const debugPage = session?.page ?? e.debugPage;

        if (debugPage != null) {
            await debugPage.screenshot({path: path.join(dir, `${shot.shot}.png`), fullPage: true}).catch(() => {});
        }

        fs.writeFileSync(path.join(dir, `${shot.shot}.log`), [
            `shot: ${shot.page}/${shot.shot}`,
            `manifest: ${shot.manifest}`,
            `url: ${session?.page.url() ?? '-'}`,
            `error: ${e.stack ?? e.message}`,
            '',
            '--- steps ---',
            ...lines,
            '',
            '--- browser console ---',
            ...(session?.sink ?? e.debugSink ?? []),
            '',
        ].join('\n'));

        await e.debugContext?.close().catch(() => {});

        return {status: 'FAILED', reason};
    } finally {
        await removeRouteMocks(session?.page, mocks);
    }
}

/**
 * `mockRoutes`: [{url, method?, status?, json?, body?, contentType?}]. `url` is a Playwright glob such as
 * `**\/api/ai_providers/*\/models`. Matching requests (of `method`, when given) are answered with `json`
 * (serialised) or `body` instead of reaching the server, for the whole shot including cleanup.
 */
async function installRouteMocks(page, specs, log) {
    const installed = [];

    for (const spec of [].concat(specs ?? [])) {
        const handler = (route) => {
            if (spec.method != null && route.request().method() !== String(spec.method).toUpperCase()) {
                return route.fallback();
            }

            return route.fulfill({
                status: spec.status ?? 200,
                contentType: spec.json != null ? 'application/json' : (spec.contentType ?? 'text/plain'),
                body: spec.json != null ? JSON.stringify(spec.json) : (spec.body ?? ''),
            });
        };

        await page.route(spec.url, handler);
        installed.push({url: spec.url, handler});
        log(`  mock ${spec.method ?? 'any'} ${spec.url} -> ${spec.status ?? 200}`);
    }

    return installed;
}

async function removeRouteMocks(page, installed) {
    for (const {url, handler} of installed ?? []) {
        await page?.unroute(url, handler).catch(() => {});
    }
}

function printSummary(results) {
    const rows = [['page', 'shot', 'status', 'reason'], ...results.map((r) => [r.page, r.shot, r.status, r.reason])];
    const widths = [0, 1, 2].map((i) => Math.max(...rows.map((r) => r[i].length)));
    const fmt = (r) => [r[0].padEnd(widths[0]), r[1].padEnd(widths[1]), r[2].padEnd(widths[2]), r[3].slice(0, 110)].join('  ');

    process.stdout.write(`\n${fmt(rows[0])}\n${widths.map((w) => '-'.repeat(w)).join('  ')}  ------\n`);

    for (const r of rows.slice(1)) {
        process.stdout.write(`${fmt(r)}\n`);
    }

    const failed = results.filter((r) => r.status === 'FAILED').length;
    const skipped = results.filter((r) => r.status === 'skipped').length;

    process.stdout.write(`\n${results.length - failed - skipped} ok, ${failed} failed, ${skipped} skipped\n`);
}

function dryRun(shots) {
    let unknown = 0;

    for (const shot of shots) {
        const {entry} = shot;
        const route = parseRoute(entry.route);

        process.stdout.write(`\n=== ${shot.page}/${shot.shot}  user=${entry.user ?? 'admin'}  route=${route.kind === 'url' ? route.url : route.hash}${route.warning ? `  WARN ${route.warning}` : ''}\n`);

        for (const step of parseSteps(entry.steps)) {
            process.stdout.write(`  step: ${step.raw}\n`);

            for (const a of step.actions) {
                const nested = a.type === 'ifNotText' ? a.then : [];

                if (a.shape === 'generic' || nested.some((n) => n.shape === 'generic')) {
                    unknown++;
                }

                process.stdout.write(`    [${a.shape}${a.optional ? ', optional' : ''}] ${describeAction(a)}\n`);
            }
        }

        const crop = parseCrop(entry.crop);

        process.stdout.write(`  crop: ${crop.kind} ${crop.targets.map(describeTarget).join(' + ')}${Object.keys(crop.expand ?? {}).length ? ` expand ${JSON.stringify(crop.expand)}` : ''}${crop.maxHeight ? ` maxHeight ${crop.maxHeight}` : ''}${crop.notes.length ? `  (${crop.notes.join('; ')})` : ''}\n`);

        const hl = parseHighlight(entry.highlight, entry.highlightStyle ?? null);

        process.stdout.write(`  highlight (${hl.style}): ${hl.items.map((i) => `${i.position}=${i.target ? describeTarget(i.target) : 'UNREADABLE'}`).join(' | ') || 'none'}\n`);
    }

    process.stdout.write(`\n${shots.length} shot(s), ${unknown} step clause(s) with no known shape\n`);
}

async function main() {
    const opts = parseCli(process.argv.slice(2));
    const shots = loadShots(opts.manifests, opts.only);

    if (shots.length === 0) {
        process.stderr.write(`no shots matched in ${opts.manifests}${opts.only ? ` for --only ${opts.only.join(',')}` : ''}\n`);
        process.exit(1);
    }

    if (opts.dryRun) {
        dryRun(shots);

        return 0;
    }

    const {chromium, selectors} = loadPlaywright(opts.playwrightFrom);

    selectors.setTestIdAttribute('data-test-id');

    const users = loadUsers(opts.usersFile);
    const log = (line) => process.stdout.write(`${line}\n`);

    fs.mkdirSync(opts.out, {recursive: true});

    if (opts.restore) {
        await restoreSnapshot(opts.apiUrl, opts.snapshot, log);
    }

    const browser = await chromium.launch({
        headless: !opts.headed,
        slowMo: opts.slowMo || undefined,
        executablePath: opts.executablePath ?? undefined,
    });
    const sessions = new Sessions(browser, opts, users);
    const results = [];

    try {
        for (const shot of shots) {
            const r = await runShot(shot, sessions, opts);

            results.push({page: shot.page, shot: shot.shot, ...r});
        }
    } finally {
        await sessions.closeAll();
        await browser.close();
    }

    printSummary(results);

    return results.some((r) => r.status === 'FAILED') ? 1 : 0;
}

main().then((code) => {
    process.exitCode = code;
}, (e) => {
    process.stderr.write(`${e.stack ?? e.message}\n`);
    process.exitCode = 1;
});
