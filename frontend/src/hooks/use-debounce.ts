"use client";

import { useEffect, useState } from "react";

/**
 * Debounce een waarde — geeft pas de nieuwe waarde terug nadat `delay` ms
 * geen wijziging is geweest. Voor zoekvelden: voorkomt een API-call per
 * toetsaanslag.
 */
export function useDebounce<T>(value: T, delay = 300): T {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debounced;
}
