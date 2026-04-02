import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import QRCode from 'qrcode';
import api from '../api/client';
import type { KioskQRData } from '../types/api';
import {
  isKioskUnlocked,
  unlockKiosk,
  lockKiosk,
  validateKioskPin,
} from '../utils/helpers';

type Mode = 'checkin' | 'checkout';

// ─── API ───────────────────────────────────────────────────────────────────────
async function fetchKioskQR(): Promise<KioskQRData> {
  const { data } = await api.get<KioskQRData>('/kiosk/today');
  return data;
}

async function buildQRImage(text: string, color: string): Promise<string> {
  return QRCode.toDataURL(text, {
    width: 300,
    margin: 2,
    color: { dark: color, light: '#ffffff' },
    errorCorrectionLevel: 'H',
  });
}

// ─── Countdown to midnight ─────────────────────────────────────────────────────
function useCountdown(expiresAt: string | null): string {
  const [timeLeft, setTimeLeft] = useState('--:--:--');
  useEffect(() => {
    const getTarget = () => {
      if (expiresAt) return new Date(expiresAt).getTime();
      const midnight = new Date();
      midnight.setHours(24, 0, 0, 0);
      return midnight.getTime();
    };
    const tick = () => {
      const diff = getTarget() - Date.now();
      if (diff <= 0) { setTimeLeft('00:00:00'); return; }
      const h = Math.floor(diff / 3_600_000);
      const m = Math.floor((diff % 3_600_000) / 60_000);
      const s = Math.floor((diff % 60_000) / 1_000);
      setTimeLeft(`${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`);
    };
    tick();
    const id = setInterval(tick, 1_000);
    return () => clearInterval(id);
  }, [expiresAt]);
  return timeLeft;
}

function useClock() {
  const [now, setNow] = useState(new Date());
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1_000);
    return () => clearInterval(id);
  }, []);
  return now;
}

// ─── PIN Setup Screen ─────────────────────────────────────────────────────────
function PinSetupScreen({ onUnlocked }: { onUnlocked: () => void }) {
  const navigate = useNavigate();
  const [pin, setPin] = useState('');
  const [error, setError] = useState('');
  const [attempts, setAttempts] = useState(0);

  const handleSubmit = () => {
    if (validateKioskPin(pin)) {
      unlockKiosk();
      onUnlocked();
    } else {
      setAttempts((a) => a + 1);
      setError(`Incorrect PIN. ${3 - attempts - 1 > 0 ? `${3 - attempts - 1} attempts remaining.` : 'Redirecting...'}`);
      setPin('');
      if (attempts >= 2) {
        setTimeout(() => navigate('/login'), 1500);
      }
    }
  };

  return (
    <div
      className="min-h-screen flex items-center justify-center"
      style={{ background: 'linear-gradient(160deg, #001a6e 0%, #002395 50%, #001470 100%)' }}
    >
      {/* Decorative circles */}
      <div className="absolute top-0 right-0 w-96 h-96 rounded-full opacity-10"
        style={{ background: 'radial-gradient(circle, #00A550, transparent)' }} />
      <div className="absolute bottom-0 left-0 w-64 h-64 rounded-full opacity-10"
        style={{ background: 'radial-gradient(circle, white, transparent)' }} />

      <div className="relative bg-white rounded-3xl p-10 w-full max-w-sm mx-4 shadow-2xl animate-slide-up">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4"
            style={{ background: '#002395' }}>
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
                d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002
                2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 font-display">Kiosk Setup</h2>
          <p className="text-sm text-gray-400 mt-1">Ministry of Health · Lesotho</p>
        </div>

        <p className="text-sm text-gray-500 text-center mb-6">
          Enter the Ministry kiosk PIN to activate this device as an attendance kiosk.
          Contact your IT administrator if you don't have the PIN.
        </p>

        {/* Lesotho flag stripe */}
        <div className="flex h-1 rounded-full overflow-hidden gap-0.5 mb-6">
          <div className="flex-1 bg-[#002395]" />
          <div className="flex-1 bg-gray-200" />
          <div className="flex-1 bg-[#00A550]" />
        </div>

        <label className="input-label">Kiosk PIN</label>
        <input
          type="password"
          inputMode="text"
          placeholder="Enter kiosk PIN"
          value={pin}
          onChange={(e) => { setPin(e.target.value); setError(''); }}
          onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
          className={`input-field text-center text-lg tracking-widest mb-3 ${
            error ? 'border-red-400 focus:ring-red-400' : ''
          }`}
          autoFocus
        />

        {error && (
          <p className="text-xs text-red-500 text-center mb-3">{error}</p>
        )}

        <button
          onClick={handleSubmit}
          disabled={!pin.trim()}
          className="btn-primary w-full mb-3"
        >
          Activate Kiosk
        </button>

        <button
          onClick={() => navigate('/login')}
          className="w-full text-sm text-gray-400 hover:text-gray-600 py-2 transition-colors"
        >
          Not a kiosk device? Sign in →
        </button>
      </div>
    </div>
  );
}

// ─── Admin settings modal ──────────────────────────────────────────────────────
function AdminModal({ onClose }: { onClose: () => void }) {
  const navigate = useNavigate();
  const [pin, setPin] = useState('');
  const [error, setError] = useState('');

  const handleUnlock = () => {
    if (validateKioskPin(pin)) {
      lockKiosk();
      navigate('/login');
    } else {
      setError('Incorrect PIN.');
      setPin('');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />
      <div className="relative card p-8 w-72 animate-slide-up text-center">
        <h3 className="font-bold text-gray-900 font-display mb-1">Admin Access</h3>
        <p className="text-sm text-gray-400 mb-5">
          Enter PIN to exit kiosk mode
        </p>
        <input
          type="password"
          placeholder="Enter kiosk PIN"
          value={pin}
          onChange={(e) => { setPin(e.target.value); setError(''); }}
          onKeyDown={(e) => e.key === 'Enter' && handleUnlock()}
          className={`input-field text-center tracking-widest mb-3 ${
            error ? 'border-red-400 focus:ring-red-400' : ''
          }`}
          autoFocus
        />
        {error && <p className="text-xs text-red-500 mb-3">{error}</p>}
        <button onClick={handleUnlock} className="btn-primary w-full mb-2">
          Exit Kiosk Mode
        </button>
        <button onClick={onClose}
          className="w-full text-sm text-gray-400 hover:text-gray-600 py-2">
          Cancel
        </button>
      </div>
    </div>
  );
}

// ─── Main Kiosk Display ────────────────────────────────────────────────────────
function KioskDisplay() {
  const [mode, setMode] = useState<Mode>('checkin');
  const [qrImage, setQrImage] = useState<string | null>(null);
  const [showAdmin, setShowAdmin] = useState(false);
  const now = useClock();

  const { data: kioskData, isLoading, isError, refetch } = useQuery({
    queryKey: ['kiosk-qr'],
    queryFn: fetchKioskQR,
    staleTime: 60_000,
    retry: 1,
  });

  const countdown = useCountdown(kioskData?.expires_at ?? null);
  const modeColor = mode === 'checkin' ? '#002395' : '#00A550';
  const modeLabel = mode === 'checkin' ? 'Check In' : 'Check Out';

  const generateImage = useCallback(async () => {
    let text: string;
    if (kioskData) {
      text = mode === 'checkin' ? kioskData.checkin_qr : kioskData.checkout_qr;
    } else {
      text = JSON.stringify({
        type: mode,
        date: new Date().toISOString().split('T')[0],
        token: 'PENDING_BACKEND_IMPLEMENTATION',
      });
    }
    const img = await buildQRImage(text, modeColor);
    setQrImage(img);
  }, [mode, kioskData, modeColor]);

  useEffect(() => { generateImage(); }, [generateImage]);

  // Auto-refresh at midnight
  useEffect(() => {
    const midnight = new Date();
    midnight.setHours(24, 0, 0, 0);
    const ms = midnight.getTime() - Date.now();
    const id = setTimeout(() => refetch(), ms);
    return () => clearTimeout(id);
  }, [refetch]);

  const dateStr = now.toLocaleDateString('en-LS', {
    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
  });
  const timeStr = now.toLocaleTimeString('en-LS', {
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  });

  return (
    <div
      className="min-h-screen flex flex-col select-none"
      style={{ background: 'linear-gradient(160deg, #f0f2f7 0%, #e8eaf6 100%)' }}
    >
      {/* Top bar */}
      <header className="flex items-center justify-between px-6 py-4 animate-fade-in">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center"
            style={{ background: '#002395' }}>
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor"
              viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
                d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4
                12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1
                1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1
                0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0
                001 1z" />
            </svg>
          </div>
          <div>
            <p className="font-bold text-gray-900 font-display text-sm leading-tight">
              Hospital Attendance Kiosk
            </p>
            <p className="text-xs text-gray-400">Ministry of Health · Lesotho</p>
          </div>
        </div>

        {/* Live clock */}
        <div className="text-center">
          <p className="text-2xl font-bold text-gray-900 font-display tabular-nums">
            {timeStr}
          </p>
          <p className="text-xs text-gray-400">{dateStr}</p>
        </div>

        {/* Settings gear */}
        <button
          onClick={() => setShowAdmin(true)}
          title="Admin settings"
          className="p-2 rounded-xl text-gray-300 hover:text-gray-500
            hover:bg-white/60 transition-colors"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
              d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0
              002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065
              2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066
              2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572
              1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0
              00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0
              00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0
              001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07
              2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
              d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </button>
      </header>

      {/* Main content */}
      <main className="flex-1 flex flex-col items-center justify-center gap-6 px-4 py-6">
        <div className="text-center animate-fade-in">
          <h1 className="text-3xl font-bold text-gray-900 font-display">
            Scan with your phone
          </h1>
          <p className="text-gray-400 mt-1">
            Open the Attendance app and scan the code below to record your attendance
          </p>
        </div>

        <div className="card p-6 flex flex-col items-center gap-5 w-full max-w-xs animate-slide-up">
          {/* Toggle */}
          <div className="card p-1 flex gap-1 w-full" style={{ background: '#f8f9ff' }}>
            {(['checkin', 'checkout'] as Mode[]).map((m) => (
              <button
                key={m}
                onClick={() => setMode(m)}
                className={`flex-1 py-2.5 px-3 rounded-xl text-sm font-semibold
                  transition-all duration-200 ${
                  mode === m ? 'text-white shadow-sm' : 'text-gray-400 hover:text-gray-600'
                }`}
                style={mode === m ? { background: modeColor } : {}}
              >
                {m === 'checkin' ? '→ Check In' : '← Check Out'}
              </button>
            ))}
          </div>

          {/* QR Code */}
          {isLoading ? (
            <div className="w-64 h-64 flex items-center justify-center">
              <div className="flex flex-col items-center gap-3">
                <svg className="w-8 h-8 animate-spin" style={{ color: modeColor }}
                  fill="none" viewBox="0 0 24 24">
                  <circle cx="12" cy="12" r="10" stroke="#e5e7eb" strokeWidth="3" />
                  <path d="M12 2a10 10 0 0 1 10 10" stroke={modeColor}
                    strokeWidth="3" strokeLinecap="round" />
                </svg>
                <p className="text-sm text-gray-400">Generating today's QR…</p>
              </div>
            </div>
          ) : (
            <>
              {isError && (
                <div className="w-full flex items-start gap-2 bg-amber-50 border
                  border-amber-200 text-amber-700 rounded-xl px-3 py-2 text-xs">
                  <svg className="w-4 h-4 shrink-0 mt-0.5" fill="none"
                    stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2
                      2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
                  </svg>
                  <span>Kiosk endpoint pending — showing placeholder QR</span>
                </div>
              )}
              {qrImage && (
                <div className="relative">
                  <img
                    src={qrImage}
                    alt={`${modeLabel} QR code`}
                    className="w-64 h-64 rounded-2xl"
                    style={{ imageRendering: 'pixelated' }}
                  />
                  <div
                    className="absolute -top-2 -right-2 px-2.5 py-0.5 rounded-full
                      text-white text-[10px] font-bold uppercase tracking-widest"
                    style={{ background: modeColor }}
                  >
                    {mode === 'checkin' ? 'IN' : 'OUT'}
                  </div>
                </div>
              )}
              <p className="text-sm text-gray-400 text-center">
                {modeLabel} · {new Date().toLocaleDateString('en-LS')}
              </p>
            </>
          )}
        </div>

        {/* Countdown */}
        <div className="flex items-center gap-2 text-sm text-gray-400 animate-fade-in">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>
            QR refreshes in{' '}
            <span className="font-bold tabular-nums text-gray-700">{countdown}</span>
          </span>
        </div>
      </main>

      {/* Footer */}
      <footer className="flex items-center justify-center gap-3 py-4 animate-fade-in">
        <div className="flex h-1 w-16 rounded-full overflow-hidden gap-0.5">
          <div className="flex-1 bg-[#002395]" />
          <div className="flex-1 bg-white border border-gray-200" />
          <div className="flex-1 bg-[#00A550]" />
        </div>
        <p className="text-xs text-gray-400">
          Ministry of Health Lesotho · Secure Attendance Platform
        </p>
      </footer>

      {showAdmin && <AdminModal onClose={() => setShowAdmin(false)} />}
    </div>
  );
}

// ─── Kiosk Page — entry point ──────────────────────────────────────────────────
export function KioskPage() {
  const [unlocked, setUnlocked] = useState<boolean | null>(null);

  useEffect(() => {
    // Check if this device is already unlocked as a kiosk
    const kioskUnlocked = isKioskUnlocked();
    if (kioskUnlocked) {
      setUnlocked(true);
    } else {
      setUnlocked(false);
    }
  }, []);

  // Loading state while checking localStorage
  if (unlocked === null) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#002395]">
        <div className="w-8 h-8 border-4 border-white/30 border-t-white rounded-full animate-spin" />
      </div>
    );
  }

  // Not unlocked — show PIN setup screen
  if (!unlocked) {
    return (
      <PinSetupScreen
        onUnlocked={() => setUnlocked(true)}
      />
    );
  }

  // Unlocked — show the kiosk display
  return <KioskDisplay />;
}
