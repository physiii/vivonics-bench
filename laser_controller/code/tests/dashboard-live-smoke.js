'use strict';

const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const baseUrl = new URL(process.argv[2] || 'http://192.168.4.1/');
const exerciseGreen = process.argv.includes('--exercise-green');
const exerciseMulti = process.argv.includes('--exercise-multi');
const exerciseOutput = exerciseGreen || exerciseMulti;
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
  if (name === 'desktop') {
    await page.locator('#sensingTestButton').click();
    await page.waitForFunction(
      () => document.querySelector('#sensingTestStatus')?.textContent.startsWith('PASS'),
      null,
      { timeout: 6000 }
    );
    assert(await page.locator('#sensingTestTableBody tr').count() === 8, 'Expected eight live sensing-input results');
    assert(await page.locator('#sensingTestTableBody .test-pass').count() === 8, 'All live sensing inputs did not respond');
  }
  if (name === 'desktop' && exerciseOutput) {
    if (exerciseMulti) {
      await page.locator('.laser-activate[data-target="IR"]').click();
      await page.waitForFunction(() => document.querySelector('#activeOutput')?.textContent === 'IR');
    }
    await page.locator('.laser-activate[data-target="GREEN"]').click();
    await page.waitForFunction(
      (multi) => document.querySelector('#activeOutput')?.textContent === (multi ? 'IR + GREEN' : 'GREEN'),
      exerciseMulti
    );
    await page.waitForTimeout(600);
    activeSample = await api('/api/telemetry');
    const expectedMask = exerciseMulti ? 5 : 4;
    assert(activeSample.output.active && activeSample.output.channelMask === expectedMask, 'Requested output mask did not become active');
    if (exerciseMulti) {
      assert(activeSample.lasers[0].active && activeSample.lasers[2].active, 'IR and Green were not active together');
      assert(activeSample.lasers[0].currentSense.status === 'signal', 'IR current-sense status did not report signal');
    }
    await page.screenshot({ path: path.join(outputDir, exerciseMulti ? 'active-multi.png' : 'active-green.png'), fullPage: true });
    if (exerciseMulti) {
      await page.locator('.laser-activate[data-target="IR"]').click();
      await page.waitForFunction(() => document.querySelector('#activeOutput')?.textContent === 'GREEN');
      const greenOnly = await api('/api/telemetry');
      assert(greenOnly.output.channelMask === 4 && greenOnly.lasers[2].active, 'Removing IR did not preserve Green');
    }
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
      assert(logs.some((entry) => entry.message.includes(exerciseMulti ? 'IR_GREEN' : 'GREEN')), 'Output command was not logged');
    }
    await verifyPage(browser, { width: 390, height: 844 }, 'mobile');
    const state = await api('/api/state');
    const finalTelemetry = await allOff();
    process.stdout.write(JSON.stringify({
      ok: true,
      baseUrl: baseUrl.href,
      exercisedGreen: exerciseOutput,
      exercisedMulti: exerciseMulti,
      activeTelemetry: activeTelemetry ? {
        output: activeTelemetry.output,
        ir: activeTelemetry.lasers[0],
        green: activeTelemetry.lasers[2],
        pd3: activeTelemetry.photodiodes[2],
        sensingDegraded: activeTelemetry.sensingDegraded,
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
