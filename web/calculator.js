/* Browser-only research calculations. No network calls, persistence or automated medical dosing. */
(function (root) {
  'use strict';
  function finitePositive(value, name) {
    const number = typeof value === 'number' ? value : Number(value);
    if (!Number.isFinite(number) || number <= 0) throw new Error(name + ' must be a finite positive number.');
    return number;
  }
  function targetRange(low, high) {
    low = finitePositive(low, 'Target low');
    high = finitePositive(high, 'Target high');
    if (!(low < high && high <= 4.5)) throw new Error('Choose a valid target interval (low < high ≤ 4.5).');
    return { low, high };
  }
  function reviewInr(inr, low = 2, high = 3, bleeding = 'unknown') {
    inr = finitePositive(inr, 'INR');
    const target = targetRange(low, high);
    if (!['unknown', 'no', 'yes'].includes(bleeding)) throw new Error('Choose a bleeding status.');
    let status, severity = 'routine', message;
    if (bleeding === 'yes') {
      status = 'Bleeding reported';
      severity = 'urgent';
      message = 'Bleeding while receiving anticoagulation requires prompt medical assessment. Major or ongoing bleeding is an emergency.';
    } else if (inr > 10) {
      status = 'INR above 10';
      severity = 'urgent';
      message = 'Urgent clinician assessment is required. Treatment depends on bleeding, indication and individualized risk; this tool does not generate reversal orders.';
    } else if (inr > 4.5) {
      status = 'INR above 4.5';
      severity = 'urgent';
      message = 'Prompt clinician review is needed. Routine vitamin K is not suggested by CHEST for INR 4.5–10 without bleeding.';
    } else if (inr < target.low) {
      status = 'Below target';
      severity = 'review';
      message = 'Assess anticoagulation indication, adherence, recent changes, and thrombosis risk. No automatic dose change is issued.';
    } else if (inr > target.high) {
      status = 'Above target';
      severity = 'review';
      message = 'Assess bleeding risk, interacting medicines and the prescribing protocol. No automatic dose change is issued.';
    } else {
      status = 'Within target';
      message = 'Within the entered INR range. Follow-up depends on the individual clinical plan and stability.';
    }
    if (bleeding === 'unknown' && severity !== 'urgent') {
      message += ' Bleeding has not been assessed.';
    }
    return { inr, target_low: target.low, target_high: target.high, bleeding, status, severity, message, dose_order: null };
  }
  function previewWeeklyDose(weeklyDose, percentage) {
    weeklyDose = finitePositive(weeklyDose, 'Weekly dose');
    percentage = typeof percentage === 'number' ? percentage : Number(percentage);
    if (!Number.isFinite(percentage) || percentage < -100 || percentage > 100) {
      throw new Error('Manually entered change must be between −100% and +100%.');
    }
    const adjusted = weeklyDose * (1 + percentage / 100);
    return { previous_mg: weeklyDose, entered_percent: percentage, change_mg: weeklyDose * percentage / 100, hypothetical_weekly_mg: adjusted, hypothetical_daily_average_mg: adjusted / 7, not_a_prescription: true };
  }
  function parseMeasurements(raw) {
    if (typeof raw !== 'string') throw new Error('Provide measurement rows as text.');
    const lines = raw.trim().split(/\r?\n/);
    if (lines.length < 2) throw new Error('Enter at least two measurement rows.');
    if (lines.length > 1000) throw new Error('Maximum 1,000 rows.');
    const parsed = lines.map((line, i) => {
      const cols = line.trim().split(/[\s,;]+/).filter(Boolean);
      if (cols.length !== 2) throw new Error('Row ' + (i + 1) + ': use day, INR.');
      const day = Number(cols[0]);
      const inr = finitePositive(Number(cols[1]), 'INR at row ' + (i + 1));
      if (!Number.isFinite(day)) throw new Error('Day at row ' + (i + 1) + ' must be finite.');
      return { day, inr };
    }).sort((a, b) => a.day - b.day);
    for (let i = 1; i < parsed.length; i++) {
      if (parsed[i].day <= parsed[i - 1].day) throw new Error('Days must be unique.');
    }
    return parsed;
  }
  function rosendaal(rows, low = 2, high = 3) {
    const target = targetRange(low, high);
    if (!Array.isArray(rows) || rows.length < 2) throw new Error('At least two measurements required.');
    const sorted = rows.map(r => ({
      day: Number(r.day),
      inr: finitePositive(r.inr, 'INR')
    })).sort((a, b) => a.day - b.day);
    let total = 0, inRange = 0;
    for (let i = 1; i < sorted.length; i++) {
      const a = sorted[i - 1], b = sorted[i];
      if (!Number.isFinite(a.day) || !Number.isFinite(b.day) || b.day <= a.day) throw new Error('Days must be finite and unique.');
      const duration = b.day - a.day;
      total += duration;
      const fractions = [0, 1];
      if (a.inr !== b.inr) {
        for (const boundary of [target.low, target.high]) {
          const at = (boundary - a.inr) / (b.inr - a.inr);
          if (at > 0 && at < 1) fractions.push(at);
        }
      }
      fractions.sort((x, y) => x - y);
      for (let j = 1; j < fractions.length; j++) {
        const start = fractions[j - 1], end = fractions[j];
        const midpoint = a.inr + (b.inr - a.inr) * (start + end) / 2;
        if (midpoint >= target.low && midpoint <= target.high) inRange += (end - start) * duration;
      }
    }
    return { ttr_percent: 100 * inRange / total, days_in_range: inRange, observed_days: total, measurement_count: sorted.length, target_low: target.low, target_high: target.high, method: 'Rosendaal linear interpolation, no extrapolation' };
  }
  const api = { reviewInr, previewWeeklyDose, parseMeasurements, rosendaal };
  if (typeof module === 'object' && module.exports) module.exports = api;
  root.WarfarinWorkbench = api;

  if (typeof document !== 'undefined') {
    document.addEventListener('DOMContentLoaded', () => {
      const byId = id => document.getElementById(id);
      const number = (id, label) => {
        if (byId(id).value.trim() === '') throw new Error(label + ' is required.');
        return Number(byId(id).value);
      };
      const fmt = n => Number(n).toFixed(2);
      let lastReport = null;
      function renderError(box, error) {
        box.textContent = error.message;
        box.className = 'result error';
      }
      byId('inr-form').addEventListener('submit', e => {
        e.preventDefault();
        const box = byId('inr-result');
        lastReport = null;
        try {
          const low = number('target-low', 'Target low'), high = number('target-high', 'Target high');
          const report = reviewInr(number('inr', 'INR'), low, high, byId('bleeding').value);
          let text = report.status + ' — ' + report.message;
          if (report.severity !== 'urgent' && byId('weekly-dose').value.trim() !== '') {
            const hypothetical = previewWeeklyDose(number('weekly-dose', 'Weekly dose'), number('manual-change', 'Manual percentage'));
            text += '\n\nUser-entered arithmetic only: ' + fmt(hypothetical.previous_mg) + ' mg/week ' +
              (hypothetical.entered_percent >= 0 ? '+' : '') + fmt(hypothetical.entered_percent) +
              '% = ' + fmt(hypothetical.hypothetical_weekly_mg) + ' mg/week (' +
              fmt(hypothetical.hypothetical_daily_average_mg) + ' mg/day average). Not a prescribed regimen.';
            report.hypothetical_arithmetic = hypothetical;
          }
          box.textContent = text;
          box.className = 'result ' + (report.severity === 'urgent' ? 'urgent' : report.severity === 'review' ? 'caution' : 'ok');
          lastReport = { type: 'inr-review', ...report };
        } catch (err) { renderError(box, err); }
      });
      byId('ttr-form').addEventListener('submit', e => {
        e.preventDefault();
        const box = byId('ttr-result');
        lastReport = null;
        try {
          const rows = parseMeasurements(byId('measurements').value);
          const r = rosendaal(rows, number('target-low', 'Target low'), number('target-high', 'Target high'));
          box.textContent = 'Interpolated TTR: ' + fmt(r.ttr_percent) + '% (' + fmt(r.days_in_range) +
            ' of ' + fmt(r.observed_days) + ' observed days, ' + r.measurement_count +
            ' measurements). No extrapolation beyond first/last INR.';
          box.className = 'result ok';
          lastReport = { type: 'ttr', ...r };
        } catch (err) { renderError(box, err); }
      });
      byId('export-json').addEventListener('click', () => {
        if (!lastReport) { renderError(byId('download-status'), new Error('Run a calculation before exporting.')); return; }
        const blob = new Blob([JSON.stringify(lastReport, null, 2) + '\n'], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const anchor = document.createElement('a');
        anchor.href = url;
        anchor.download = 'warfarin-research-result.json';
        document.body.appendChild(anchor);
        anchor.click();
        anchor.remove();
        URL.revokeObjectURL(url);
        byId('download-status').textContent = 'The research result was exported locally.';
        byId('download-status').className = 'status';
      });
    });
  }
})(typeof globalThis !== 'undefined' ? globalThis : this);
