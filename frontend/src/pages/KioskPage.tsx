import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import QRCode from 'qrcode';
import { kioskApi, type KioskCurrentSession, type KioskDepartment } from '../api/kiosk';
import {
  isKioskUnlocked,
  unlockKiosk,
  lockKiosk,
  validateKioskPin,
} from '../utils/helpers';

type Mode = 'checkin' | 'checkout';

async function buildQRImage(text: string, color: string): Promise<string> {
  return QRCode.toDataURL(text, {
    width: 320,
    margin: 2,
    color: { dark: color, light: '#ffffff' },
    errorCorrectionLevel: 'H',
  });
}

function useClock() {
  const [now, setNow] = useState(new Date());
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000);
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
      const next = attempts + 1;
      setAttempts(next);
      if (next >= 3) {
        setError('Too many attempts. Redirecting…');
        setTimeout(() => navigate('/login'), 1500);
      } else {
        setError(`Incorrect PIN. ${3 - next} attempt${3 - next === 1 ? '' : 's'} remaining.`);
      }
      setPin('');
    }
  };

  return (
    <div
      className="min-h-screen flex items-center justify-center relative overflow-hidden"
      style={{ background: 'linear-gradient(160deg, #001a6e 0%, #002395 50%, #001470 100%)' }}
    >
      <div className="absolute top-0 right-0 w-96 h-96 rounded-full opacity-10"
        style={{ background: 'radial-gradient(circle, #00A550, transparent)' }} />
      <div className="absolute bottom-0 left-0 w-64 h-64 rounded-full opacity-10"
        style={{ background: 'radial-gradient(circle, white, transparent)' }} />

      <div className="relative bg-white rounded-3xl p-10 w-full max-w-sm mx-4
        shadow-2xl animate-slide-up">
        <div className="text-center mb-8">
          <div className="w-16 h-16 rounded-2xl flex items-center justify-center
            mx-auto mb-4" style={{ background: '#002395' }}>
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor"
              viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
                d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2
                2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 font-display">Kiosk Setup</h2>
          <p className="text-sm text-gray-400 mt-1">Ministry of Health · Lesotho</p>
        </div>

        <p className="text-sm text-gray-500 text-center mb-6">
          Enter the Ministry kiosk PIN to activate this device as an attendance kiosk.
        </p>

        <div className="flex h-1 rounded-full overflow-hidden gap-0.5 mb-6">
          <div className="flex-1 bg-[#002395]" />
          <div className="flex-1 bg-gray-200" />
          <div className="flex-1 bg-[#00A550]" />
        </div>

        <label className="input-label">Kiosk PIN</label>
        <input
          type="password"
          placeholder="Enter kiosk PIN"
          value={pin}
          onChange={(e) => { setPin(e.target.value); setError(''); }}
          onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
          className={`input-field text-center text-lg tracking-widest mb-3 ${
            error ? 'border-red-400 focus:ring-red-400' : ''
          }`}
          autoFocus
        />
        {error && <p className="text-xs text-red-500 text-center mb-3">{error}</p>}

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
          Not a kiosk? Sign in →
        </button>
      </div>
    </div>
  );
}

// ─── Admin Modal ──────────────────────────────────────────────────────────────
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
        <p className="text-sm text-gray-400 mb-5">Enter PIN to exit kiosk mode</p>
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

// ─── Kiosk Display ────────────────────────────────────────────────────────────
function KioskDisplay() {
  const [mode, setMode] = useState<Mode>('checkin');
  const [selectedDept, setSelectedDept] = useState('');
  const [departments, setDepartments] = useState<KioskDepartment[]>([]);
  const [currentSession, setCurrentSession] = useState<KioskCurrentSession | null>(null);
  const [qrImage, setQrImage] = useState<string | null>(null);
  const [showAdmin, setShowAdmin] = useState(false);
  const [isIdle, setIsIdle] = useState(true); // no active session
  const now = useClock();

  // Fetch departments once
  useEffect(() => {
    kioskApi.getLocations()
      .then((r) => setDepartments(r.locations))
      .catch(() => {});
  }, []);

  // Generate QR image from session data
  const generateImage = useCallback(async (session: KioskCurrentSession) => {
    const color = mode === 'checkin' ? '#002395' : '#00A550';
    const img = await buildQRImage(session.qr_data, color);
    setQrImage(img);
  }, [mode]);

  // Poll for current session every 2 seconds
  useEffect(() => {
    const poll = async () => {
      try {
        const session = await kioskApi.getCurrentSession(
          mode,
          selectedDept || undefined
        );
        if (session) {
          setCurrentSession(session);
          setIsIdle(false);
          await generateImage(session);
        } else {
          setCurrentSession(null);
          setIsIdle(true);
          setQrImage(null);
        }
      } catch {
        // keep polling silently
      }
    };

    poll(); // immediate first call
    const id = setInterval(poll, 2000);
    return () => clearInterval(id);
  }, [mode, selectedDept, generateImage]);

  const timeStr = now.toLocaleTimeString('en-LS', {
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  });
  const dateStr = now.toLocaleDateString('en-LS', {
    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
  });
  const modeColor = mode === 'checkin' ? '#002395' : '#00A550';

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
            <p className="font-bold text-gray-900 font-display text-sm">
              Hospital Attendance Kiosk
            </p>
            <p className="text-xs text-gray-400">Ministry of Health · Lesotho</p>
          </div>
        </div>

        <div className="text-center">
          <p className="text-2xl font-bold text-gray-900 font-display tabular-nums">
            {timeStr}
          </p>
          <p className="text-xs text-gray-400">{dateStr}</p>
        </div>

        <button
          onClick={() => setShowAdmin(true)}
          className="p-2 rounded-xl text-gray-300 hover:text-gray-500 hover:bg-white/60 transition-colors"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
              d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573
              1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426
              1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37
              2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724
              1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0
              00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31
              2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
              d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </button>
      </header>

      {/* Main */}
      <main className="flex-1 flex flex-col items-center justify-center gap-6 px-4 py-6">

        {/* Mode toggle */}
        <div className="card p-1 flex gap-1 w-full max-w-xs">
          {(['checkin', 'checkout'] as Mode[]).map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`flex-1 py-3 px-4 rounded-xl text-sm font-semibold
                transition-all duration-200 ${
                mode === m ? 'text-white shadow-sm' : 'text-gray-400 hover:text-gray-600'
              }`}
              style={mode === m ? { background: modeColor } : {}}
            >
              {m === 'checkin' ? '→ Check In' : '← Check Out'}
            </button>
          ))}
        </div>

        {/* Department selector */}
        {departments.length > 0 && (
          <select
            value={selectedDept}
            onChange={(e) => setSelectedDept(e.target.value)}
            className="input-field w-full max-w-xs text-sm text-center"
          >
            <option value="">All Departments</option>
            {departments.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name} — {d.location}
              </option>
            ))}
          </select>
        )}

        {/* QR Card */}
        <div className="card p-6 flex flex-col items-center gap-4 w-full max-w-xs animate-slide-up">
          {isIdle ? (
            /* Waiting state */
            <div className="w-full py-8 flex flex-col items-center gap-4">
              <div className="w-20 h-20 rounded-2xl bg-gray-100 flex items-center
                justify-center">
                <svg className="w-10 h-10 text-gray-300" fill="none" stroke="currentColor"
                  viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                    d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="text-center">
                <p className="font-bold text-gray-700 font-display">
                  Waiting for employee
                </p>
                <p className="text-sm text-gray-400 mt-1">
                  Tap <strong>Check In</strong> or <strong>Check Out</strong> on your phone
                </p>
              </div>
              {/* Animated dots */}
              <div className="flex gap-1.5">
                {[0, 1, 2].map((i) => (
                  <div
                    key={i}
                    className="w-2 h-2 rounded-full bg-gray-300"
                    style={{
                      animation: `bounce 1.2s ease-in-out ${i * 0.2}s infinite alternate`,
                    }}
                  />
                ))}
              </div>
            </div>
          ) : (
            /* Active session */
            <>
              {currentSession && (
                <div className="w-full text-center">
                  <div className="flex items-center justify-center gap-2 mb-3">
                    <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                    <p className="text-sm font-semibold text-emerald-700">
                      Ready for {currentSession.employee_name}
                    </p>
                  </div>
                </div>
              )}

              {qrImage && (
                <div className="relative">
                  <img
                    src={qrImage}
                    alt="Session QR code"
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

              <div className="text-center">
                <p className="font-bold text-gray-900 font-display">
                  {mode === 'checkin' ? 'Scan to Check In' : 'Scan to Check Out'}
                </p>
                <p className="text-xs text-gray-400 mt-0.5">
                  Open the Attendance app on your phone
                </p>
              </div>
            </>
          )}
        </div>

        {/* Instructions */}
        <div className="text-center max-w-xs animate-fade-in">
          <p className="text-sm text-gray-400">
            {isIdle
              ? 'Open the Attendance app on your phone and tap Check In or Check Out to join the queue'
              : 'This QR is unique to you — scan it with your phone to continue'}
          </p>
        </div>
      </main>

      {/* Footer */}
      <footer className="flex items-center justify-center gap-3 py-4">
        <div className="flex h-1 w-16 rounded-full overflow-hidden gap-0.5">
          <div className="flex-1 bg-[#002395]" />
          <div className="flex-1 bg-white border border-gray-200" />
          <div className="flex-1 bg-[#00A550]" />
        </div>
        <p className="text-xs text-gray-400">
          Ministry of Health Lesotho · Secure Attendance Platform
        </p>
      </footer>

      <style>{`
        @keyframes bounce {
          from { transform: translateY(0); opacity: 0.4; }
          to   { transform: translateY(-6px); opacity: 1; }
        }
      `}</style>

      {showAdmin && <AdminModal onClose={() => setShowAdmin(false)} />}
    </div>
  );
}

// ─── Entry point ──────────────────────────────────────────────────────────────
export function KioskPage() {
  const [unlocked, setUnlocked] = useState<boolean | null>(null);

  useEffect(() => {
    setUnlocked(isKioskUnlocked());
  }, []);

  if (unlocked === null) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#002395]">
        <div className="w-8 h-8 border-4 border-white/30 border-t-white
          rounded-full animate-spin" />
      </div>
    );
  }

  if (!unlocked) return <PinSetupScreen onUnlocked={() => setUnlocked(true)} />;
  return <KioskDisplay />;
}
