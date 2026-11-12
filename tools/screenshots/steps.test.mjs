import {test} from 'node:test';
import assert from 'node:assert/strict';
import {
    parseCrop,
    parseHighlight,
    parseRoute,
    parseStep,
    parseSteps,
    parseViewport,
    resolveDateValue,
    selectorTarget,
    shotId,
    splitClauses,
    tokenize,
} from './steps.mjs';

const shapes = (raw, prev) => parseStep(raw, prev).map((a) => a.shape);

test('tokenize keeps bracket selectors whole, including spaces inside quotes', () => {
    const tok = tokenize('wait for [data-test-id="monitoring-filtering-item--Marked for me"] to be visible');

    assert.deepEqual(tok.sel, ['[data-test-id="monitoring-filtering-item--Marked for me"]']);
    assert.equal(tok.template, 'wait for «S0» to be visible');
});

test('tokenize merges adjacent selectors into one descendant selector', () => {
    const tok = tokenize('Hover [data-test-id="a"][data-test-value="x y"] [data-test-id="b"] now');

    assert.equal(tok.sel[tok.sel.length - 1], '[data-test-id="a"][data-test-value="x y"] [data-test-id="b"]');
});

test('tokenize ignores apostrophes inside words but reads quoted strings', () => {
    const tok = tokenize('This changes the user\'s preference, click \'Show all\'');

    assert.deepEqual(tok.quotes, ['Show all']);
});

test('tokenize reads bare CSS words, "containing" and attribute phrases', () => {
    assert.deepEqual(
        tokenize('Click the last button in the header: button.sd-navbtn containing i.icon-switches').sel.at(-1),
        'button.sd-navbtn:has(i.icon-switches)',
    );
    assert.deepEqual(tokenize('Type \'election\' in the input with name="slugline"').sel, ['input[name="slugline"]']);
    assert.deepEqual(tokenize('see send-publish-button.png, e.g. this').sel, []);
});

test('tokenize extracts CSS from parentheses and routes', () => {
    const tok = tokenize('Open #/master-desk and wait for the desk cards (.sd-grid-list .sd-board) to render');

    assert.deepEqual(tok.routes, ['#/master-desk']);
    assert.ok(tok.sel.includes('.sd-grid-list .sd-board'));
});

test('splitClauses splits only before verbs', () => {
    assert.deepEqual(splitClauses('open the view switcher and click X'), ['open the view switcher', 'click X']);
    assert.deepEqual(splitClauses('wait for A and the B to appear'), ['wait for A and the B to appear']);
    assert.deepEqual(splitClauses('Hover A, click its B, click C'), ['Hover A', 'click its B', 'click C']);
});

test('route + wait, hover with trailing purpose clause', () => {
    const [go, wait] = parseStep('Open #/workspace/monitoring and wait for [data-test-id="workspace-navigation"] to be visible');

    assert.equal(go.type, 'goto');
    assert.equal(go.route, '#/workspace/monitoring');
    assert.equal(wait.type, 'wait');
    assert.equal(wait.targets[0].css, '[data-test-id="workspace-navigation"]');

    const [hover] = parseStep('Hover [data-test-id="open-send-publish-pane"] so the \'Send to / Publish\' tooltip shows');

    assert.equal(hover.type, 'hover');
    assert.equal(hover.target.css, '[data-test-id="open-send-publish-pane"]');
});

test('select desk, open item, open send/publish panel', () => {
    assert.deepEqual(shapes('Open #/workspace/monitoring, select desk \'Sports\' and open \'story 2\' for editing'), ['goto', 'select-desk', 'open-item']);

    const [, open] = parseStep('Open #/workspace/monitoring and open \'test sports story\' with the item actions menu > \'Edit\'');

    assert.equal(open.type, 'openItem');
    assert.equal(open.name, 'test sports story');

    const [item, panel] = parseStep('Open \'test sports story\' for editing and open the Send to / Publish panel on the \'Publish\' tab');

    assert.equal(item.type, 'openItem');
    assert.equal(panel.type, 'openSendPublish');
    assert.equal(panel.tab, 'Publish');
    assert.equal(parseStep('Select desk \'Sports\' via [data-test-id="x"] then the \'Sports\' button in [data-test-id="y"]')[0].type, 'selectDesk');
});

test('scoped clicks: "its", "inside that item", leading "In [x]" and role=tab', () => {
    const [hover, click, edit] = parseStep('Hover [data-test-id="article-item"] with text \'story 2\', click its [data-test-id="context-menu-button"], click \'Edit\' in [data-test-id="context-menu"]');

    assert.equal(hover.target.hasText, 'story 2');
    assert.equal(click.target.scopePrev, true);
    assert.equal(edit.target.kind, 'label');
    assert.equal(edit.target.text, 'Edit');
    assert.equal(edit.target.within[0].css, '[data-test-id="context-menu"]');

    const [tab] = parseStep('In [data-test-id="panel"] click the tab with role=tab name \'Send to\' inside [data-test-id="tabs"]');

    assert.equal(tab.type, 'click');
    assert.deepEqual({role: tab.target.role, name: tab.target.name}, {role: 'tab', name: 'Send to'});
    assert.deepEqual(tab.target.within.map((w) => w.css), ['[data-test-id="panel"]', '[data-test-id="tabs"]']);

    const [radio] = parseStep('In [data-test-id="stage-select"] check the radio \'Incoming Stage\'');

    assert.equal(radio.type, 'check');
    assert.equal(radio.target.role, 'radio');
});

test('conditional step and "do the same for"', () => {
    const [cond] = parseStep('if [data-test-id="monitoring--selected-desk"] does not show SPORTS, click it and click the button \'Sports\' inside [data-test-id="opts"]');

    assert.equal(cond.type, 'ifNotText');
    assert.equal(cond.expected, 'SPORTS');
    assert.deepEqual(cond.then.map((a) => a.type), ['click', 'click']);
    assert.equal(cond.then[0].target.kind, 'prev');

    const prev = 'hover [data-test-id="article-item"][data-test-value="test sports story"] [data-test-id="t"] and check its [data-test-id="c"]';
    const repeat = parseStep('do the same for \'story 2\'', prev);

    assert.deepEqual(repeat.map((a) => a.shape), ['repeat:hover', 'repeat:check']);

    const grouped = parseStep('do the same for \'B\'', 'hover [data-test-id="monitoring-group"][data-test-value="Sports"] [data-test-id="article-item"][data-test-value="A"] [data-test-id="t"]');

    assert.match(grouped[0].target.css, /data-test-value="Sports"\] \[data-test-id="article-item"\]\[data-test-value="B"\]/);
    assert.match(repeat[0].target.css, /data-test-value="story 2"/);
});

test('fill, set date/time, switches, choose, ensure-selected, notes, optional', () => {
    const [fill] = parseStep('Change the headline in [data-test-id="field--headline"] (role textbox) to \'new\'');

    assert.deepEqual({type: fill.type, css: fill.target.css, value: fill.value}, {type: 'fill', css: '[data-test-id="field--headline"]', value: 'new'});

    const [set] = parseStep('In [data-test-id="publish-schedule"] set the date to tomorrow and the time to 10:00');

    assert.equal(set.type, 'setDateTime');
    assert.deepEqual(set.pairs.map((p) => [p.field, p.value]), [['date', 'tomorrow'], ['time', '10:00']]);
    assert.equal(set.within[0].css, '[data-test-id="publish-schedule"]');

    const [sw] = parseStep('Turn on the switches for Politics and Sports (the \'Show all\' switch turns off automatically)');

    assert.deepEqual(sw.names, ['Politics', 'Sports']);

    const [, choose] = parseStep('Open [data-test-id="destination-select"] and choose \'Education\'');

    assert.equal(choose.type, 'choose');
    assert.equal(choose.text, 'Education');

    const [ensure] = parseStep('Make sure the \'Publish\' tab is active in [data-test-id="tabs"] (it is the default)');

    assert.equal(ensure.type, 'ensureSelected');
    assert.equal(ensure.role, 'tab');
    assert.equal(parseStep('Do not click Send')[0].type, 'noop');

    const [opt] = parseStep('Optionally pick \'Europe/London\' in the Time zone select');

    assert.equal(opt.optional, true);
    assert.equal(opt.text, 'Europe/London');
});

test('view switcher, mouse away, waits for texts and images, press', () => {
    assert.deepEqual(shapes('open the view switcher and click \'Compact View\''), ['open-view-switcher', 'click']);
    assert.equal(parseStep('in the second toolbar row click the view switcher toggle: the button with aria-label \'List View\'')[0].type, 'openViewSwitcher');
    assert.equal(parseStep('move the mouse away from the list so no row is hovered')[0].type, 'mouseAway');
    assert.equal(parseStep('wait for all thumbnails to finish loading (img elements complete)')[0].type, 'waitImages');
    assert.equal(parseStep('press Escape')[0].key, 'Escape');
    assert.equal(parseStep('Wait until [data-test-id="save"] is enabled (edit registered)')[0].state, 'enabled');

    const [w] = parseStep('wait for [data-test-id="bar"] to show \'2 Items selected\' and [data-test-id="inline"]');

    assert.equal(w.targets.length, 2);
    assert.deepEqual(w.texts, [{text: '2 Items selected', inContainer: true}]);

    const [w2] = parseStep('wait for .sd-kanban-list to be visible and the \'Columns:\' input to appear');

    assert.deepEqual(w2.texts, [{text: 'Columns:', inContainer: false}]);
});

test('unknown shapes become generic, never dropped', () => {
    const [a] = parseStep('in [data-test-id="filter-contentProfile"] select two profiles');

    assert.equal(a.shape, 'generic');
    assert.match(a.reason, /no quoted values/);
    assert.equal(parseStep('Frobnicate the widget')[0].shape, 'generic');
});

test('structured steps pass through', () => {
    const [s] = parseSteps([{action: 'click', target: 'save', optional: true}]);

    assert.equal(s.actions[0].type, 'click');
    assert.deepEqual(s.actions[0].target, {kind: 'bare', value: 'save'});
    assert.equal(s.actions[0].optional, true);
});

test('selectorTarget: test id, css, text', () => {
    assert.deepEqual(selectorTarget('data-test-id=modal-confirm'), {kind: 'bare', value: 'modal-confirm'});
    assert.deepEqual(selectorTarget('authoring-topbar'), {kind: 'bare', value: 'authoring-topbar'});
    assert.deepEqual(selectorTarget('[data-test-id="x"] .y'), {kind: 'css', css: '[data-test-id="x"] .y'});
    assert.deepEqual(selectorTarget('Save and send'), {kind: 'bare', value: 'Save and send'});
});

test('parseCrop handles full, unions, expansion and max height', () => {
    assert.equal(parseCrop('full').kind, 'full');

    const plus = parseCrop('element: [data-test-id="context-menu"] plus the item row');

    assert.deepEqual(plus.targets.map((t) => t.kind), ['css', 'alias']);

    const left = parseCrop('element: the open view switcher dropdown plus about 200px of toolbar to its left');

    assert.deepEqual(left.expand, {left: 200});
    assert.equal(left.targets[0].name, 'open view switcher dropdown');

    const top = parseCrop('element: [data-test-id="monitoring-view"] top 400px (bar plus the two selected rows)');

    assert.equal(top.maxHeight, 400);
    assert.equal(top.targets.length, 1);

    const named = parseCrop('element: the Scheduled Desk Output [data-test-id="monitoring-group"]');

    assert.equal(named.targets[0].hasText, 'Scheduled Desk Output');
});

test('parseHighlight: none, badge lists, scoped buttons', () => {
    assert.deepEqual(parseHighlight('none').items, []);

    const badges = parseHighlight('number or outline: Filters icon ([data-test-id="filters-dropdown"]), Search box (#search-input), view switcher');

    assert.equal(badges.style, 'badge');
    assert.deepEqual(badges.items.map((i) => i.position), [1, 2, 3]);
    assert.equal(badges.items[0].target.css, '[data-test-id="filters-dropdown"]');
    assert.equal(badges.items[1].target.css, '#search-input');
    assert.equal(badges.items[2].target.kind, 'alias');

    const scoped = parseHighlight('the tab row and the \'Close preview\' button in [data-test-id="authoring-preview"]');

    assert.equal(scoped.style, 'outline');
    assert.equal(scoped.items[1].target.role, 'button');
    assert.equal(scoped.items[1].target.within[0].css, '[data-test-id="authoring-preview"]');
    assert.equal(parseHighlight(['save'], 'badge').items[0].target.value, 'save');
});

test('parseRoute, parseViewport, shotId, resolveDateValue', () => {
    assert.deepEqual(parseRoute('/#/workspace/monitoring'), {kind: 'hash', hash: '#/workspace/monitoring'});
    assert.equal(parseRoute('#/master-desk').hash, '#/master-desk');
    assert.equal(parseRoute('Settings > Desks').kind, 'menu');
    assert.deepEqual(parseViewport('1440x1100'), {width: 1440, height: 1100});
    assert.deepEqual(parseViewport(undefined), {width: 1440, height: 900});
    assert.deepEqual(shotId('master-desk/overview-tab.png', 'x'), {page: 'master-desk', shot: 'overview-tab'});
    assert.deepEqual(shotId('lonely.png', 'manifest'), {page: 'manifest', shot: 'lonely'});

    const now = new Date(2026, 9, 12);

    assert.equal(resolveDateValue('tomorrow', 'DD/MM/YYYY', now), '13/10/2026');
    assert.equal(resolveDateValue('today', 'MM/DD/YYYY', now), '10/12/2026');
    assert.equal(resolveDateValue('12:00', 'DD/MM/YYYY', now), '12:00');
});
