'use strict';

const fs = require('fs');
const http = require('http');
const path = require('path');
const { chromium } = require('playwright');

const publicDir = path.resolve(process.argv[2] || path.join(__dirname, '..', 'main', 'public'));
const outputDir = path.resolve(process.argv[3] || '/tmp/vivonics-laser-dashboard-smoke');
fs.mkdirSync(outputDir, { recursive: true });

let sampleIndex = 41000;
let output = { active: false, latched: false, channelMask: 0, target: 'OFF', dutyPermille: 0, sharedDuty: false, channels: [] };
const commandLog = [];
let eventLog = [
  { timestamp: 92500, message: 'Embedded laser dashboard started' },
  { timestamp: 91400, message: 'Wi-Fi connected at 192.168.1.142' },
  { timestamp: 100, message: 'Boot complete; laser outputs default off' },
];

const targetMasks = { IR: 1, RED: 2, GREEN: 4, BLUE: 8, IR_GREEN: 5 };
const targetOrder = ['IR', 'RED', 'GREEN', 'BLUE'];
const contentTypes = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.svg': 'image/svg+xml',
};

function telemetry() {
  sampleIndex += 10;
  const phase = sampleIndex / 37;
  const counts = [6314, 7261, 7458, 7407].map((base, index) => Math.round(base + Math.sin(phase + index) * (index === 2 ? 75 : 24)));
  const lasers = [
    ['IR', 'Infrared', 780, 10, 362, 1240],
    ['RED', 'Red', 650, 11, 0, 8],
    ['GREEN', 'Green', 520, 12, 78, 2110],
    ['BLUE', 'Blue', 450, 16, 0, 5],
  ].map(([target, name, wavelengthNm, pwmGpio, activeMv, activeMonitor], index) => {
    const active = output.active && (output.channelMask & (1 << index)) !== 0;
    const millivolts = active ? activeMv : 0;
    const monitor = active ? activeMonitor : 0;
    return {
      channel: index + 1,
      target,
      name,
      wavelengthNm,
      pwmGpio,
      active,
      dutyPermille: active ? output.channels.find((entry) => entry.target === target)?.dutyPermille || 0 : 0,
      currentSense: {
        raw: millivolts * 4,
        millivolts,
        milliampsApprox: millivolts / 10,
        expectedWhenActive: true,
        status: active ? (millivolts ? 'signal' : 'no-response') : 'idle',
        healthy: !active || Boolean(millivolts),
      },
      sourceMonitor: {
        raw: monitor * 4,
        millivolts: monitor,
        equipped: index < 3,
        expectedWhenActive: index < 3,
        status: index === 3 ? 'not-equipped' : (active ? (monitor ? 'signal' : 'no-response') : 'idle'),
        healthy: index === 3 || !active || Boolean(monitor),
      },
    };
  });
  return {
    ok: true,
    sampleIndex,
    sampledAtUs: sampleIndex * 20000,
    sampleRateHz: 50,
    timingOverruns: 2,
    safetyState: output.active ? 'running' : 'ready-lasers-off',
    faultMask: 0,
    output,
    photodiodes: counts.map((value, index) => ({ channel: index + 1, name: 'Signal photodiode', counts: value, volts: value * 5 / 32768 })),
    lasers,
    sensingDegraded: lasers.some((laser) => laser.active && (!laser.currentSense.healthy || !laser.sourceMonitor.healthy)),
  };
}

function state() {
  return {
    ok: true,
    device: {
      uuid: 'laser-ac276eca0ce4',
      name: 'Vivonics Laser Controller',
      network: {
        wifi_ap_ip: '192.168.4.1',
        wifi_sta_ip: '192.168.1.142',
        wifi_sta_mac: 'ac:27:6e:ca:0c:e4',
        wifi_ap_mac: 'ac:27:6e:ca:0c:e5',
        wifi_ap_ssid: 'VIVONICS-LASER-CA0CE4',
        wifi_sta_connected: true,
        active_ssid: 'HelloWorld',
        wifi_sta_rssi: -48,
        wifi_sta_quality: 100,
        wifi_sta_channel: 6,
        wifi_sta_auth: 'WPA2',
      },
    },
    system: {
      uptimeSeconds: 93784,
      freeHeap: 166240,
      minFreeHeap: 142632,
      largestFreeBlock: 90112,
      resetReason: 'Power-on',
      firmware: {
        projectName: 'vivonics_laser_controller',
        projectVersion: '0.2.0-dashboard',
        idfVersion: 'v5.5.4',
        buildDate: 'Jul 21 2026',
        buildTime: '14:32:07',
        elfSha256: 'c7a1f2bda49e0921',
        runningPartition: 'ota_0',
        bootPartition: 'ota_0',
        nextUpdatePartition: 'ota_1',
        otaPartitionCount: 2,
        rollbackEnabled: true,
        maxUploadBytes: 2097152,
        otaState: 'valid',
      },
    },
    telemetry: telemetry(),
  };
}

function sendJson(response, payload, status = 200) {
  response.writeHead(status, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
  response.end(JSON.stringify(payload));
}

async function bodyJson(request) {
  const chunks = [];
  for await (const chunk of request) chunks.push(chunk);
  return JSON.parse(Buffer.concat(chunks).toString('utf8') || '{}');
}

const server = http.createServer(async (request, response) => {
  try {
    const url = new URL(request.url, 'http://127.0.0.1');
    if (request.method === 'GET' && url.pathname === '/api/state') return sendJson(response, state());
    if (request.method === 'GET' && url.pathname === '/api/telemetry') return sendJson(response, telemetry());
    if (request.method === 'GET' && url.pathname === '/api/logs') return sendJson(response, eventLog);
    if (request.method === 'GET' && url.pathname === '/api/wifi/scan') return sendJson(response, [
      { ssid: 'HelloWorld', rssi: -48, channel: 6, auth: 'WPA2', secure: true },
      { ssid: 'Vivonics Lab', rssi: -67, channel: 11, auth: 'WPA3', secure: true },
      { ssid: 'Instrumentation', rssi: -75, channel: 1, auth: 'WPA2', secure: true },
    ]);
    if (request.method === 'POST' && url.pathname === '/api/lasers/off') {
      output = { active: false, latched: false, channelMask: 0, target: 'OFF', dutyPermille: 0, sharedDuty: false, channels: [] };
      commandLog.push({ kind: 'off' });
      return sendJson(response, { ok: true, queued: true });
    }
    if (request.method === 'POST' && url.pathname === '/api/lasers') {
      const command = await bodyJson(request);
      const channels = Array.isArray(command.channels)
        ? command.channels
        : [{ target: command.target, dutyPermille: command.dutyPermille }];
      const channelMask = channels.reduce((mask, channel) => mask | targetMasks[channel.target], 0);
      const target = targetOrder.filter((_, index) => channelMask & (1 << index)).join('_');
      const sharedDuty = channels.every((entry) => entry.dutyPermille === channels[0].dutyPermille);
      output = {
        active: true,
        latched: true,
        channelMask,
        target,
        dutyPermille: sharedDuty ? channels[0].dutyPermille : 0,
        sharedDuty,
        channels,
      };
      commandLog.push({ kind: 'on', ...command });
      return sendJson(response, { ok: true, queued: true, target, channelMask, channels });
    }
    if (request.method === 'POST' && url.pathname === '/api/diagnostics/sensing-pins') {
      const signals = [
        ['ISENSE1', 4, 53, 47], ['ISENSE2', 5, 52, 46],
        ['ISENSE3', 6, 52, 46], ['ISENSE4', 7, 51, 45],
        ['MPD1', 2, 54, 48], ['MPD2', 3, 54, 48],
        ['MPD3', 8, 51, 45], ['MPD4_SPARE', 9, 52, 46],
      ];
      const records = signals.map(([signal, gpio, pullupRaw, pullupMv], index) => ({
        timestamp: 93020 + index,
        message: `SENSE_PIN ${signal} G${gpio} F0/0mV U${pullupRaw}/${pullupMv}mV D0/0mV`,
      }));
      eventLog = [
        { timestamp: 93040, message: 'SENSETEST_END outputs=OFF' },
        ...records.reverse(),
        { timestamp: 93010, message: 'SENSETEST_BEGIN outputs=OFF weak_internal_pulls_only' },
        ...eventLog,
      ];
      commandLog.push({ kind: 'sensetest' });
      return sendJson(response, { ok: true, queued: true, outputsOff: true, results: '/api/logs' });
    }
    if (request.method === 'POST' && url.pathname === '/api/wifi') {
      const credentials = await bodyJson(request);
      commandLog.push({ kind: 'wifi', ssid: credentials.ssid, passwordProvided: Boolean(credentials.password) });
      return sendJson(response, { ok: true, ssid: credentials.ssid, connecting: true });
    }
    if (request.method === 'POST' && url.pathname === '/api/ota/upload') {
      return sendJson(response, { ok: true, reboot: true, partition: 'ota_1', bytes: Number(request.headers['content-length'] || 0), rebootDelayMs: 1500 });
    }

    const relative = url.pathname === '/' ? 'index.html' : url.pathname.slice(1);
    const allowed = new Set(['index.html', 'style.css', 'script.js', 'favicon.svg']);
    if (request.method !== 'GET' || !allowed.has(relative)) {
      response.writeHead(404);
      return response.end('Not found');
    }
    const file = path.join(publicDir, relative);
    response.writeHead(200, { 'Content-Type': contentTypes[path.extname(file)] || 'application/octet-stream' });
    fs.createReadStream(file).pipe(response);
  } catch (error) {
    response.writeHead(500);
    response.end(error.stack);
  }
});

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

async function verifyPage(browser, baseUrl, viewport, name) {
  const page = await browser.newPage({ viewport, deviceScaleFactor: 1 });
  const consoleErrors = [];
  const pageErrors = [];
  page.on('console', (message) => { if (message.type() === 'error') consoleErrors.push(message.text()); });
  page.on('pageerror', (error) => pageErrors.push(error.message));
  await page.goto(baseUrl, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => document.querySelector('#headerLive').textContent === 'Live');

  assert(await page.title() === 'Vivonics Laser Controller', 'Unexpected page title');
  assert(await page.locator('.nav-item').count() === 3, 'Expected three primary tabs');
  assert(await page.locator('[data-laser-card]').count() === 4, 'Expected four laser cards');
  assert(await page.locator('[data-pd-card]').count() === 4, 'Expected four photodiode cards');
  assert((await page.locator('[data-pd-counts="3"]').textContent()) !== '—', 'PD3 did not receive telemetry');
  assert((await page.locator('[data-current-ma="IR"]').textContent()) !== '—', 'IR current telemetry did not render');
  assert(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth), 'Page has horizontal viewport overflow');

  if (name === 'desktop') {
    await page.locator('#sensingTestButton').click();
    await page.waitForFunction(() => document.querySelector('#sensingTestStatus').textContent.startsWith('PASS'));
    assert(await page.locator('#sensingTestTableBody tr').count() === 8, 'Expected eight sensing-input results');
    assert(await page.locator('#sensingTestTableBody .test-pass').count() === 8, 'All sensing inputs did not pass');
    await page.locator('.laser-activate[data-target="IR"]').click();
    await page.waitForFunction(() => document.querySelector('#activeOutput').textContent === 'IR');
    await page.locator('.laser-activate[data-target="GREEN"]').click();
    await page.waitForFunction(() => document.querySelector('#activeOutput').textContent === 'IR + GREEN');
    assert(await page.locator('[data-laser-card].is-active').count() === 2, 'Two laser cards were not active together');
    assert((await page.locator('#activeChannelCount').textContent()) === '2 active channels', 'Active channel count did not update');
    assert((await page.locator('.laser-activate[data-target="IR"]').textContent()).startsWith('Remove'), 'IR did not become removable while Green stayed active');
    await page.locator('.laser-activate[data-target="IR"]').click();
    await page.waitForFunction(() => document.querySelector('#activeOutput').textContent === 'GREEN');
    assert(await page.locator('[data-laser-card="GREEN"].is-active').count() === 1, 'Removing IR did not preserve Green');
    await page.locator('#allOffButton').click();
    await page.waitForFunction(() => document.querySelector('#activeOutput').textContent === 'OFF');
    await page.locator('.nav-item[data-target="network"]').click();
    await page.locator('#wifiScanButton').click();
    await page.waitForSelector('.wifi-network-card');
    await page.waitForTimeout(350);
    await page.evaluate(() => document.querySelector('#toast').classList.remove('show'));
    await page.screenshot({ path: path.join(outputDir, 'network.png'), fullPage: true });
    await page.locator('.nav-item[data-target="system"]').click();
    await page.waitForFunction(() => document.querySelector('#eventLog li:not(.empty-panel)'));
    await page.waitForTimeout(350);
    await page.screenshot({ path: path.join(outputDir, 'system.png'), fullPage: true });
    await page.locator('.nav-item[data-target="dashboard"]').click();
  }

  await page.waitForTimeout(350);
  if (name === 'mobile') {
    const cards = await page.locator('[data-laser-card]').evaluateAll((elements) => elements.map((element) => element.getBoundingClientRect().left));
    assert(cards.every((left) => Math.abs(left - cards[0]) < 2), 'Mobile laser cards are not in one column');
  }
  await page.screenshot({ path: path.join(outputDir, `${name}.png`), fullPage: true });
  await page.close();
  assert(consoleErrors.length === 0, `Console errors: ${consoleErrors.join(' | ')}`);
  assert(pageErrors.length === 0, `Page errors: ${pageErrors.join(' | ')}`);
}

(async () => {
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  const address = server.address();
  const baseUrl = `http://127.0.0.1:${address.port}/`;
  const browser = await chromium.launch({ headless: true });
  try {
    await verifyPage(browser, baseUrl, { width: 1440, height: 1000 }, 'desktop');
    await verifyPage(browser, baseUrl, { width: 390, height: 844 }, 'mobile');
    assert(commandLog.some((entry) => entry.kind === 'on' && Array.isArray(entry.channels) && entry.channels.length === 2), 'Multi-laser activation command was not issued');
    assert(commandLog.some((entry) => entry.kind === 'off'), 'All-off command was not issued');
    assert(commandLog.some((entry) => entry.kind === 'sensetest'), 'Sensing-input self-test was not issued');
    process.stdout.write(JSON.stringify({ ok: true, baseUrl, screenshots: outputDir, commands: commandLog }, null, 2) + '\n');
  } finally {
    await browser.close();
    server.close();
  }
})().catch((error) => {
  console.error(error.stack || error.message);
  server.close();
  process.exitCode = 1;
});
