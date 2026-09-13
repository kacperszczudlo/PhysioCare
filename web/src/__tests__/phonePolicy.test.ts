import { describe, it, expect } from 'vitest';
import { getPhoneError, formatPhoneForApi, parseStoredPhone, PHONE_MESSAGES } from '../lib/phonePolicy';

describe('phonePolicy (Web)', () => {
  it('formats phone for API correctly', () => {
    const formatted = formatPhoneForApi('123456789', 'PL');
    expect(formatted).toBe('+48123456789');
  });

  it('parses stored phone into parts', () => {
    const parts = parseStoredPhone('+48123456789');
    expect(parts.countryCode).toBe('PL');
    expect(parts.nationalNumber).toBe('123456789');
  });

  it('validates a valid national phone number', () => {
    const error = getPhoneError('123456789', 'PL');
    expect(error).toBeNull();
  });

  it('rejects phone number starting with zero or too short', () => {
    const error = getPhoneError('012', 'PL');
    expect(error).toBe(PHONE_MESSAGES.invalid);
  });
});
