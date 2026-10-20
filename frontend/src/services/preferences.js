// Preserve the legacy preference keys; privacy/storage restrictions are non-fatal.
export function read(key,fallback) {
  try { return localStorage.getItem(key)||fallback; }
  catch { return fallback; }
}
export function save(key,value) {
  try { localStorage.setItem(key,value); return true; }
  catch { return false; }
}
