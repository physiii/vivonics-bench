'use strict';

const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const baseUrl = new URL(process.argv[2] || 'http://192.168.4.1/');
const exerciseOutput = process.argv.includes('--exercise-green');
const outputDir = path.resolve(
  process.env.LASER_DASHBOARD_SMOKE_OUTPUT || '/tmp/vivonics-laser-dashboard-live'
);
fs.mkdirSync(outputDir, { recursive: true });

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

async function api(pathname, options = {}) {
  const response = await fetch(new URL(pathname, baseUrl), {
    signal: AbortSignal.timeout(5000),
    ...options,
    headers: {
      ...(options.body ? { 'Content-Type': 'application/json' } : {}),
      ...(options.headers || {}),
    },
  });
  const body = await response.text();
  if (!response.ok) throw new Error(`${pathname}: HTTP ${response.status} ${body}`);
  return body ? JSON.parse(body) : null;
}

async function allOff() {
  await api('/api/lasers/off', { method: 'POST', body: '{}' });
  const deadline = Date.now() + 3000;
  while (Date.now() < deadline) {
    const telemetry = await api('/api/telemetry');
    if (!telemetry.output.active && telemetry.output.target === 'OFF') return telemetry;
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  throw new Error('Output did not reach OFF state');
}

async function verifyPage(browser, viewport, name) {
  const page = await browser.newPage({ viewport, deviceScaleFactor: 1 });
  const consoleErrors = [];
  const pageErrors = [];
  page.on('console', (message) => {
    if (message.type() === 'error') consoleErrors.push(message.text());
  });
  page.on('pageerror', (error) => pageErrors.push(error.message));

  await page.goto(baseUrl.href, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => document.querySelector('#headerLive')?.textContent === 'Live');
  assert(await page.title() === 'Vivonics Laser Controller', 'Unexpected page title');
  assert(await page.locator('.nav-item').count() === 3, 'Expected three primary tabs');
  assert(await page.locator('[data-laser-card]').count() === 4, 'Expected four laser cards');
  assert(await page.locator('[data-pd-card]').count() === 4, 'Expected four photodiode cards');
  assert((await page.locator('[data-pd-counts="3"]').textContent()) !== '—', 'PD3 telemetry missing');
  assert(
    await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth),
    'Page has horizontal viewport overflow'
  );

  let activeSample = null;
  if (name === 'desktop' && exerciseOutput) {
    await page.locator('.laser-activate[data-target="GREEN"]').click();
    await page.waitForFunction(() => document.querySelector('#activeOutput')?.textContent === 'GREEN');
    await page.waitForTimeout(600);
    activeSample = await api('/api/telemetry');
    assert(activeSample.output.active && activeSample.output.target === 'GREEN', 'Green output did not become active');
    await page.locator('#allOffButton').click();
    await page.waitForFunction(() => document.querySelector('#activeOutput')?.textContent === 'OFF');
  }

  if (name === 'desktop') {
    await page.locator('.nav-item[data-target="system"]').click();
    await page.waitForFunction(() => document.querySelector('#eventLog li:not(.empty-panel)'));
  }
  if (name === 'mobile') {
    const cardLefts = await page.locator('[data-laser-card]').evaluateAll((elements) =>
      elements.map((element) => element.getBoundingClientRect().left)
    );
    assert(cardLefts.every((left) => Math.abs(left - cardLefts[0]) < 2), 'Mobile cards are not one column');
  }
  await page.screenshot({ path: path.join(outputDir, `${name}.png`), fullPage: true });
  await page.close();
  assert(consoleErrors.length === 0, `Console errors: ${consoleErrors.join(' | ')}`);
  assert(pageErrors.length === 0, `Page errors: ${pageErrors.join(' | ')}`);
  return activeSample;
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  let activeTelemetry = null;
  try {
    const health = await api('/api/health');
    assert(health.ok && health.adcReady && health.faultMask === 0, 'Controller health gate failed');
    await allOff();
    activeTelemetry = await verifyPage(browser, { width: 1440, height: 1000 }, 'desktop');
    if (exerciseOutput) {
      const logs = await api('/api/logs');
      assert(logs.some((entry) => entry.message.includes('GREEN')), 'Green command was not logged');
    }
    await verifyPage(browser, { width: 390, height: 844 }, 'mobile');
    const state = await api('/api/state');
    const finalTelemetry = await allOff();
    process.stdout.write(JSON.stringify({
      ok: true,
      baseUrl: baseUrl.href,
      exercisedGreen: exerciseOutput,
      greenTelemetry: activeTelemetry ? {
        output: activeTelemetry.output,
        currentSense: activeTelemetry.lasers[2].currentSense,
        sourceMonitor: activeTelemetry.lasers[2].sourceMonitor,
        pd3: activeTelemetry.photodiodes[2],
      } : null,
      pd3: finalTelemetry.photodiodes[2],
      sampleIndex: finalTelemetry.sampleIndex,
      timingOverruns: finalTelemetry.timingOverruns,
      faultMask: finalTelemetry.faultMask,
      runningPartition: state.system.firmware.runningPartition,
      screenshots: outputDir,
    }, null, 2) + '\n');
  } finally {
    try { await allOff(); } catch (_) { /* Preserve the original test failure. */ }
    await browser.close();
  }
})().catch((error) => {
  console.error(error.stack || error.message);
  process.exitCode = 1;
});
