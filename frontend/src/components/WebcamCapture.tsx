
import { useEffect, useRef, useState } from 'react'
import { api } from '../services/api'

type WebcamCaptureProps = {
  sessionId?: number
  onFrame?: (canvas: HTMLCanvasElement) => void
  onStatusChange?: (active: boolean) => void
}

export function WebcamCapture({
  sessionId,
  onFrame,
  onStatusChange,
}: WebcamCaptureProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const intervalRef = useRef<number | null>(null)
  const sessionIdRef = useRef<number | undefined>(sessionId)
  const analyzingRef = useRef(false)

  const [status, setStatus] = useState<
    'idle' | 'starting' | 'active' | 'denied' | 'error'
  >('idle')

  const [message, setMessage] = useState('')

  const [faceDetected, setFaceDetected] = useState(false)
  const [landmarkCount, setLandmarkCount] = useState(0)
  const [leftEar, setLeftEar] = useState(0)
  const [rightEar, setRightEar] = useState(0)
  const [blinkCount, setBlinkCount] = useState(0)
  const [gazeDirection, setGazeDirection] = useState('unknown')
  const [yaw, setYaw] = useState(0)
  const [pitch, setPitch] = useState(0)
  const [roll, setRoll] = useState(0)

  /*
   * Always keep the latest session ID.
   */
  useEffect(() => {
    const previousSessionId = sessionIdRef.current

    sessionIdRef.current = sessionId

    console.log(
      '[WEBCAM] sessionId:',
      previousSessionId,
      '->',
      sessionId,
    )

    /*
     * The camera may already be active when the assessment
     * session gets created.
     *
     * Start CV immediately when that happens.
     */
    if (
      sessionId &&
      status === 'active' &&
      previousSessionId !== sessionId
    ) {
      console.log(
        '[WEBCAM] Session received. Starting CV loop.',
      )

      startCvLoop()
    }
  }, [sessionId, status])

  /*
   * Start the camera when requested by the user.
   */
  async function startCamera() {
    console.log('[WEBCAM] startCamera()')

    setStatus('starting')
    setMessage('Requesting camera permission...')
    onStatusChange?.(false)

    try {
      const stream =
        await navigator.mediaDevices.getUserMedia({
          video: {
            facingMode: 'user',
            width: { ideal: 640 },
            height: { ideal: 480 },
          },
          audio: false,
        })

      console.log('[WEBCAM] Camera permission granted.')

      streamRef.current = stream

      const video = videoRef.current

      if (!video) {
        throw new Error(
          'Video element is unavailable.',
        )
      }

      video.srcObject = stream

      await video.play()

      console.log(
        '[WEBCAM] Video playing:',
        video.videoWidth,
        'x',
        video.videoHeight,
      )

      setStatus('active')
      onStatusChange?.(true)

      if (sessionIdRef.current) {
        setMessage(
          'Camera is active. Starting CV analysis...',
        )

        /*
         * Session already exists.
         */
        startCvLoop()
      } else {
        setMessage(
          'Camera active. Waiting for assessment session...',
        )
      }
    } catch (error) {
      console.error(
        '[WEBCAM] Unable to access webcam:',
        error,
      )

      onStatusChange?.(false)

      if (
        error instanceof DOMException &&
        error.name === 'NotAllowedError'
      ) {
        setStatus('denied')
        setMessage(
          'Camera permission was denied.',
        )
      } else {
        setStatus('error')
        setMessage(
          'Unable to access the camera.',
        )
      }
    }
  }

  /*
   * Start the CV loop.
   */
  function startCvLoop() {
    if (intervalRef.current !== null) {
      console.log(
        '[WEBCAM] CV loop already running.',
      )
      return
    }

    if (!sessionIdRef.current) {
      console.log(
        '[WEBCAM] Cannot start CV loop: no session ID.',
      )
      return
    }

    console.log(
      '[WEBCAM] Starting CV loop for session:',
      sessionIdRef.current,
    )

    /*
     * First frame immediately.
     */
    void captureFrame()

    /*
     * Then approximately 5 frames/second.
     */
    intervalRef.current = window.setInterval(() => {
      void captureFrame()
    }, 83)
  }

  /*
   * Capture and send one webcam frame.
   */
  async function captureFrame() {
    const video = videoRef.current
    const canvas = canvasRef.current
    const currentSessionId =
      sessionIdRef.current

    

    if (
      !video ||
      !canvas ||
      video.readyState < 2 ||
      video.videoWidth === 0 ||
      video.videoHeight === 0 ||
      analyzingRef.current
    ) {
      return
    }

    const context =
      canvas.getContext('2d')

    if (!context) {
      console.error(
        '[WEBCAM] Could not get canvas context.',
      )
      return
    }

    canvas.width = video.videoWidth
    canvas.height = video.videoHeight

    context.drawImage(
      video,
      0,
      0,
      canvas.width,
      canvas.height,
    )

    onFrame?.(canvas)

    analyzingRef.current = true

    try {
      const image = canvas.toDataURL(
        'image/jpeg',
        0.7,
      )

      const token = localStorage.getItem(
        'mindtrace_access_token',
      )

      if (!token) {
        throw new Error(
          'MindTrace access token is missing.',
        )
      }

      console.log(
        '[WEBCAM] POST /cv/analyze session:',
        currentSessionId,
      )

      const endpoint = currentSessionId
  ? '/cv/analyze'
  : '/cv/preview'

const payload = currentSessionId
  ? {
      image,
      session_id: currentSessionId,
    }
  : {
      image,
    }

const { data } = await api.post(
  endpoint,
  payload,
  {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  },
)

      console.log(
        '[WEBCAM] CV response:',
        data,
      )

      setFaceDetected(
        Boolean(data.face_detected),
      )

      setLandmarkCount(
        Number(data.landmark_count ?? 0),
      )

      setLeftEar(
        Number(data.left_ear ?? 0),
      )

      setRightEar(
        Number(data.right_ear ?? 0),
      )

      setBlinkCount(
        Number(data.blink_count ?? 0),
      )

      setGazeDirection(
        data.gaze?.direction ?? 'unknown',
      )

      setYaw(
        Number(data.head_pose?.yaw ?? 0),
      )

      setPitch(
        Number(data.head_pose?.pitch ?? 0),
      )

      setRoll(
        Number(data.head_pose?.roll ?? 0),
      )

      setMessage(
        data.face_detected
          ? 'Face detected.'
          : 'No face detected.',
      )
    } catch (error) {
      console.error(
        '[WEBCAM] CV frame analysis failed:',
        error,
      )
    } finally {
      analyzingRef.current = false
    }
  }

  function stopCamera() {
    console.log('[WEBCAM] stopCamera()')

    if (intervalRef.current !== null) {
      window.clearInterval(
        intervalRef.current,
      )

      intervalRef.current = null
    }

    if (streamRef.current) {
      streamRef.current
        .getTracks()
        .forEach((track) => track.stop())

      streamRef.current = null
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null
    }

    sessionIdRef.current = undefined

    setFaceDetected(false)
    setLandmarkCount(0)
    setLeftEar(0)
    setRightEar(0)
    setBlinkCount(0)
    setGazeDirection('unknown')
    setYaw(0)
    setPitch(0)
    setRoll(0)

    setStatus('idle')
    setMessage('')

    onStatusChange?.(false)
  }

  /*
   * Component cleanup.
   */
  useEffect(() => {
    return () => {
      if (intervalRef.current !== null) {
        window.clearInterval(
          intervalRef.current,
        )

        intervalRef.current = null
      }

      if (streamRef.current) {
        streamRef.current
          .getTracks()
          .forEach((track) => track.stop())

        streamRef.current = null
      }
    }
  }, [])

  return (
    <div className="space-y-3 rounded-lg border border-slate-200 bg-white p-4">
      <div className="aspect-video overflow-hidden rounded-md bg-slate-900">
        <video
          ref={videoRef}
          muted
          playsInline
          className="h-full w-full object-cover"
        />
      </div>

      <canvas
        ref={canvasRef}
        className="hidden"
      />

      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="font-semibold">
            Webcam
          </p>

          <p className="text-sm text-slate-500">
            {message}
          </p>

          {status === 'active' && (
            <div className="mt-2 space-y-1 text-xs text-slate-500">
              <p>
                Face:{' '}
                {faceDetected
                  ? 'Detected'
                  : 'Not detected'}
                {' · '}
                Landmarks: {landmarkCount}
              </p>

              {faceDetected && (
                <>
                  <p>
                    EAR: {leftEar.toFixed(3)} /{' '}
                    {rightEar.toFixed(3)}
                    {' · '}
                    Blinks: {blinkCount}
                  </p>

                  <p>
                    Gaze: {gazeDirection}
                  </p>

                  <p>
                    Head pose:{' '}
                    Yaw {yaw.toFixed(1)}°
                    {' · '}
                    Pitch {pitch.toFixed(1)}°
                    {' · '}
                    Roll {roll.toFixed(1)}°
                  </p>
                </>
              )}
            </div>
          )}
        </div>

        {status === 'idle' && (
          <button
            type="button"
            onClick={startCamera}
            className="rounded-md bg-indigo-700 px-4 py-2 font-semibold text-white"
          >
            Enable camera
          </button>
        )}

        {status === 'starting' && (
          <span className="text-sm text-slate-500">
            Starting camera...
          </span>
        )}

        {status === 'active' && (
          <button
            type="button"
            onClick={stopCamera}
            className="rounded-md border border-slate-300 px-4 py-2 font-semibold"
          >
            Stop camera
          </button>
        )}
      </div>
    </div>
  )
}

