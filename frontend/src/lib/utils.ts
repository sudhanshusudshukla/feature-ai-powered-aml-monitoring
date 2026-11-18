/**
 * Utility functions for the AML monitoring frontend
 */

/**
 * Format currency amount in INR with Indian digit grouping
 */
export function formatInr(amount: number, includeSymbol = true): string {
  const formatted = new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
  }).format(amount);
  return includeSymbol ? formatted : formatted.replace(/^₹/, '');
}

/**
 * Format large amounts in lakhs/crores (short form)
 */
export function formatInrShort(amount: number): string {
  if (amount >= 10000000) {
    return `₹${(amount / 10000000).toFixed(1)} Cr`;
  }
  if (amount >= 100000) {
    return `₹${(amount / 100000).toFixed(1)} L`;
  }
  return formatInr(amount);
}

/**
 * Format date-time in DD MMM YYYY, HH:mm format
 */
export function formatDateTime(iso: string): string {
  return new Intl.DateTimeFormat('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(iso));
}

/**
 * Format relative time (e.g., "2 h ago")
 */
export function formatRelativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const minutes = Math.floor(diff / 60000);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

/**
 * Truncate UUID to first 8 characters
 */
export function truncateId(id: string): string {
  return id.substring(0, 8) + '…';
}

/**
 * Simple class name combiner
 */
export function cn(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(' ');
}
