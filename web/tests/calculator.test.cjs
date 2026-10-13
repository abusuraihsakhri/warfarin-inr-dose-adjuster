'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const { reviewInr, previewWeeklyDose, parseMeasurements, rosendaal } = require('../calculator.js');

test('custom target is respected', () => {
  assert.equal(reviewInr(3.3, 2.5, 3.5, 'no').status, 'Within target');
  assert.equal(reviewInr(2.2, 2.5, 3.5, 'no').status, 'Below target');
  assert.equal(reviewInr(3.6, 2.5, 3.5, 'no').status, 'Above target');
});
test('bleeding and high INR are urgent without automatic orders', () => {
  for (const [inr, bleeding] of [[2.5, 'yes'], [5, 'no'], [10.1, 'unknown']]) {
    const r = reviewInr(inr, 2, 3, bleeding);
    assert.equal(r.severity, 'urgent');
    assert.equal(r.dose_order, null);
  }
});
test('reject invalid measurements and targets', () => {
  assert.throws(() => reviewInr(NaN), /finite positive/);
  assert.throws(() => reviewInr(2.5, 3, 2), /valid target/);
  assert.throws(() => previewWeeklyDose(Infinity, 0), /finite positive/);
  assert.throws(() => previewWeeklyDose(35, 200), /between/);
  assert.throws(() => parseMeasurements('0 2.5\n0 2.8'), /unique/);
  assert.throws(() => parseMeasurements('0 2.5\n7 NaN'), /finite/);
});
test('user-entered percentage is arithmetic only', () => {
  const r = previewWeeklyDose(35, -10);
  assert.equal(r.hypothetical_weekly_mg, 31.5);
  assert.equal(r.not_a_prescription, true);
});
test('Rosendaal clipping is correct in either direction', () => {
  for (const values of [[1, 4], [4, 1]]) {
    const r = rosendaal([{day:0,inr:values[0]}, {day:9,inr:values[1]}]);
    assert.ok(Math.abs(r.ttr_percent - 100/3) < 1e-9);
    assert.ok(Math.abs(r.days_in_range - 3) < 1e-9);
  }
  assert.equal(rosendaal(parseMeasurements('0,2.1\n14,2.8')).ttr_percent, 100);
});
