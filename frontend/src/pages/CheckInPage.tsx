import { useState, useRef, useCallback, useEffect } from 'react';
import Webcam from 'react-webcam';
import {
  Html5QrcodeScanner,
  Html5QrcodeSupportedFormats,
  Html5QrcodeScanType,
} from 'html5-qrcode';
import { attendanceApi } from '../api/attendance';
import { kioskApi, type QueueSession } from '../api/kiosk';
import {
  useGeolocation,
  generateDeviceId,
  toast,
  extractApiError,
  formatTime,
} from '../utils/helpers';
import { Spinner } from '../components/common/Loading';
import { useAuthStore } from '../store/authStore';

type Mode = 'check-in' | 'check-out';
type Step = 'idle' | 'queued' | 'your-turn' | 'scan' | 'camera' | 'confirm' | 'success' | 'error';

function dataURLtoBlob(dataUrl: string): Blob {
  const [header, data] = dataUrl.split(',');
  const mime = header.match(/:(.*?);/)![1];
  const binary = atob(data);
  const arr = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) arr[i] = binary.charCodeAt(i);
  return new Blob([arr], { type: mime });
}

function useSessionCountdown(expiresAt: string | null): number {
  const [seconds, setSeconds] = useState(300);
  useEffect(() => {
    if (!expiresAt) return;
    const tick = () => {
      const diff = Math.max(0, Math.floor(
        (new Date(expiresAt).getTime() - Date.now()) / 1000
      ));
      setSeconds(diff);
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [expiresAt]);
  return seconds;
}

// ─── Queue Waiting Screen ─────────────────────────────────────────────────────
function QueueWaitingScreen({
  session,
  onYourTurn,
  onCancel,
}: {
  session: QueueSession;
  onYourTurn: (qrData: string) => void;
  onCancel: () => void;
}) {
  const [current, setCurrent] = useState(session);
  const countdown = useSessionCountdown(current.expires_at);

  useEffect(() => {
    const id = setInterval(async () => {
      try {
        const status = await kioskApi.getSessionStatus(session.session_id);
        setCurrent(status);
        if (status.your_turn && status.qr_data) {
          clearInterval(id);
          onYourTurn(status.qr_data);
        }
        if (status.status === 'EXPIRED' || status.status === 'CANCELLED') {
          clearInterval(id);
          toast.error('Your session expired. Please try again.');
          onCancel();
        }
      } catch {
        // keep polling silently
      }
    }, 2000);
    return () => clearInterval(id);
  }, [session.session_id, onYourTurn, onCancel]);

  const ahead = current.queue_position - 1;
  const waitMin = Math.ceil(current.estimated_wait_seconds / 60);

  return (
    <div className="card p-8 text-center animate-slide-up">
      {/* Position circle */}
      <div className="relative inline-flex items-center justify-center mb-6">
        <div
          className="w-28 h-28 rounded-full flex items-center justify-center"
          style={{ background: '#002395' }}
        >
          <div>
            <p className="text-xs text-blue-200 font-medium uppercase tracking-wide">
              Position
            </p>
            <p className="text-5xl font-bold text-white font-display leading-none">
              {current.queue_position}
            </p>
          </div>
        </div>
        <div
          className="absolute w-28 h-28 rounded-full border-2 border-[#002395]"
          style={{ animation: 'pulseRing 1.5s ease-out infinite', opacity: 0.4 }}
        />
      </div>

      <h2 className="text-xl font-bold text-gray-900 font-display mb-2">
        {ahead === 0 ? "You're next!" : "You're in the queue"}
      </h2>
      <p className="text-gray-400 text-sm mb-6">
        {ahead === 0
          ? 'Almost your turn — stay by the kiosk'
          : `${ahead} ${ahead === 1 ? 'person' : 'people'} ahead of you`}
      </p>

      {/* Wait estimate */}
      {ahead > 0 && (
        <div className="bg-blue-50 border border-blue-100 rounded-xl px-4 py-3 mb-5">
          <p className="text-sm text-[#002395] font-medium">
            Estimated wait: ~{waitMin} {waitMin === 1 ? 'minute' : 'minutes'}
          </p>
        </div>
      )}

      {/* Queue dots */}
      <div className="flex items-center justify-center gap-2 mb-6">
        {Array.from({ length: Math.min(current.queue_position + 2, 7) }).map((_, i) => (
          <div
            key={i}
            className={`rounded-full transition-all duration-500 ${
              i < current.queue_position
                ? 'w-3 h-3 bg-[#002395]'
                : 'w-2 h-2 bg-gray-200'
            } ${i === current.queue_position - 1 ? 'scale-125' : ''}`}
          />
        ))}
      </div>

      {/* Session countdown */}
      <div className="flex items-center justify-center gap-1.5 text-xs text-gray-400 mb-8">
        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span>
          Session expires in{' '}
          <span className={`font-bold tabular-nums ${
            countdown < 60 ? 'text-red-500' : 'text-gray-700'
          }`}>
            {Math.floor(countdown / 60)}:{String(countdown % 60).padStart(2, '0')}
          </span>
        </span>
      </div>

      <button onClick={onCancel} className="btn-outline w-full text-sm py-2.5">
        Cancel &amp; Leave Queue
      </button>
    </div>
  );
}

// ─── Your Turn Screen ─────────────────────────────────────────────────────────
function YourTurnScreen({
  onStartScan,
  expiresAt,
}: {
  onStartScan: () => void;
  expiresAt: string;
}) {
  const countdown = useSessionCountdown(expiresAt);

  return (
    <div className="card p-8 text-center animate-bounce-in">
      <div className="w-24 h-24 rounded-full bg-emerald-500/10 flex items-center
        justify-center mx-auto mb-5 relative">
        <svg className="w-12 h-12 text-emerald-500" fill="none"
          stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M5 13l4 4L19 7" />
        </svg>
        <div
          className="absolute inset-0 rounded-full border-2 border-emerald-400"
          style={{ animation: 'pulseRing 1.5s ease-out infinite' }}
        />
      </div>

      <h2 className="text-2xl font-bold text-gray-900 font-display mb-2">
        It's Your Turn!
      </h2>
      <p className="text-gray-400 text-sm mb-6">
        Walk to the kiosk and scan the QR code displayed on screen
      </p>

      {countdown < 120 && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 mb-5">
          <p className="text-sm text-amber-700 font-medium">
            ⚠️ Hurry! Session expires in {countdown}s
          </p>
        </div>
      )}

      <div className="flex items-center justify-center gap-1.5 text-xs text-gray-400 mb-8">
        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span>
          Time remaining:{' '}
          <span className={`font-bold tabular-nums ${
            countdown < 60 ? 'text-red-500' : 'text-gray-700'
          }`}>
            {Math.floor(countdown / 60)}:{String(countdown % 60).padStart(2, '0')}
          </span>
        </span>
      </div>

      <button
        onClick={onStartScan}
        className="btn-success w-full flex items-center justify-center gap-2 text-base py-4"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4" />
        </svg>
        Scan Kiosk QR Now
      </button>
    </div>
  );
}

// ─── Main Check-In Page ───────────────────────────────────────────────────────
export function CheckInPage() {
  const { user } = useAuthStore();
  const [mode, setMode] = useState<Mode>('check-in');
  const [step, setStep] = useState<Step>('idle');
  const [session, setSession] = useState<QueueSession | null>(null);
  const [sessionQrData, setSessionQrData] = useState('');
  const [photo, setPhoto] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [joiningQueue, setJoiningQueue] = useState(false);
  const [result, setResult] = useState<{ time: string; message: string } | null>(null);
  const [errorMsg, setErrorMsg] = useState('');

  const webcamRef = useRef<Webcam>(null);
  const scannerRef = useRef<Html5QrcodeScanner | null>(null);
  const scannerInitialized = useRef(false);
  const submitted = useRef(false);
  const geo = useGeolocation();

  // Cancel session on unmount if not submitted
  useEffect(() => {
    return () => {
      if (session && !submitted.current) {
        kioskApi.cancelSession(session.session_id).catch(() => {});
      }
    };
  }, [session]);

  // Join queue
  const handleJoinQueue = async (selectedMode: Mode) => {
    setMode(selectedMode);
    setJoiningQueue(true);
    try {
      const sessionType = selectedMode === 'check-in' ? 'checkin' : 'checkout';
      const sess = await kioskApi.joinQueue({
        session_type: sessionType,
        latitude: geo.latitude ?? undefined,
        longitude: geo.longitude ?? undefined,
      });
      setSession(sess);
      if (sess.your_turn && sess.qr_data) {
        setSessionQrData(sess.qr_data);
        setStep('your-turn');
      } else {
        setStep('queued');
      }
    } catch (err) {
      toast.error(extractApiError(err));
    } finally {
      setJoiningQueue(false);
    }
  };

  const handleYourTurn = (qrData: string) => {
    setSessionQrData(qrData);
    setStep('your-turn');
    toast.success("It's your turn! Walk to the kiosk.");
  };

  const handleCancel = async () => {
    if (session) {
      kioskApi.cancelSession(session.session_id).catch(() => {});
    }
    setSession(null);
    setStep('idle');
  };

  // Init QR scanner
  useEffect(() => {
    if (step !== 'scan') return;
    if (scannerInitialized.current) return;
    scannerInitialized.current = true;

    const scanner = new Html5QrcodeScanner(
      'qr-reader',
      {
        fps: 10,
        qrbox: { width: 260, height: 260 },
        rememberLastUsedCamera: true,
        formatsToSupport: [Html5QrcodeSupportedFormats.QR_CODE],
        supportedScanTypes: [Html5QrcodeScanType.SCAN_TYPE_CAMERA],
        aspectRatio: 1,
      },
      false
    );

    scanner.render(
      (text) => {
        scanner.clear().catch(() => {});
        scannerInitialized.current = false;
        setSessionQrData(text);
        setStep('camera');
        toast.success('QR scanned!');
      },
      () => {}
    );

    scannerRef.current = scanner;
    return () => {
      scanner.clear().catch(() => {});
      scannerInitialized.current = false;
    };
  }, [step]);

  const capturePhoto = useCallback(() => {
    const imageSrc = webcamRef.current?.getScreenshot();
    if (imageSrc) {
      setPhoto(imageSrc);
      setStep('confirm');
    }
  }, []);

  const handleSubmit = async () => {
    if (!sessionQrData || !photo) return;
    setLoading(true);
    try {
      const photoBlob = dataURLtoBlob(photo);
      const payload = {
        qr_code_data: sessionQrData,
        latitude: geo.latitude ?? -29.3167,
        longitude: geo.longitude ?? 27.4833,
        device_id: generateDeviceId(),
        photo: photoBlob,
      };

      const rec = mode === 'check-in'
        ? await attendanceApi.checkIn(payload)
        : await attendanceApi.checkOut(payload);

      submitted.current = true;
      setResult({
        time: formatTime(
          mode === 'check-in'
            ? rec.check_in_time
            : rec.check_out_time ?? rec.check_in_time
        ),
        message: mode === 'check-in'
          ? 'Check-in successful! Confirmation sent to your phone & email.'
          : 'Check-out recorded! Summary sent to your phone & email.',
      });
      setStep('success');
    } catch (err) {
      setErrorMsg(extractApiError(err));
      setStep('error');
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    submitted.current = false;
    setSession(null);
    setSessionQrData('');
    setPhoto(null);
    setResult(null);
    setErrorMsg('');
    setStep('idle');
  };

  return (
    <div className="max-w-md mx-auto">
      {/* Header */}
      <div className="page-header">
        <h1 className="page-title">Attendance</h1>
        <p className="page-subtitle">
          {user?.first_name} {user?.last_name} · {user?.employee_number}
        </p>
      </div>

      {/* GPS status */}
      {step !== 'success' && step !== 'error' && (
        <div className={`flex items-center gap-2 text-xs px-4 py-2.5 rounded-xl mb-5
          font-medium ${
          geo.loading
            ? 'bg-amber-50 text-amber-700 border border-amber-200'
            : geo.error
            ? 'bg-orange-50 text-orange-700 border border-orange-200'
            : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
        }`}>
          <svg className="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor"
            viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8
              8 0 1111.314 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          <span className="flex-1">
            {geo.loading
              ? 'Getting your location…'
              : geo.error
              ? 'Using approximate location'
              : `Location acquired · ±${Math.round(geo.accuracy ?? 0)}m accuracy`}
          </span>
          {geo.error && (
            <button onClick={geo.refresh} className="underline font-semibold shrink-0">
              Retry
            </button>
          )}
        </div>
      )}

      {/* ── Step: Idle — choose mode ── */}
      {step === 'idle' && (
        <div className="card p-8 text-center animate-fade-in">
          <div className="w-16 h-16 rounded-2xl bg-[#002395]/10 flex items-center
            justify-center mx-auto mb-5">
            <svg className="w-8 h-8 text-[#002395]" fill="none" stroke="currentColor"
              viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
                d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4
                12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1
                1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1
                0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0
                001 1z" />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-gray-900 font-display mb-2">
            Ready to record attendance?
          </h2>
          <p className="text-sm text-gray-400 mb-8">
            Tap a button to join the queue. When it's your turn, scan the QR code
            on the kiosk screen.
          </p>

          <div className="space-y-3">
            <button
              onClick={() => handleJoinQueue('check-in')}
              disabled={joiningQueue}
              className="btn-success w-full flex items-center justify-center gap-2 py-4 text-base"
            >
              {joiningQueue && mode === 'check-in'
                ? <><Spinner size="sm" color="white" /> Joining queue…</>
                : <>
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                        d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0
                        01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
                    </svg>
                    Check In
                  </>
              }
            </button>

            <button
              onClick={() => handleJoinQueue('check-out')}
              disabled={joiningQueue}
              className="btn-outline w-full flex items-center justify-center gap-2 py-4 text-base"
            >
              {joiningQueue && mode === 'check-out'
                ? <><Spinner size="sm" color="#002395" /> Joining queue…</>
                : <>
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                        d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0
                        01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                    </svg>
                    Check Out
                  </>
              }
            </button>
          </div>
        </div>
      )}

      {/* ── Step: Queued — waiting ── */}
      {step === 'queued' && session && (
        <QueueWaitingScreen
          session={session}
          onYourTurn={handleYourTurn}
          onCancel={handleCancel}
        />
      )}

      {/* ── Step: Your Turn ── */}
      {step === 'your-turn' && session && (
        <YourTurnScreen
          onStartScan={() => setStep('scan')}
          expiresAt={session.expires_at}
        />
      )}

      {/* ── Step: QR Scan ── */}
      {step === 'scan' && (
        <div className="card p-6 animate-fade-in">
          <h2 className="text-lg font-bold text-gray-900 font-display mb-1">
            Scan Kiosk QR Code
          </h2>
          <p className="text-sm text-gray-400 mb-5">
            Point your camera at the QR code on the kiosk screen
          </p>
          <div id="qr-reader" className="w-full rounded-xl overflow-hidden" />
          <p className="text-xs text-center text-gray-400 mt-4">
            Camera only · Hold steady · Good lighting helps
          </p>
          <button
            onClick={() => setStep('your-turn')}
            className="w-full text-sm text-gray-400 hover:text-gray-600 mt-3 py-2"
          >
            ← Back
          </button>
        </div>
      )}

      {/* ── Step: Camera / Selfie ── */}
      {step === 'camera' && (
        <div className="card p-6 animate-fade-in">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <p className="text-sm font-medium text-emerald-700">
              QR verified — now take your selfie
            </p>
          </div>
          <h2 className="text-lg font-bold text-gray-900 font-display mb-1">
            Take a Selfie
          </h2>
          <p className="text-xs text-gray-400 mb-4">
            Please look directly at the camera
          </p>
          <div className="rounded-2xl overflow-hidden mb-5 bg-black">
            <Webcam
              ref={webcamRef}
              screenshotFormat="image/jpeg"
              videoConstraints={{ facingMode: 'user', width: 400, height: 400 }}
              className="w-full aspect-square object-cover"
            />
          </div>
          <button onClick={capturePhoto} className="btn-primary w-full">
            📸 Capture Photo
          </button>
          <button
            onClick={() => setStep('scan')}
            className="w-full text-sm text-gray-400 hover:text-gray-600 mt-3 py-2"
          >
            ← Scan again
          </button>
        </div>
      )}

      {/* ── Step: Confirm ── */}
      {step === 'confirm' && photo && (
        <div className="card p-6 animate-slide-up">
          <h2 className="text-lg font-bold text-gray-900 font-display mb-1">
            Confirm {mode}
          </h2>
          <p className="text-sm text-gray-400 mb-5">Review before submitting</p>

          <img
            src={photo}
            alt="Your selfie"
            className="w-full aspect-square object-cover rounded-2xl mb-5"
          />

          <div className="space-y-2 mb-6">
            {[
              { label: 'Employee', value: `${user?.first_name} ${user?.last_name}` },
              { label: 'Action', value: mode === 'check-in' ? '🟢 Check In' : '🔴 Check Out' },
              {
                label: 'Location',
                value: geo.latitude
                  ? `${geo.latitude.toFixed(4)}, ${geo.longitude?.toFixed(4)}`
                  : 'Default location',
              },
              {
                label: 'Time',
                value: new Date().toLocaleTimeString('en-LS', {
                  hour: '2-digit', minute: '2-digit',
                }),
              },
            ].map(({ label, value }) => (
              <div key={label}
                className="flex justify-between text-sm py-2 border-b border-gray-50">
                <span className="text-gray-500">{label}</span>
                <span className="font-medium text-gray-800">{value}</span>
              </div>
            ))}
          </div>

          <button
            onClick={handleSubmit}
            disabled={loading}
            className={`${mode === 'check-in' ? 'btn-success' : 'btn-danger'} w-full
              flex items-center justify-center gap-2`}
          >
            {loading
              ? <><Spinner size="sm" color="white" /> Processing…</>
              : `Confirm ${mode}`}
          </button>
          <button
            onClick={() => setStep('camera')}
            className="w-full text-sm text-gray-400 hover:text-gray-600 mt-3 py-2"
          >
            ← Retake photo
          </button>
        </div>
      )}

      {/* ── Step: Success ── */}
      {step === 'success' && result && (
        <div className="card p-8 text-center animate-bounce-in">
          <div className="relative inline-flex items-center justify-center mb-6">
            <div className="w-20 h-20 rounded-full bg-emerald-500/10
              flex items-center justify-center">
              <svg className="w-10 h-10 text-emerald-500" fill="none"
                stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <div
              className="absolute w-20 h-20 rounded-full border-2 border-emerald-400"
              style={{ animation: 'pulseRing 1.5s ease-out infinite' }}
            />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 font-display mb-2">
            {mode === 'check-in' ? 'Checked In!' : 'Checked Out!'}
          </h2>
          <p className="text-3xl font-bold text-[#002395] font-display mb-3">
            {result.time}
          </p>
          <p className="text-sm text-gray-500 mb-8">{result.message}</p>
          <button onClick={reset} className="btn-outline w-full">Done</button>
        </div>
      )}

      {/* ── Step: Error ── */}
      {step === 'error' && (
        <div className="card p-8 text-center animate-fade-in">
          <div className="w-20 h-20 rounded-full bg-red-50 flex items-center
            justify-center mx-auto mb-5">
            <svg className="w-10 h-10 text-red-500" fill="none" stroke="currentColor"
              viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-gray-900 font-display mb-2">
            Unable to {mode}
          </h2>
          <p className="text-sm bg-red-50 text-red-700 rounded-xl p-3 mb-8">
            {errorMsg}
          </p>
          <button onClick={reset} className="btn-primary w-full">Try Again</button>
        </div>
      )}
    </div>
  );
}
