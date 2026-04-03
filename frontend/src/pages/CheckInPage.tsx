import { useState, useRef, useCallback, useEffect } from 'react';
import Webcam from 'react-webcam';
import { Html5QrcodeScanner, Html5QrcodeSupportedFormats, Html5QrcodeScanType } from 'html5-qrcode';
import { attendanceApi } from '../api/attendance';
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
type Step = 'scan' | 'camera' | 'confirm' | 'success' | 'error';

function dataURLtoBlob(dataUrl: string): Blob {
  const [header, data] = dataUrl.split(',');
  const mime = header.match(/:(.*?);/)![1];
  const binary = atob(data);
  const arr = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) arr[i] = binary.charCodeAt(i);
  return new Blob([arr], { type: mime });
}

export function CheckInPage() {
  const { user } = useAuthStore();
  const [mode, setMode] = useState<Mode>('check-in');
  const [step, setStep] = useState<Step>('scan');
  const [qrData, setQrData] = useState('');
  const [photo, setPhoto] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ time: string; message: string } | null>(null);
  const [errorMsg, setErrorMsg] = useState('');

  const webcamRef = useRef<Webcam>(null);
  const scannerRef = useRef<Html5QrcodeScanner | null>(null);
  const scannerInitialized = useRef(false);
  const geo = useGeolocation();

  // Init QR scanner when on scan step
  useEffect(() => {
    if (step !== 'scan') return;
    if (scannerInitialized.current) return;
    scannerInitialized.current = true;

    const scanner = new Html5QrcodeScanner(
      'qr-reader',
      {
        fps: 10,
        qrbox: { width: 250, height: 250 },
        rememberLastUsedCamera: true,
        formatsToSupport: [Html5QrcodeSupportedFormats.QR_CODE],
        supportedScanTypes: [Html5QrcodeScanType.SCAN_TYPE_CAMERA],
        aspectRatio: 1,
      },
      false
    );

    scanner.render(
      (text) => {
        // Successfully scanned the kiosk's encrypted daily token
        setQrData(text);
        scanner.clear().catch(() => {});
        scannerInitialized.current = false;
        setStep('camera');
        toast.success('QR code scanned!');
      },
      () => {} // ignore scan errors — user just needs to reposition
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
    if (!qrData || !photo) return;
    setLoading(true);
    try {
      const photoBlob = dataURLtoBlob(photo);
      const payload = {
        qr_code_data: qrData,          // encrypted kiosk token
        latitude: geo.latitude ?? -29.3167,
        longitude: geo.longitude ?? 27.4833,
        device_id: generateDeviceId(),
        photo: photoBlob,
      };

      // JWT is attached automatically by axios interceptor
      // Backend validates: kiosk token + JWT + geofence + photo
      const rec = mode === 'check-in'
        ? await attendanceApi.checkIn(payload)
        : await attendanceApi.checkOut(payload);

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
    setStep('scan');
    setQrData('');
    setPhoto(null);
    setResult(null);
    setErrorMsg('');
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

      {/* Mode toggle — only show on scan/camera step */}
      {(step === 'scan' || step === 'camera') && (
        <div className="card p-1 flex mb-6 gap-1">
          {(['check-in', 'check-out'] as Mode[]).map((m) => (
            <button
              key={m}
              onClick={() => { setMode(m); reset(); }}
              className={`flex-1 py-2.5 px-4 rounded-xl text-sm font-medium
                transition-all duration-200 capitalize ${
                mode === m
                  ? 'bg-[#002395] text-white shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {m}
            </button>
          ))}
        </div>
      )}

      {/* GPS status bar */}
      {step !== 'success' && (
        <div className={`flex items-center gap-2 text-xs px-4 py-2.5 rounded-xl
          mb-5 font-medium ${
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
            <button
              onClick={geo.refresh}
              className="underline font-semibold shrink-0"
            >
              Retry
            </button>
          )}
        </div>
      )}

      {/* ── Step: QR Scan ── */}
      {step === 'scan' && (
        <div className="card p-6 animate-fade-in">
          <h2 className="text-lg font-bold text-gray-900 font-display mb-1">
            Scan Kiosk QR Code
          </h2>
          <p className="text-sm text-gray-400 mb-5">
            Point your camera at the QR code displayed on the kiosk screen
          </p>
          <div id="qr-reader" className="w-full rounded-xl overflow-hidden" />
          <p className="text-xs text-center text-gray-400 mt-4">
            Ensure good lighting · Hold steady for best results
          </p>
        </div>
      )}

      {/* ── Step: Camera / Selfie ── */}
      {step === 'camera' && (
        <div className="card p-6 animate-fade-in">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <p className="text-sm font-medium text-emerald-700">
              Kiosk QR scanned — now take your selfie
            </p>
          </div>
          <h2 className="text-lg font-bold text-gray-900 font-display mb-4">
            Take a Selfie
          </h2>
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
            onClick={reset}
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
          <p className="text-sm text-gray-400 mb-5">
            Review your details before submitting
          </p>

          <img
            src={photo}
            alt="Your photo"
            className="w-full aspect-square object-cover rounded-2xl mb-5"
          />

          <div className="space-y-2 mb-6">
            {[
              {
                label: 'Employee',
                value: `${user?.first_name} ${user?.last_name}`,
              },
              {
                label: 'Action',
                value: mode === 'check-in' ? '🟢 Check In' : '🔴 Check Out',
              },
              {
                label: 'GPS',
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
              <div
                key={label}
                className="flex justify-between text-sm py-2 border-b border-gray-50"
              >
                <span className="text-gray-500">{label}</span>
                <span className="font-medium text-gray-800">{value}</span>
              </div>
            ))}
          </div>

          <button
            onClick={handleSubmit}
            disabled={loading}
            className={`${
              mode === 'check-in' ? 'btn-success' : 'btn-danger'
            } w-full flex items-center justify-center gap-2`}
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
            <div className="absolute w-20 h-20 rounded-full border-2
              border-emerald-400 animate-pulse-ring" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 font-display mb-2">
            {mode === 'check-in' ? 'Checked In!' : 'Checked Out!'}
          </h2>
          <p className="text-3xl font-bold text-[#002395] font-display mb-3">
            {result.time}
          </p>
          <p className="text-sm text-gray-500 mb-8">{result.message}</p>
          <button onClick={reset} className="btn-outline w-full">
            Done
          </button>
        </div>
      )}

      {/* ── Step: Error ── */}
      {step === 'error' && (
        <div className="card p-8 text-center animate-fade-in">
          <div className="w-20 h-20 rounded-full bg-red-50 flex items-center
            justify-center mx-auto mb-5">
            <svg className="w-10 h-10 text-red-500" fill="none"
              stroke="currentColor" viewBox="0 0 24 24">
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
          <button onClick={reset} className="btn-primary w-full">
            Try Again
          </button>
        </div>
      )}
    </div>
  );
}
