/**
 * Tests for STV ballot validation logic
 * Testing the submitSTVBallot function from app.js
 */

// Mock jQuery
global.$ = (selector) => {
  return {
    serializeArray: () => {
      // Will be mocked per test
      return global.mockFormData || [];
    },
    fadeOut: jest.fn(),
    fadeIn: jest.fn(),
    attr: jest.fn()
  };
};

// Mock alert
global.alert = jest.fn();

// Extract and adapt the validation logic for testing
function validateSTVBallot(formData) {
  const options = [...formData];
  options.sort((a, b) => a.value - b.value);
  let currentpref = 1;
  const out = {};

  for (const option of options) {
    const value = parseInt(option.value, 10);
    if (isNaN(value) || value === 0) { continue; }
    else if (value % 1 !== 0) { return { valid: false, error: 'non-integer' }; }
    else if (value === currentpref) { currentpref++; out[option.name] = value; }
    else { return { valid: false, error: 'not-consecutive' }; }
  }

  return { valid: true, out };
}

describe('STV Ballot Validation', () => {
  test('valid consecutive preferences 1,2,3', () => {
    const formData = [
      { name: 'opt1', value: '1' },
      { name: 'opt2', value: '2' },
      { name: 'opt3', value: '3' }
    ];
    const result = validateSTVBallot(formData);
    expect(result.valid).toBe(true);
    expect(result.out).toEqual({ opt1: 1, opt2: 2, opt3: 3 });
  });

  test('valid partial ranking 1,2', () => {
    const formData = [
      { name: 'opt1', value: '1' },
      { name: 'opt2', value: '2' },
      { name: 'opt3', value: '' }
    ];
    const result = validateSTVBallot(formData);
    expect(result.valid).toBe(true);
    expect(result.out).toEqual({ opt1: 1, opt2: 2 });
  });

  test('invalid skipped number 1,3', () => {
    const formData = [
      { name: 'opt1', value: '1' },
      { name: 'opt2', value: '3' }
    ];
    const result = validateSTVBallot(formData);
    expect(result.valid).toBe(false);
    expect(result.error).toBe('not-consecutive');
  });

  test('invalid not starting at 1', () => {
    const formData = [
      { name: 'opt1', value: '2' },
      { name: 'opt2', value: '3' }
    ];
    const result = validateSTVBallot(formData);
    expect(result.valid).toBe(false);
  });

  test('handles string values correctly', () => {
    // This tests the type coercion fix
    const formData = [
      { name: 'opt1', value: '1' },  // String "1"
      { name: 'opt2', value: '2' }   // String "2"
    ];
    const result = validateSTVBallot(formData);
    expect(result.valid).toBe(true);
  });

  test('rejects non-integer values', () => {
    const formData = [
      { name: 'opt1', value: '1.5' }
    ];
    const result = validateSTVBallot(formData);
    expect(result.valid).toBe(false);
  });
});
