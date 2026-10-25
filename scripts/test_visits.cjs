const {test} = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const source = fs.readFileSync(`${__dirname}/../assets/visits.js`, 'utf8');

function page(hostname = 'phyytang.github.io', search = '') {
  let now = 0, id = 0, notify;
  const timers = new Map(), requests = [];
  const value = {textContent: '加载中…'}, unit = {hidden: false}, counter = {hidden: false};
  const context = {
    URLSearchParams,
    location: {hostname, search},
    document: {
      getElementById: (key) => ({'teaching-visit-count': counter, 'busuanzi_value_page_pv': value, 'visit-count-unit': unit}[key]),
      body: {classList: {contains: () => false}},
      createElement: () => ({}), head: {append: (script) => requests.push(script)}
    },
    MutationObserver: class {
      constructor(callback) {notify = callback;}
      observe() {}
      disconnect() {}
    },
    setTimeout: (callback, delay) => {timers.set(++id, {at: now + delay, callback}); return id;},
    clearTimeout: (key) => timers.delete(key)
  };
  vm.runInNewContext(source, context);
  return {value, unit, counter, requests, notify: () => notify(), advance: (target) => {
    while (true) {
      const due = [...timers].filter(([, timer]) => timer.at <= target).sort((a, b) => a[1].at - b[1].at)[0];
      if (!due) break;
      now = due[1].at; timers.delete(due[0]); due[1].callback();
    }
    now = target;
  }};
}

test('statistics wait 20 seconds; response timeout begins only after requesting', () => {
  const p = page();
  p.advance(19999);
  assert.equal(p.requests.length, 0);
  assert.equal(p.value.textContent, '稍后更新…');
  p.advance(20000);
  assert.equal(p.requests.length, 1);
  assert.equal(p.requests[0].async, true);
  p.advance(29999);
  assert.equal(p.value.textContent, '稍后更新…');
  p.advance(30000);
  assert.equal(p.value.textContent, '暂不可用');
});

test('a returned count is formatted and survives the response timeout', () => {
  const p = page();
  p.advance(20000);
  p.value.textContent = '1234'; p.notify();
  assert.equal(p.value.textContent, '1,234');
  assert.equal(p.unit.hidden, false);
  p.advance(60000);
  assert.equal(p.value.textContent, '1,234');
});

test('local previews never request statistics and legacy readers hide the catalog counter', () => {
  const local = page('localhost'); local.advance(60000);
  assert.equal(local.requests.length, 0);
  assert.equal(local.value.textContent, '—');
  const reader = page('phyytang.github.io', '?note=materials/test.md');
  assert.equal(reader.counter.hidden, true);
});
