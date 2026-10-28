const {test} = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const source = fs.readFileSync(`${__dirname}/../assets/visits.js`, 'utf8');

function counter(kind, data = {}) {
  const classes = new Set();
  const value = {textContent: ''};
  const labels = [];
  return {
    hidden: false, title: '累计页面浏览次数', value,
    dataset: {visitCounter: kind, ...data},
    classList: {add: (c) => classes.add(c), remove: (c) => classes.delete(c), contains: (c) => classes.has(c)},
    querySelector: (selector) => selector === '.visit-value' ? value : labels.find((label) => `.${label.className}` === selector),
    append: (label) => labels.push(label)
  };
}
const config = {site: {workspace:'unit-test-workspace',name:'site-total'}, pages: {
  '/teaching/': {workspace:'unit-test-workspace',name:'teaching-home'},
  '/teaching/courses/theoretical-mechanics/': {workspace:'unit-test-workspace',name:'theoretical-mechanics'}
}};
const tick = () => new Promise(setImmediate);
function page({hostname = 'phyytang.github.io', pathname = '/', search = '', home = false, counters = [], settings = config, results = {}, storage = {}, duplicate = false} = {}) {
  let now = 0, id = 0;
  const timers = new Map(), requests = [];
  const context = {
    URL, URLSearchParams, Number, String, Math, Object, Date, AbortController,
    location: {hostname, pathname, search},
    localStorage: {getItem: (key) => storage[key] ?? null, setItem: (key, value) => {storage[key] = value;}},
    document: {
      currentScript: {src: 'https://phyytang.github.io/assets/visits.js?v=test'},
      querySelectorAll: () => counters,
      createElement: () => ({}),
      body: {classList: {contains: (name) => home && name === 'home'}}
    },
    setTimeout: (callback, delay) => {timers.set(++id, {at: now + delay, callback}); return id;},
    clearTimeout: (key) => timers.delete(key),
    fetch: async (input, options) => {
      const url = new URL(input);
      requests.push({url, options});
      const name = url.hostname === 'api.counterapi.dev' ? url.pathname.split('/').at(-2) : 'config';
      const result = results[name] || {};
      if (result.hang) return new Promise((resolve, reject) => options.signal.addEventListener('abort', () => reject(new Error('aborted')), {once: true}));
      return {ok: !result.status || result.status === 200, status: result.status || 200,
        json: async () => result.body ?? (name === 'config' ? settings : {code: '200', data: {up_count: 0, down_count: 0}})};
    }
  };
  context.window = context;
  vm.runInNewContext(source, context);
  if (duplicate) vm.runInNewContext(source, context);
  return {requests, storage, api: () => requests.filter(({url}) => url.hostname === 'api.counterapi.dev'),
    advance: async (target) => {
      while (true) {
        const due = [...timers].filter(([, timer]) => timer.at <= target).sort((a,b) => a[1].at - b[1].at)[0];
        if (!due) break;
        now = due[1].at; timers.delete(due[0]); due[1].callback(); await tick();
      }
      now = target; await tick();
    }};
}

test('waits one second and sends one public V2 increment without credentials or cached responses', async () => {
  const p = page({duplicate: true});
  await p.advance(999); assert.equal(p.requests.length, 0);
  await p.advance(1000); assert.equal(p.api().length, 1);
  const {url, options} = p.api()[0];
  assert.equal(url.pathname, '/v2/unit-test-workspace/site-total/up');
  assert.ok(url.searchParams.get('_'));
  assert.equal(options.cache, 'no-store');
  assert.equal(options.credentials, 'omit');
  assert.equal(options.headers, undefined);
});

test('course homepage increments the global and its own counter, with historic baselines added once', async () => {
  const site = counter('site', {visitOffset: '230', visitFloor: '230'});
  const course = counter('page', {visitOffset: '130', visitFloor: '130'});
  const p = page({pathname:'/teaching/courses/theoretical-mechanics/', counters:[site,course], results:{
    'site-total': {body:{code:'200',data:{up_count:12,down_count:2}}},
    'theoretical-mechanics': {body:{code:'200',data:{up_count:4,down_count:0}}}
  }});
  await p.advance(1000);
  assert.equal(p.api().length, 2);
  assert.equal(site.value.textContent, '240'); assert.equal(course.value.textContent, '134');
  assert.equal(course.dataset.visitState, 'ready');
  assert.equal(course.querySelector('.visit-status').textContent, '');
});

test('lecture pages use only the global counter; course counters do not expand per lecture', async () => {
  const p = page({pathname:'/teaching/notes/Mechanics/刚体运动.html'});
  await p.advance(1000);
  assert.deepEqual(p.api().map(({url}) => url.pathname), ['/v2/unit-test-workspace/site-total/up']);
});

test('index.html aliases use the same page counter and the teaching directory has its own counter', async () => {
  for (const pathname of ['/teaching/', '/teaching/index.html']) {
    const p = page({pathname, counters:[counter('page')]}); await p.advance(1000);
    assert.deepEqual(p.api().map(({url}) => url.pathname).sort(), ['/v2/unit-test-workspace/site-total/up','/v2/unit-test-workspace/teaching-home/up'].sort());
  }
});

test('local previews and redirecting legacy home pages send no statistics', async () => {
  for (const options of [{hostname:'localhost'}, {home:true, search:'?note=materials/test.md'}]) {
    const p = page({...options, counters:[counter('site')]}); await p.advance(60000);
    assert.equal(p.requests.length, 0);
  }
  const c = counter('page'); const p = page({pathname:'/teaching/',search:'?note=materials/copyright.md',counters:[c]});
  await p.advance(1000); assert.equal(c.hidden,true); assert.equal(p.api().length,1);
});

test('timeouts preserve explicitly labelled history without retrying increments', async () => {
  const c = counter('site',{visitOffset:'230',visitFloor:'230'});
  const p = page({counters:[c],results:{'site-total':{hang:true}}});
  assert.equal(c.querySelector('.visit-status').textContent,'（历史记录）');
  await p.advance(60000);
  assert.equal(c.value.textContent,'230'); assert.equal(c.dataset.visitState,'stale');
  assert.equal(p.api().length,1);
});

test('one missing or private counter does not prevent another counter updating', async () => {
  const site=counter('site',{visitOffset:'230'}), course=counter('page',{visitFloor:'130'});
  const p=page({pathname:'/teaching/courses/theoretical-mechanics/',counters:[site,course],results:{
    'site-total':{body:{code:'200',data:{up_count:5,down_count:0}}}, 'theoretical-mechanics':{status:404}
  }}); await p.advance(1000);
  assert.equal(site.value.textContent,'235');assert.equal(site.dataset.visitState,'ready');
  assert.equal(course.value.textContent,'130');assert.equal(course.dataset.visitState,'stale');
});

test('zero and buffered values are displayed honestly without a fabricated plus one', async () => {
  const c=counter('site',{visitOffset:'230',visitFloor:'230'}); const p=page({counters:[c]});
  await p.advance(1000);assert.equal(c.value.textContent,'230');assert.equal(c.dataset.visitState,'ready');
});

test('old provider cached totals do not mask fresh CounterAPI increments', async () => {
  const c=counter('site',{visitOffset:'230',visitFloor:'230'});
  const p=page({counters:[c],storage:{'visits:site:':'9999'},results:{'site-total':{body:{code:'200',data:{up_count:2,down_count:0}}}}});
  await p.advance(1000);assert.equal(c.value.textContent,'232');
  assert.equal(p.storage['visits:counterapi:unit-test-workspace/site-total:site:'],'232');
});

test('missing workspace and malformed payloads keep history and never produce NaN or fake counts', async () => {
  const c=counter('site',{visitFloor:'230'}); const p=page({counters:[c],settings:{site:{workspace:'',name:'site-total'}}});
  await p.advance(1000);assert.equal(p.api().length,0);assert.equal(c.dataset.visitState,'stale');
  const d=counter('site',{visitFloor:'230'});const q=page({counters:[d],results:{'site-total':{body:{code:'200',data:{up_count:'invalid'}}}}});
  await q.advance(1000);assert.equal(d.value.textContent,'230');assert.equal(d.dataset.visitState,'stale');
});


test('actual configuration keeps the three counters in their separate workspaces', async () => {
  const settings=JSON.parse(fs.readFileSync(`${__dirname}/../assets/counterapi.json`,'utf8'));
  const expectedSite='/v2/yong-tangs-team-6063/total-counter/up';
  for (const [pathname, expectedPage] of [
    ['/teaching/','/v2/teach-counter/teach-counter/up'],
    ['/teaching/courses/theoretical-mechanics/','/v2/mech-counter/mech-counter/up']
  ]) {
    const p=page({pathname,settings,counters:[counter('page')]}); await p.advance(1000);
    assert.deepEqual(p.api().map(({url})=>url.pathname).sort(),[expectedSite,expectedPage].sort());
  }
});

test('matching names in different workspaces remain independent and use isolated history', async () => {
  const site=counter('site'),course=counter('page');
  const p=page({pathname:'/teaching/',counters:[site,course],settings:{
    site:{workspace:'site-workspace',name:'views'},pages:{'/teaching/':{workspace:'course-workspace',name:'views'}}
  },storage:{'visits:counterapi:site-workspace/views:site:':'21','visits:counterapi:course-workspace/views:page:/teaching/':'7'}});
  await p.advance(1000);
  assert.deepEqual(p.api().map(({url})=>url.pathname).sort(),['/v2/site-workspace/views/up','/v2/course-workspace/views/up'].sort());
  assert.equal(site.value.textContent,'21');assert.equal(course.value.textContent,'7');
});

test('a missing workspace on one definition does not stop the other definition', async () => {
  const site=counter('site'),course=counter('page',{visitFloor:'130'});
  const p=page({pathname:'/teaching/',counters:[site,course],settings:{
    site:{workspace:'global',name:'views'},pages:{'/teaching/':{workspace:'',name:'views'}}
  },results:{views:{body:{code:'200',data:{up_count:8,down_count:0}}}}});
  await p.advance(1000);assert.equal(p.api().length,1);
  assert.equal(site.value.textContent,'8');assert.equal(site.dataset.visitState,'ready');
  assert.equal(course.value.textContent,'130');assert.equal(course.dataset.visitState,'stale');
});
