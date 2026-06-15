export function cn(...classes) {
  return classes.filter(Boolean).join(' ')
}

export function formatCurrency(value) {
  const number = Number(value ?? 0)
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 2,
  }).format(number)
}

export function formatNumber(value, max = 2) {
  const number = Number(value ?? 0)
  return new Intl.NumberFormat('en-US', { maximumFractionDigits: max }).format(number)
}

export function toTitle(pathname) {
  const clean = pathname.replace(/^\//, '') || 'dashboard'
  return clean
    .split('-')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')
}
