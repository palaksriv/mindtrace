import { FaceLandmarker, FilesetResolver } from '@mediapipe/tasks-vision'
import { useEffect, useRef, useState } from 'react'
import { api, authHeaders } from '../services/api'

type Props = { sessionId?: number; onStatusChange?: (active: boolean) => void }
type Point = { x: number; y: number }

// Pinned versions: the WASM runtime matches the npm package in package-lock.json and the
// model uses Google's versioned path, so results are reproducible between runs.
const modelUrl = 'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task'
const wasmUrl = 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@1.0.1/wasm'
const SAMPLE_INTERVAL_MS = 500 // 2 Hz telemetry cadence (documented in the paper)
const distance = (a: Point, b: Point) => Math.hypot(a.x - b.x, a.y - b.y)

export function WebcamCapture({ sessionId, onStatusChange }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const detectorRef = useRef<FaceLandmarker | null>(null)
  const timerRef = useRef<number | null>(null)
  const sessionIdRef = useRef<number | undefined>(sessionId)
  const blinkCountRef = useRef(0)
  const closedRef = useRef(false)
  const [status, setStatus] = useState<'idle' | 'starting' | 'active' | 'error'>('idle')
  const [message, setMessage] = useState('Camera is off.')
  const [faceDetected, setFaceDetected] = useState(false)

  useEffect(() => { sessionIdRef.current = sessionId }, [sessionId])

  async function startCamera() {
    setStatus('starting'); setMessage('Requesting camera permission…')
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } }, audio: false })
      streamRef.current = stream
      const video = videoRef.current
      if (!video) throw new Error('Camera preview is unavailable.')
      video.srcObject = stream; await video.play()
      const vision = await FilesetResolver.forVisionTasks(wasmUrl)
      detectorRef.current = await FaceLandmarker.createFromOptions(vision, {
        baseOptions: { modelAssetPath: modelUrl, delegate: 'CPU' }, runningMode: 'VIDEO', numFaces: 1,
      })
      setStatus('active'); setMessage('Camera analysis is active in this browser.'); onStatusChange?.(true)
      timerRef.current = window.setInterval(() => { void analyse() }, SAMPLE_INTERVAL_MS)
    } catch (error) {
      console.error(error); setStatus('error'); setMessage('Unable to start browser-based camera analysis.'); onStatusChange?.(false)
    }
  }

  async function analyse() {
    const video = videoRef.current; const detector = detectorRef.current
    if (!video || !detector || video.readyState < 2) return
    const landmarks = detector.detectForVideo(video, performance.now()).faceLandmarks[0] as Point[] | undefined
    if (!landmarks) {
      setFaceDetected(false); setMessage('No face detected.')
      if (sessionIdRef.current) await send({ face_detected: false, landmark_count: 0, left_ear: 0, right_ear: 0, blink_detected: false, blink_count: blinkCountRef.current, gaze: { horizontal: 0, vertical: 0, direction: 'unknown' }, head_pose: { yaw: 0, pitch: 0, roll: 0 } })
      return
    }
    const ear = (ids: number[]) => (distance(landmarks[ids[1]], landmarks[ids[5]]) + distance(landmarks[ids[2]], landmarks[ids[4]])) / distance(landmarks[ids[0]], landmarks[ids[3]])
    const left = ear([33, 160, 158, 133, 153, 144]); const right = ear([362, 385, 387, 263, 373, 380])
    const isClosed = (left + right) / 2 < 0.45
    const blink = !closedRef.current && isClosed
    if (blink) blinkCountRef.current += 1
    closedRef.current = isClosed
    const eyeLeft = landmarks[33], eyeRight = landmarks[263], nose = landmarks[1], chin = landmarks[152]
    const horizontal = Math.max(-0.5, Math.min(0.5, (nose.x - (eyeLeft.x + eyeRight.x) / 2) / distance(eyeLeft, eyeRight)))
    const vertical = Math.max(-0.5, Math.min(0.5, (nose.y - (eyeLeft.y + eyeRight.y) / 2) / distance({ x: (eyeLeft.x + eyeRight.x) / 2, y: (eyeLeft.y + eyeRight.y) / 2 }, chin)))
    const h = horizontal < -0.08 ? 'left' : horizontal > 0.08 ? 'right' : 'center'
    const v = vertical < -0.12 ? 'up' : vertical > 0.12 ? 'down' : 'center'
    const roll = Math.atan2(eyeRight.y - eyeLeft.y, eyeRight.x - eyeLeft.x) * 180 / Math.PI
    const payload = { face_detected: true, landmark_count: landmarks.length, left_ear: left, right_ear: right, blink_detected: blink, blink_count: blinkCountRef.current, gaze: { horizontal, vertical, direction: `${h}-${v}` }, head_pose: { yaw: horizontal * 90, pitch: vertical * 90, roll } }
    setFaceDetected(true); setMessage(`Face detected · ${landmarks.length} landmarks`)
    if (sessionIdRef.current) await send(payload)
  }

  async function send(payload: object) { try { await api.post('/cv/telemetry', { session_id: sessionIdRef.current, ...payload }, { headers: authHeaders() }) } catch { /* telemetry must not interrupt assessment */ } }
  function stop() { if (timerRef.current) window.clearInterval(timerRef.current); timerRef.current = null; detectorRef.current?.close(); detectorRef.current = null; streamRef.current?.getTracks().forEach(t => t.stop()); streamRef.current = null; setStatus('idle'); setFaceDetected(false); setMessage('Camera is off.'); onStatusChange?.(false) }
  useEffect(() => () => stop(), [])
  return <div className="space-y-3 rounded-lg border border-slate-200 bg-white p-4"><div className="aspect-video overflow-hidden rounded-md bg-slate-900"><video ref={videoRef} muted playsInline className="h-full w-full object-cover" /></div><div className="flex items-center justify-between gap-4"><div><p className="font-semibold">Webcam</p><p className="text-sm text-slate-500">{message}</p>{status === 'active' && <p className="mt-1 text-xs text-slate-500">Face: {faceDetected ? 'Detected' : 'Not detected'} · Analysis stays in this browser.</p>}</div>{status === 'idle' && <button type="button" onClick={() => void startCamera()} className="rounded-md bg-indigo-700 px-4 py-2 font-semibold text-white">Enable camera</button>}{status === 'starting' && <span className="text-sm text-slate-500">Starting…</span>}{status === 'active' && <button type="button" onClick={stop} className="rounded-md border border-slate-300 px-4 py-2 font-semibold">Stop camera</button>}</div></div>
}
