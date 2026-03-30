import { useState, useEffect, useCallback } from 'react';

// ─── Geolocation Hook ─────────────────────────────────────────────────────────
interface GeoState {
  latitude: number | null;
  longitude: number | null;
  accuracy: number | null;
  error: string | null;
  loading: boolean;
}

export function useGeolocation() {
  const [state, setState] = useState<GeoState>({
    latitude: null,
    longitude: null,
    accuracy: null,
    error: null,
    loading: true,
  });

  const getLocation = useCallback(() => {
    setState((s) => ({ ...s, loading: true, error: null }));
    if (!navigator.geolocation) {
      setState((s) => ({ ...s, loading: false, error: 'Geolocation is not supported by your browser.' }));
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setState({
          latitude: pos.coords.latitude,
          longitude: pos.coords.longitude,
          accuracy: pos.coords.accuracy,
          error: null,
          loading: false,
        });
      },
      (err) => {
        setState((s) => ({
          ...s,
          loading: false,
          error: err.code === 1
            ? 'Location access denied. Please enable location permissions.'
            : err.code === 3
            ? 'Location timed out. Please try again.'
            : 'Unable to determine your location. Please try again.',
        }));
      },
      { 
        enableHighAccuracy: false,  // ← was true, caused timeout
        timeout: 30000,             // ← was 10000, too short
        maximumAge: 60000           // ← was 30000, accept cached location
      }
    );
  }, []);

  useEffect(() => { getLocation(); }, [getLocation]);

  return { ...state, refresh: getLocation };
}

// ─── Device Fingerprint ────────────────────────────────────────────────────────
export function generateDeviceId(): string {
  const cached = localStorage.getItem('device_id');
  if (cached) return cached;

  const raw = [
    navigator.userAgent,
    navigator.language,
    screen.colorDepth,
    screen.width,
    screen.height,
    new Date().getTimezoneOffset(),
    navigator.hardwareConcurrency || 0,
  ].join('|');

  // Simple hash
  let hash = 0;
  for (let i = 0; i < raw.length; i++) {
    const char = raw.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash;
  }

  const id = Math.abs(hash).toString(36) + Date.now().toString(36);
  localStorage.setItem('device_id', id);
  return id;
}

// ─── Toast Notification ────────────────────────────────────────────────────────
type ToastType = 'success' | 'error' | 'info' | 'warning';

interface Toast {
  id: string;
  type: ToastType;
  message: string;
}

type ToastListener = (toasts: Toast[]) => void;

class ToastManager {
  private toasts: Toast[] = [];
  private listeners: ToastListener[] = [];

  subscribe(fn: ToastListener) {
    this.listeners.push(fn);
    return () => { this.listeners = this.listeners.filter((l) => l !== fn); };
  }

  private notify() {
    this.listeners.forEach((l) => l([...this.toasts]));
  }

  show(type: ToastType, message: string, duration = 4000) {
    const id = Date.now().toString();
    this.toasts = [...this.toasts, { id, type, message }];
    this.notify();
    setTimeout(() => {
      this.toasts = this.toasts.filter((t) => t.id !== id);
      this.notify();
    }, duration);
  }

  success = (msg: string) => this.show('success', msg);
  error = (msg: string) => this.show('error', msg, 5000);
  info = (msg: string) => this.show('info', msg);
  warning = (msg: string) => this.show('warning', msg);
}

export const toast = new ToastManager();

export function useToasts() {
  const [toasts, setToasts] = useState<Toast[]>([]);
  useEffect(() => toast.subscribe(setToasts), []);
  return toasts;
}

// ─── Format helpers ────────────────────────────────────────────────────────────
export function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString('en-LS', { hour: '2-digit', minute: '2-digit' });
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-LS', { day: 'numeric', month: 'short', year: 'numeric' });
}

export function formatHours(start: string, end: string | null): string {
  if (!end) return '—';
  const diff = (new Date(end).getTime() - new Date(start).getTime()) / 3600000;
  const h = Math.floor(diff);
  const m = Math.round((diff - h) * 60);
  return `${h}h ${m}m`;
}

export function getInitials(first: string, last: string): string {
  return `${first[0] ?? ''}${last[0] ?? ''}`.toUpperCase();
}

export function extractApiError(error: unknown): string {
  const err = error as { 
    response?: { data?: { detail?: string | Array<{msg: string}> } }; 
    message?: string 
  };
  const detail = err?.response?.data?.detail;
  if (Array.isArray(detail)) {
    return detail.map((d) => d.msg).join(', ');
  }
  if (typeof detail === 'string') return detail;
  return err?.message || 'Something went wrong.';
}
