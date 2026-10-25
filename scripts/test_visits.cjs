const {test} = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const source = fs.readFileSync(`${__dirname}/../assets/visits.js`, 'utf8');

function counter(kind, data = {}) {
  const value = {textContent: ''};
  const classes = new Set();
  return {
    hidden: false, title: '累计页面浏览次数', value,
    dataset: {visitCounter: kind, ...data},
    classList: {add: (c) => classes.add(c), remove: (c) => classes.delete(c), contains: (c) => classes.has(c)},
    querySelector: (selector) => (selector === '.visit-value' ? value : null),
  };
}

function page({hostname = 'phyytang.github.io', search = '', pathname = '/', counters = [], storage = {}, home = false} = {}) {
  let now = 0, id = 0;
  const timers = new Map(), requests = [];
  const context = {
    URLSearchParams, Number, Math, String,
    location: {hostname, search, pathname},
    localStorage: {getItem: (k) => (k in storage ? storage[k] : null), setItem: (k, v) => { storage[k] = v; }},
    document: {
      querySelectorAll: () => counters,
      body: {classList: {contains: (c) => c === 'home' && home}},
      createElement: () => ({remove() {}}),
      head: {append: (script) => requests.push(script)},
    },
    setTimeout: (callback, delay) => { timers.set(++id, {at: now + delay, callback}); return id; },
  };
  context.window = context;
  vm.runInNewContext(source, context);
  const start = () => { for (const [key, timer] of [...timers]) if (timer.at <= 1000) { timers.delete(key); now = timer.at; timer.callback(); } now = Math.max(now, 1000); };
  const callbackName = () => /jsonpCallback=([\w]+)/.exec(requests[0].src)[1];
  return {
    requests, storage,
    start,
    answer: (data) => { if (!requests.length) start(); context[callbackName()](data); },
    advance: (target) => {
      while (true) {
        const due = [...timers].filter(([, timer]) => timer.at <= target).sort((a, b) => a[1].at - b[1].at)[0];
        if (!due) break;
        now = due[1].at; timers.delete(due[0]); due[1].callback();
      }
      now = target;
    },
  };
}

test('a view is recorded after 1 second, with the full page URL as referrer', () => {
  const p = page({counters: [counter('site', {visitFloor: '230'})]});
  p.advance(999);
  assert.equal(p.requests.length, 0);
  p.advance(1000);
  assert.equal(p.requests.length, 1);
  assert.equal(p.requests[0].async, true);
  assert.equal(p.requests[0].referrerPolicy, 'no-referrer-when-downgrade');
  assert.match(p.requests[0].src, /^https:\/\/busuanzi\.ibruce\.info\/busuanzi\?jsonpCallback=/);
});

test('the last known total shows at once and stays if the service never answers', () => {
  const site = counter('site', {visitFloor: '230'});
  const p = page({counters: [site]});
  assert.equal(site.value.textContent, '230');
  p.advance(60000);
  assert.equal(site.value.textContent, '230');
  assert.equal(site.classList.contains('visit-stale'), true);
  assert.match(site.title, /最近一次记录/);
});

test('live numbers include the offset, never drop below the floor, and are remembered', () => {
  const site = counter('site', {visitFloor: '230'});
  const course = counter('page', {visitOffset: '130', visitFloor: '130'});
  const p = page({pathname: '/teaching/courses/theoretical-mechanics/', counters: [site, course]});
  p.answer({site_pv: 12, page_pv: 4, site_uv: 3, page_uv: 2});
  assert.equal(site.value.textContent, '230');
  assert.equal(course.value.textContent, '134');
  const site2 = counter('site', {visitFloor: '230'});
  const course2 = counter('page', {visitOffset: '130', visitFloor: '130'});
  const q = page({pathname: '/teaching/courses/theoretical-mechanics/', counters: [site2, course2], storage: p.storage});
  assert.equal(course2.value.textContent, '134');  // remembered from the previous visit
  q.answer({site_pv: 1234, page_pv: 5});
  assert.equal(site2.value.textContent, '1,234');
  assert.equal(q.storage['visits:site:'], '1234');
  assert.equal(q.storage['visits:page:/teaching/courses/theoretical-mechanics/'], '135');
});

test('a late answer still updates a counter marked stale', () => {
  const site = counter('site', {visitFloor: '230'});
  const p = page({counters: [site]});
  p.advance(20000);
  assert.equal(site.classList.contains('visit-stale'), true);
  p.answer({site_pv: 240});
  assert.equal(site.value.textContent, '240');
  assert.equal(site.classList.contains('visit-stale'), false);
  assert.equal(site.title, '累计页面浏览次数');
});

test('a remembered total in this browser is never shown lower', () => {
  const site = counter('site', {visitFloor: '230'});
  const p = page({counters: [site], storage: {'visits:site:': '260'}});
  assert.equal(site.value.textContent, '260');
  p.answer({site_pv: 250});
  assert.equal(site.value.textContent, '260');
});

test('local previews never count; legacy readers hide page counters but still count', () => {
  const local = page({hostname: 'localhost', counters: [counter('site', {visitFloor: '230'})]});
  local.advance(60000);
  assert.equal(local.requests.length, 0);
  const course = counter('page', {visitOffset: '130'});
  const reader = page({search: '?note=materials/test.md', counters: [course]});
  reader.advance(1000);
  assert.equal(course.hidden, true);
  assert.equal(reader.requests.length, 1);
});
