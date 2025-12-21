/**
 * Allowed Users Configuration
 * Only these specific people can access the dashboard
 */

export const ALLOWED_NAMES = [
  'chandana',
  'nagendra',
  'gundamma',
  'pavan',
  'rachana',
  'tn',
];

// Case-insensitive check
export function isNameAllowed(name: string): boolean {
  return ALLOWED_NAMES.includes(name.toLowerCase().trim());
}
