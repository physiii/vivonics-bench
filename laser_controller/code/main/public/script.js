'use strict';

const LASER_ORDER = ['IR', 'RED', 'GREEN', 'BLUE'];
const SENSING_SIGNAL_ORDER = ['ISENSE1', 'ISENSE2', 'ISENSE3', 'ISENSE4', 'MPD1', 'MPD2', 'MPD3', 'MPD4_SPARE'];
const HISTORY_LENGTH = 120;
const TELEMETRY_INTERVAL_MS = 200;
const STATE_INTERVAL_MS = 3000;
const REQUEST_TIMEOUT_MS = 2500;

const histories = Array.from({ length: 4 }, () => []);
let lastTelemetryAt = 0;
let lastStateAt = 0;
let telemetryRequestPending = false;
let stateRequestPending = false;
let toastTimer = null;
let currentOutput = { active: false, target: 'OFF', channelMask: 0, dutyPermille: 0 };
let controllerReady = false;
let otaInProgress = false;
let commandPending = false;
let sensingTestPending = false;

const byId = (id) => document.getElementById(id);
const all = (selector, root = document) => Array.from(root.querySelectorAll(selector));

function setText(target, value) {
  const element = typeof target === 'string' ? byId(target) : target;
  if (element) element.textContent = value;
}

function formatInteger(value) {
  return Number.isFinite(Number(value)) ? Math.round(Number(value)).toLocaleString() : '—';
}

function formatBytes(value) {
  const bytes = Number(value);
  if (!Number.isFinite(bytes)) return '—';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KiB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MiB`;
}

function formatUptime(value) {
  let seconds = Math.max(0, Math.floor(Number(value) || 0));
  const days = Math.floor(seconds / 86400);
  seconds %= 86400;
  const hours = Math.floor(seconds / 3600);
  seconds %= 3600;
  const minutes = Math.floor(seconds / 60);
  const parts = [];
  if (days) parts.push(`${days}d`);
  if (hours || days) parts.push(`${hours}h`);
  parts.push(`${minutes}m`);
  return parts.join(' ');
}

function showToast(message, isError = false) {
  const toast = byId('toast');
  if (!toast) return;
  toast.textContent = message;
  toast.classList.toggle('is-error', isError);
  toast.classList.add('show');
  window.clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => toast.classList.remove('show'), 3500);
}

async function fetchJson(url, options = {}, timeoutMs = REQUEST_TIMEOUT_MS) {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url, {
      cache: 'no-store',
      ...options,
      headers: {
        Accept: 'application/json',
        ...(options.body ? { 'Content-Type': 'application/json' } : {}),
        ...(options.headers || {}),
      },
      signal: controller.signal,
    });
    const body = await response.text();
    let payload = null;
    if (body) {
      try { payload = JSON.parse(body); } catch (_) { payload = null; }
    }
    if (!response.ok) {
      throw new Error((payload && (payload.error || payload.message)) || body || `HTTP ${response.status}`);
    }
    return payload;
  } finally {
    window.clearTimeout(timeout);
  }
}

function updateConnectionState() {
  const freshest = Math.max(lastTelemetryAt, lastStateAt);
  const age = freshest ? Date.now() - freshest : Infinity;
  const live = age < 2500;
  const dot = byId('liveDot');
  dot.classList.toggle('is-live', live);
  dot.classList.toggle('is-offline', !live && freshest > 0);
  setText('headerLive', live ? 'Live' : (freshest ? 'Offline' : 'Connecting'));
  all('.laser-activate').forEach((button) => {
    button.disabled = !live || !controllerReady || otaInProgress || commandPending;
  });
  byId('allOffButton').disabled = !live || otaInProgress;
  const sensingTestButton = byId('sensingTestButton');
  if (sensingTestButton) {
    sensingTestButton.disabled = !live || !controllerReady || currentOutput.active ||
      otaInProgress || commandPending || sensingTestPending;
  }
}

function initializeTabs() {
  all('.nav-item').forEach((button) => {
    button.addEventListener('click', () => {
      all('.nav-item').forEach((item) => item.classList.toggle('active', item === button));
      all('.page').forEach((page) => page.classList.toggle('active', page.id === `page-${button.dataset.target}`));
      if (button.dataset.target === 'system') refreshLogs();
    });
  });
}

function updateRange(slider, output) {
  const value = Number(slider.value);
  slider.style.setProperty('--range-progress', `${(value / Number(slider.max)) * 100}%`);
  if (output) output.textContent = `${(value / 10).toFixed(1)}%`;
}

function initializeDutyControls() {
  all('.duty-slider').forEach((slider) => {
    const output = byId(`${slider.id}Value`);
    const update = () => updateRange(slider, output);
    slider.addEventListener('input', update);
    slider.addEventListener('change', () => {
      const channel = LASER_ORDER.indexOf(slider.dataset.target);
      if (channel >= 0 && (currentOutput.channelMask & (1 << channel)) !== 0) {
        applyChannelMask(currentOutput.channelMask, `Updated ${slider.dataset.target} duty`);
      }
    });
    update();
  });
}

function drawSparkline(channelIndex) {
  const values = histories[channelIndex];
  const svg = document.querySelector(`[data-sparkline="${channelIndex + 1}"]`);
  if (!svg || values.length === 0) return;
  const line = svg.querySelector('.spark-line');
  const area = svg.querySelector('.spark-area');
  let minimum = Math.min(...values);
  let maximum = Math.max(...values);
  if (minimum === maximum) {
    minimum -= 0.0001;
    maximum += 0.0001;
  }
  const range = maximum - minimum;
  const points = values.map((value, index) => {
    const x = values.length === 1 ? 150 : index * (300 / (values.length - 1));
    const y = 68 - ((value - minimum) / range) * 60;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });
  line.setAttribute('points', points.join(' '));
  area.setAttribute('d', `M ${points[0]} L ${points.join(' L ')} L ${points[points.length - 1].split(',')[0]},74 L 0,74 Z`);
}

function updatePhotodiode(item, index, recordHistory) {
  const channel = Number(item.channel) || index + 1;
  const counts = Number(item.counts);
  const volts = Number(item.volts);
  setText(document.querySelector(`[data-pd-counts="${channel}"]`), formatInteger(counts));
  setText(document.querySelector(`[data-pd-volts="${channel}"]`), Number.isFinite(volts) ? volts.toFixed(5) : '—');
  if (recordHistory && Number.isFinite(volts)) {
    histories[channel - 1].push(volts);
    if (histories[channel - 1].length > HISTORY_LENGTH) histories[channel - 1].shift();
  }
  const values = histories[channel - 1];
  if (values.length) {
    const minimum = Math.min(...values);
    const maximum = Math.max(...values);
    const mean = values.reduce((sum, value) => sum + value, 0) / values.length;
    setText(document.querySelector(`[data-pd-min="${channel}"]`), minimum.toFixed(5));
    setText(document.querySelector(`[data-pd-mean="${channel}"]`), mean.toFixed(5));
    setText(document.querySelector(`[data-pd-max="${channel}"]`), maximum.toFixed(5));
    drawSparkline(channel - 1);
  }
}

function updateLaser(item) {
  const target = item.target;
  if (!LASER_ORDER.includes(target)) return;
  const current = item.currentSense || {};
  const monitor = item.sourceMonitor || {};
  setText(document.querySelector(`[data-current-ma="${target}"]`), Number.isFinite(Number(current.milliampsApprox)) ? Number(current.milliampsApprox).toFixed(1) : '—');
  setText(document.querySelector(`[data-current-mv="${target}"]`), formatInteger(current.millivolts));
  setText(document.querySelector(`[data-current-raw="${target}"]`), formatInteger(current.raw));
  setText(document.querySelector(`[data-monitor-mv="${target}"]`), formatInteger(monitor.millivolts));
  setText(document.querySelector(`[data-monitor-raw="${target}"]`), formatInteger(monitor.raw));
  const statusLabels = {
    idle: 'Idle',
    signal: 'Signal',
    'no-response': 'No response',
    'not-equipped': 'Not equipped',
  };
  const currentStatus = document.querySelector(`[data-current-status="${target}"]`);
  const monitorStatus = document.querySelector(`[data-monitor-status="${target}"]`);
  if (currentStatus) {
    currentStatus.textContent = statusLabels[current.status] || 'Unknown';
    currentStatus.classList.toggle('is-signal', current.status === 'signal');
    currentStatus.classList.toggle('is-warning', current.status === 'no-response');
  }
  if (monitorStatus) {
    monitorStatus.textContent = statusLabels[monitor.status] || 'Unknown';
    monitorStatus.classList.toggle('is-signal', monitor.status === 'signal');
    monitorStatus.classList.toggle('is-warning', monitor.status === 'no-response');
  }
  const state = document.querySelector(`[data-laser-state="${target}"]`);
  const card = document.querySelector(`[data-laser-card="${target}"]`);
  const button = document.querySelector(`.laser-activate[data-target="${target}"]`);
  state.textContent = item.active ? 'ACTIVE' : 'OFF';
  state.classList.toggle('active', Boolean(item.active));
  card.classList.toggle('is-active', Boolean(item.active));
  card.classList.toggle(
    'sensing-degraded',
    Boolean(item.active) && (current.status === 'no-response' || monitor.status === 'no-response')
  );
  if (button) {
    button.textContent = item.active ? `Remove ${item.name || target}` : `Add ${item.name || target}`;
    button.classList.toggle('is-remove', Boolean(item.active));
  }
  if (item.active && Number(item.dutyPermille) > 0) {
    const slider = document.querySelector(`.duty-slider[data-target="${target}"]`);
    if (slider && document.activeElement !== slider) {
      slider.value = String(item.dutyPermille);
      updateRange(slider, byId(`${slider.id}Value`));
    }
  }
}

function renderTelemetryTable(lasers) {
  const body = byId('telemetryTableBody');
  body.replaceChildren();
  lasers.forEach((laser) => {
    const current = laser.currentSense || {};
    const monitor = laser.sourceMonitor || {};
    const row = document.createElement('tr');
    row.classList.toggle('is-active', Boolean(laser.active));
    const values = [
      `${laser.name || laser.target} · ${formatInteger(laser.wavelengthNm)} nm`,
      laser.active ? 'ACTIVE' : 'OFF',
      formatInteger(current.raw),
      `${formatInteger(current.millivolts)} mV · ${current.status || 'unknown'}`,
      `${Number.isFinite(Number(current.milliampsApprox)) ? Number(current.milliampsApprox).toFixed(1) : '—'} mA`,
      formatInteger(monitor.raw),
      `${formatInteger(monitor.millivolts)} mV · ${monitor.status || 'unknown'}`,
    ];
    values.forEach((value, index) => {
      const cell = document.createElement('td');
      if (index === 1) {
        const pill = document.createElement('span');
        pill.className = `output-pill${laser.active ? ' is-active' : ''}`;
        pill.textContent = value;
        cell.appendChild(pill);
      } else {
        cell.textContent = value;
      }
      row.appendChild(cell);
    });
    body.appendChild(row);
  });
}

function parseSensingPinRecord(message) {
  const match = /^SENSE_PIN ([A-Z0-9_]+) G(\d+) F(\d+)\/(\d+)mV U(\d+)\/(\d+)mV D(\d+)\/(\d+)mV$/.exec(message || '');
  if (!match) return null;
  return {
    signal: match[1],
    gpio: Number(match[2]),
    floatingRaw: Number(match[3]),
    floatingMv: Number(match[4]),
    pullupRaw: Number(match[5]),
    pullupMv: Number(match[6]),
    pulldownRaw: Number(match[7]),
    pulldownMv: Number(match[8]),
  };
}

function renderSensingPinResults(records) {
  const body = byId('sensingTestTableBody');
  body.replaceChildren();
  const bySignal = new Map(records.map((record) => [record.signal, record]));
  let responsiveCount = 0;
  SENSING_SIGNAL_ORDER.forEach((signal) => {
    const record = bySignal.get(signal);
    if (!record) return;
    const responsive = record.pullupRaw > record.floatingRaw && record.pullupRaw > record.pulldownRaw;
    if (responsive) responsiveCount += 1;
    const row = document.createElement('tr');
    const values = [
      record.signal,
      `GPIO ${record.gpio}`,
      `${record.floatingRaw} · ${record.floatingMv} mV`,
      `${record.pullupRaw} · ${record.pullupMv} mV`,
      `${record.pulldownRaw} · ${record.pulldownMv} mV`,
      responsive ? 'RESPONDS' : 'CHECK',
    ];
    values.forEach((value, index) => {
      const cell = document.createElement('td');
      cell.textContent = value;
      if (index === values.length - 1) cell.className = responsive ? 'test-pass' : 'test-check';
      row.appendChild(cell);
    });
    body.appendChild(row);
  });
  byId('sensingTestResults').hidden = false;
  const complete = records.length === SENSING_SIGNAL_ORDER.length;
  const passed = complete && responsiveCount === SENSING_SIGNAL_ORDER.length;
  setText('sensingTestStatus', passed ? 'PASS · all 8 sensing inputs respond' : `CHECK · ${responsiveCount}/${SENSING_SIGNAL_ORDER.length} inputs respond`);
  setText(
    'sensingTestDetail',
    passed
      ? 'ESP32 ADC/GPIO inputs responded and every laser remained off. This validates the digital input side, not the upstream analog current/monitor circuitry.'
      : 'One or more expected SENSE_PIN records were missing or did not move under the weak pull-up. Inspect the event log and board path.'
  );
  return passed;
}

async function runSensingPinSelfTest() {
  if (currentOutput.active) {
    showToast('Switch all laser outputs off before testing sensing inputs', true);
    return;
  }
  sensingTestPending = true;
  updateConnectionState();
  const button = byId('sensingTestButton');
  button.textContent = 'Testing…';
  setText('sensingTestStatus', 'Testing eight inputs · outputs remain off');
  setText('sensingTestDetail', 'Applying only the ESP32 weak internal pulls and collecting raw ADC readings.');
  try {
    const baseline = await fetchJson('/api/logs');
    const baselineTimestamp = Array.isArray(baseline)
      ? baseline.reduce((latest, entry) => Math.max(latest, Number(entry.timestamp) || 0), 0)
      : 0;
    await fetchJson('/api/diagnostics/sensing-pins', { method: 'POST', body: '{}' });
    let records = [];
    let ended = false;
    for (let attempt = 0; attempt < 25 && !ended; attempt += 1) {
      await new Promise((resolve) => window.setTimeout(resolve, 160));
      const entries = await fetchJson('/api/logs');
      const currentEntries = Array.isArray(entries)
        ? entries.filter((entry) => (Number(entry.timestamp) || 0) > baselineTimestamp)
        : [];
      records = currentEntries.map((entry) => parseSensingPinRecord(entry.message)).filter(Boolean);
      ended = currentEntries.some((entry) => entry.message === 'SENSETEST_END outputs=OFF');
    }
    if (!ended) throw new Error('controller did not report SENSETEST_END');
    const passed = renderSensingPinResults(records);
    showToast('Sensing-input self-test finished with all outputs off', !passed);
    await refreshLogs();
  } catch (error) {
    setText('sensingTestStatus', 'Self-test did not complete');
    setText('sensingTestDetail', error.message);
    showToast(`Sensing-input test failed: ${error.message}`, true);
  } finally {
    sensingTestPending = false;
    button.textContent = 'Test sensing inputs';
    updateConnectionState();
    window.setTimeout(pollTelemetry, 50);
  }
}

function applyTelemetry(telemetry, recordHistory = true) {
  if (!telemetry || !telemetry.ok) return;
  lastTelemetryAt = Date.now();
  const output = telemetry.output || {};
  currentOutput = {
    active: Boolean(output.active),
    target: output.target || 'OFF',
    channelMask: Number(output.channelMask) || 0,
    dutyPermille: Number(output.dutyPermille) || 0,
  };
  const faultMask = Number(telemetry.faultMask) || 0;
  controllerReady = faultMask === 0 && ['ready-lasers-off', 'armed', 'running'].includes(telemetry.safetyState);
  setText('safetyState', (telemetry.safetyState || 'unknown').replaceAll('-', ' '));
  setText('faultDetail', faultMask ? `Fault mask 0x${faultMask.toString(16).padStart(8, '0')}` : 'No latched faults');
  setText('activeOutput', currentOutput.active ? currentOutput.target.replaceAll('_', ' + ') : 'OFF');
  const outputChannels = Array.isArray(output.channels) ? output.channels : [];
  const dutySummary = output.sharedDuty
    ? `${(currentOutput.dutyPermille / 10).toFixed(1)}% shared duty`
    : outputChannels.map((item) => `${item.target} ${(Number(item.dutyPermille) / 10).toFixed(1)}%`).join(' · ');
  setText('activeDuty', currentOutput.active ? `${dutySummary}${output.latched ? ' · steady ON' : ''}` : '0.0% duty');
  const activeCount = LASER_ORDER.reduce((count, _, index) => count + ((currentOutput.channelMask & (1 << index)) ? 1 : 0), 0);
  setText('activeChannelCount', `${activeCount} active channel${activeCount === 1 ? '' : 's'}`);
  setText('sampleIndex', formatInteger(telemetry.sampleIndex));
  setText('sampleAge', `Updated now · ${formatInteger(telemetry.sampleRateHz)} samples/s`);
  setText('timingOverruns', formatInteger(telemetry.timingOverruns));
  setText('headerSampleRate', `${formatInteger(telemetry.sampleRateHz)} Hz`);
  setText('pdSampleRate', `${formatInteger(telemetry.sampleRateHz)} Hz`);

  const safety = byId('safetyState');
  safety.classList.toggle('is-good', controllerReady && !currentOutput.active);
  safety.classList.toggle('is-active', controllerReady && currentOutput.active);
  safety.classList.toggle('is-fault', faultMask !== 0);
  const banner = byId('faultBanner');
  banner.hidden = faultMask === 0;
  if (faultMask) setText('faultBannerText', `Fault mask 0x${faultMask.toString(16).padStart(8, '0')}; reset is required before another output can run.`);

  (telemetry.photodiodes || []).forEach((item, index) => updatePhotodiode(item, index, recordHistory));
  const lasers = telemetry.lasers || [];
  lasers.forEach(updateLaser);
  if (lasers.length) renderTelemetryTable(lasers);
  const sensingBanner = byId('sensingBanner');
  const degradedTargets = lasers.filter((laser) => laser.active && (
    (laser.currentSense || {}).status === 'no-response' ||
    (laser.sourceMonitor || {}).status === 'no-response'
  ));
  sensingBanner.hidden = degradedTargets.length === 0;
  if (degradedTargets.length) {
    const details = degradedTargets.map((laser) => {
      const missing = [];
      if ((laser.currentSense || {}).status === 'no-response') missing.push('current');
      if ((laser.sourceMonitor || {}).status === 'no-response') missing.push('monitor');
      return `${laser.target}: ${missing.join(' + ')}`;
    });
    setText('sensingBannerText', `${details.join('; ')}. Values are live raw ADC zeros, not hidden or simulated data.`);
  }
  updateConnectionState();
}

function applyNetwork(network = {}) {
  setText('headerApIp', network.wifi_ap_ip || '—');
  setText('headerStaIp', network.wifi_sta_ip || '—');
  setText('apSsid', network.wifi_ap_ssid || '—');
  setText('apIp', network.wifi_ap_ip || '192.168.4.1');
  const connected = Boolean(network.wifi_sta_connected);
  setText('stationSummary', connected ? (network.active_ssid || 'Connected') : 'Not connected');
  if (connected) {
    const quality = Number.isFinite(Number(network.wifi_sta_quality)) ? ` · ${formatInteger(network.wifi_sta_quality)}%` : '';
    const rssi = Number.isFinite(Number(network.wifi_sta_rssi)) ? `${formatInteger(network.wifi_sta_rssi)} dBm` : 'Signal available';
    setText('stationDetail', `${network.wifi_sta_ip || 'Address pending'} · ${rssi}${quality}`);
  } else {
    setText('stationDetail', network.active_ssid ? `Trying ${network.active_ssid}` : 'No saved network');
  }
}

function applySystem(state) {
  const device = state.device || {};
  const system = state.system || {};
  const firmware = system.firmware || {};
  setText('systemDeviceName', device.name || 'Vivonics Laser Controller');
  setText('systemDeviceId', device.uuid || '—');
  setText('firmwareVersion', firmware.projectVersion || '—');
  setText('firmwareBuild', firmware.buildDate ? `${firmware.buildDate} ${firmware.buildTime || ''} · IDF ${firmware.idfVersion || '—'}` : '—');
  setText('runningPartition', firmware.runningPartition || '—');
  setText('otaState', `OTA state ${firmware.otaState || '—'} · boot ${firmware.bootPartition || '—'}`);
  setText('nextPartition', firmware.nextUpdatePartition || '—');
  setText('otaCapacity', `${formatInteger(firmware.otaPartitionCount)} OTA slots · ${formatBytes(firmware.maxUploadBytes)} capacity`);
  setText('uptime', formatUptime(system.uptimeSeconds));
  setText('resetReason', `Reset: ${system.resetReason || '—'}`);
  setText('freeHeap', formatBytes(system.freeHeap));
  setText('minFreeHeap', `Minimum ${formatBytes(system.minFreeHeap)} · largest block ${formatBytes(system.largestFreeBlock)}`);
}

async function pollTelemetry() {
  if (telemetryRequestPending || document.hidden) return;
  telemetryRequestPending = true;
  try {
    const telemetry = await fetchJson('/api/telemetry');
    applyTelemetry(telemetry, true);
  } catch (_) {
    updateConnectionState();
  } finally {
    telemetryRequestPending = false;
  }
}

async function pollState() {
  if (stateRequestPending || document.hidden) return;
  stateRequestPending = true;
  try {
    const state = await fetchJson('/api/state');
    lastStateAt = Date.now();
    applyNetwork((state.device || {}).network || {});
    applySystem(state);
    applyTelemetry(state.telemetry, false);
  } catch (_) {
    updateConnectionState();
  } finally {
    stateRequestPending = false;
  }
}

async function sendAllOff(showConfirmation = true) {
  const response = await fetchJson('/api/lasers/off', { method: 'POST', body: '{}' });
  if (showConfirmation && response && response.ok) showToast('All laser outputs switched off');
  window.setTimeout(pollTelemetry, 50);
  return response;
}

function channelConfiguration(mask) {
  return LASER_ORDER.flatMap((target, index) => {
    if ((mask & (1 << index)) === 0) return [];
    const slider = document.querySelector(`.duty-slider[data-target="${target}"]`);
    return [{ target, dutyPermille: Number(slider.value) }];
  });
}

async function applyChannelMask(mask, message) {
  if (!controllerReady || otaInProgress) {
    showToast('Controller is not ready to activate an output', true);
    return;
  }
  commandPending = true;
  updateConnectionState();
  try {
    if (mask === 0) {
      await sendAllOff(false);
      showToast(message || 'All laser outputs switched off');
      return;
    }
    const channels = channelConfiguration(mask);
    const result = await fetchJson('/api/lasers', {
      method: 'POST',
      body: JSON.stringify({ channels }),
    });
    if (result && result.ok) showToast(message || `${result.target.replaceAll('_', ' + ')} queued`);
    window.setTimeout(pollTelemetry, 60);
  } catch (error) {
    showToast(`Output command failed: ${error.message}`, true);
  } finally {
    commandPending = false;
    window.setTimeout(updateConnectionState, 180);
  }
}

function initializeLaserControls() {
  all('.laser-activate').forEach((button) => {
    button.addEventListener('click', () => {
      const target = button.dataset.target;
      const channel = LASER_ORDER.indexOf(target);
      if (channel < 0) return;
      const wasActive = (currentOutput.channelMask & (1 << channel)) !== 0;
      const nextMask = currentOutput.channelMask ^ (1 << channel);
      applyChannelMask(nextMask, `${wasActive ? 'Removed' : 'Added'} ${target}`);
    });
  });
  byId('allOffButton').addEventListener('click', async () => {
    try { await sendAllOff(true); } catch (error) { showToast(`Unable to switch outputs off: ${error.message}`, true); }
  });
}

function renderScanResults(networks) {
  const grid = byId('wifiNetworkGrid');
  grid.replaceChildren();
  if (!networks.length) {
    const empty = document.createElement('div');
    empty.className = 'empty-panel';
    empty.textContent = 'No Wi-Fi networks were found.';
    grid.appendChild(empty);
    return;
  }
  networks.sort((a, b) => Number(b.rssi) - Number(a.rssi));
  networks.forEach((network) => {
    const card = document.createElement('button');
    card.type = 'button';
    card.className = 'wifi-network-card';
    const name = document.createElement('strong');
    name.className = 'wifi-network-name';
    name.textContent = network.ssid || '(hidden network)';
    const meta = document.createElement('span');
    meta.className = 'wifi-network-meta';
    meta.textContent = `${network.auth || 'Unknown'} · ch ${formatInteger(network.channel)} · ${formatInteger(network.rssi)} dBm`;
    card.append(name, meta);
    card.addEventListener('click', () => {
      byId('wifiSsid').value = network.ssid || '';
      byId('wifiPassword').focus();
      window.scrollTo({ top: byId('wifiForm').getBoundingClientRect().top + window.scrollY - 140, behavior: 'smooth' });
    });
    grid.appendChild(card);
  });
}

async function scanNetworks() {
  const button = byId('wifiScanButton');
  button.disabled = true;
  button.textContent = 'Scanning…';
  setText('scanSubtitle', 'The radio is scanning nearby access points.');
  try {
    const networks = await fetchJson('/api/wifi/scan', {}, 15000);
    renderScanResults(Array.isArray(networks) ? networks : []);
    setText('scanSubtitle', `${Array.isArray(networks) ? networks.length : 0} nearby networks found.`);
  } catch (error) {
    showToast(`Wi-Fi scan failed: ${error.message}`, true);
    setText('scanSubtitle', 'Scan failed; the live station connection was not changed.');
  } finally {
    button.disabled = false;
    button.textContent = 'Scan networks';
  }
}

function initializeNetworkControls() {
  byId('wifiScanButton').addEventListener('click', scanNetworks);
  byId('wifiForm').addEventListener('submit', async (event) => {
    event.preventDefault();
    const submit = event.currentTarget.querySelector('button[type="submit"]');
    submit.disabled = true;
    try {
      await fetchJson('/api/wifi', {
        method: 'POST',
        body: JSON.stringify({ ssid: byId('wifiSsid').value.trim(), password: byId('wifiPassword').value }),
      }, 5000);
      byId('wifiPassword').value = '';
      showToast('Wi-Fi credentials saved; connection is starting');
      window.setTimeout(pollState, 1200);
    } catch (error) {
      showToast(`Unable to save Wi-Fi: ${error.message}`, true);
    } finally {
      submit.disabled = false;
    }
  });
}

async function refreshLogs() {
  const list = byId('eventLog');
  try {
    const entries = await fetchJson('/api/logs');
    list.replaceChildren();
    if (!Array.isArray(entries) || entries.length === 0) {
      const empty = document.createElement('li');
      empty.className = 'empty-panel';
      empty.textContent = 'No device events recorded yet.';
      list.appendChild(empty);
      return;
    }
    entries.forEach((entry) => {
      const item = document.createElement('li');
      const time = document.createElement('time');
      time.textContent = `+${formatUptime(Number(entry.timestamp) / 1000)}`;
      const message = document.createElement('span');
      message.textContent = entry.message || 'Event';
      item.append(time, message);
      list.appendChild(item);
    });
  } catch (error) {
    showToast(`Unable to load event log: ${error.message}`, true);
  }
}

function setOtaProgress(percent, label) {
  const value = Math.max(0, Math.min(100, Math.round(percent)));
  byId('otaProgressPanel').hidden = false;
  setText('otaProgressLabel', label);
  setText('otaProgressValue', `${value}%`);
  byId('otaProgressBar').style.width = `${value}%`;
}

function uploadFirmware(file) {
  return new Promise((resolve, reject) => {
    const request = new XMLHttpRequest();
    request.open('POST', '/api/ota/upload');
    request.setRequestHeader('Content-Type', 'application/octet-stream');
    request.setRequestHeader('Accept', 'application/json');
    request.upload.addEventListener('progress', (event) => {
      if (event.lengthComputable) setOtaProgress((event.loaded / event.total) * 100, 'Uploading firmware…');
    });
    request.addEventListener('load', () => {
      let response = null;
      try { response = JSON.parse(request.responseText); } catch (_) { response = null; }
      if (request.status >= 200 && request.status < 300) resolve(response || {});
      else reject(new Error((response && response.message) || request.responseText || `HTTP ${request.status}`));
    });
    request.addEventListener('error', () => reject(new Error('Network connection failed')));
    request.addEventListener('abort', () => reject(new Error('Upload was aborted')));
    request.send(file);
  });
}

function initializeOta() {
  const fileInput = byId('otaFile');
  const uploadButton = byId('otaUploadButton');
  fileInput.addEventListener('change', () => {
    const file = fileInput.files[0];
    setText('otaFileLabel', file ? `${file.name} · ${formatBytes(file.size)}` : 'Choose ESP32 firmware binary');
    uploadButton.disabled = !file;
  });
  byId('otaForm').addEventListener('submit', async (event) => {
    event.preventDefault();
    const file = fileInput.files[0];
    if (!file) return;
    otaInProgress = true;
    uploadButton.disabled = true;
    all('.laser-activate, #allOffButton, #sensingTestButton').forEach((button) => { button.disabled = true; });
    setOtaProgress(0, 'Inhibiting outputs and starting upload…');
    try {
      const result = await uploadFirmware(file);
      setOtaProgress(100, `Installed to ${result.partition || 'next OTA slot'}; controller is rebooting…`);
      showToast('Firmware installed. Waiting for controller restart.');
      window.setTimeout(() => window.location.reload(), Number(result.rebootDelayMs || 1500) + 2500);
    } catch (error) {
      otaInProgress = false;
      uploadButton.disabled = false;
      setOtaProgress(0, 'Update failed; the current firmware remains active.');
      showToast(`OTA failed: ${error.message}`, true);
      updateConnectionState();
    }
  });
}

function initialize() {
  initializeTabs();
  initializeDutyControls();
  initializeLaserControls();
  initializeNetworkControls();
  initializeOta();
  byId('sensingTestButton').addEventListener('click', runSensingPinSelfTest);
  byId('refreshLogsButton').addEventListener('click', refreshLogs);
  updateConnectionState();
  pollState();
  pollTelemetry();
  window.setInterval(pollTelemetry, TELEMETRY_INTERVAL_MS);
  window.setInterval(pollState, STATE_INTERVAL_MS);
  window.setInterval(updateConnectionState, 750);
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) {
      pollState();
      pollTelemetry();
    }
  });
}

document.addEventListener('DOMContentLoaded', initialize);
