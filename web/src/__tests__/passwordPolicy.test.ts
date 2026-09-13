import { describe, it, expect } from 'vitest';
import { getPasswordError, getPasswordRequirements, passwordsMatch, PASSWORD_MESSAGES } from '../lib/passwordPolicy';

describe('passwordPolicy (Web)', () => {
  it('validates a strong password successfully', () => {
    const error = getPasswordError('Haslo123!');
    expect(error).toBeNull();
  });

  it('rejects empty password', () => {
    const error = getPasswordError('');
    expect(error).toBe(PASSWORD_MESSAGES.required);
  });

  it('rejects passwords that are too short', () => {
    const error = getPasswordError('H1!');
    expect(error).toBe(PASSWORD_MESSAGES.tooShort);
  });

  it('rejects passwords consisting entirely of numbers', () => {
    const error = getPasswordError('123456789');
    expect(error).toBe(PASSWORD_MESSAGES.entirelyNumeric);
  });

  it('rejects passwords missing special characters', () => {
    const error = getPasswordError('Haslo12345');
    expect(error).toBe(PASSWORD_MESSAGES.noSpecial);
  });

  it('detects passwords too similar to user hints', () => {
    const error = getPasswordError('JanKowalski123!', { firstName: 'Jan', lastName: 'Kowalski' });
    expect(error).toBe(PASSWORD_MESSAGES.tooSimilar);
  });

  it('verifies passwords match check', () => {
    expect(passwordsMatch('Haslo123!', 'Haslo123!')).toBe(true);
    expect(passwordsMatch('Haslo123!', 'InneHaslo123!')).toBe(false);
  });
});
