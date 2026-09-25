from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
from scipy.spatial import distance as dist


class FaceDetector:
    LEFT_EYE = [33, 160, 158, 133, 153, 144]
    RIGHT_EYE = [362, 385, 387, 263, 373, 380]

    LEFT_IRIS = [468, 469, 470, 471]
    RIGHT_IRIS = [473, 474, 475, 476]

    NOSE_TIP = 1
    CHIN = 152
    LEFT_EYE_CORNER = 33
    RIGHT_EYE_CORNER = 263
    LEFT_MOUTH = 61
    RIGHT_MOUTH = 291

    def __init__(self):
        model_path = (
            Path(__file__).resolve().parents[3]
            / "models"
            / "face_landmarker.task"
        )

        if not model_path.exists():
            raise FileNotFoundError(
                f"Face Landmarker model not found: {model_path}"
            )

        base_options = mp.tasks.BaseOptions(
            model_asset_path=str(model_path),
            delegate=mp.tasks.BaseOptions.Delegate.CPU,
        )

        options = mp.tasks.vision.FaceLandmarkerOptions(
            base_options=base_options,
            running_mode=mp.tasks.vision.RunningMode.VIDEO,
            num_faces=1,
            min_face_detection_confidence=0.5,
            min_face_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )

        self.landmarker = (
            mp.tasks.vision.FaceLandmarker
            .create_from_options(options)
        )

        self.timestamp_ms = 0

        # =========================================================
        # BLINK DETECTION
        # Adapted directly from the supplied reference algorithm.
        # =========================================================

        # Reference:
        # blink_thresh = 0.45
        self.blink_threshold = 0.45

        # Reference:
        # succ_frame = 2
        self.blink_success_frames = 2

        # Reference:
        # count_frame = 0
        self.blink_closed_frames = 0

        # Prevent counting the same closure repeatedly.
        self.blink_in_progress = False

        # Total number of detected blinks.
        self.blink_count = 0

        # =========================================================
        # GAZE CALIBRATION
        # =========================================================

        self.gaze_calibration_samples = []
        self.gaze_calibration_frames = 30
        self.vertical_gaze_baseline = None

    # =============================================================
    # DISTANCE
    # =============================================================

    @staticmethod
    def distance(point_a, point_b):
        return float(
            dist.euclidean(
                point_a,
                point_b,
            )
        )

    # =============================================================
    # EAR
    #
    # This intentionally follows the user's reference implementation:
    #
    # y1 = distance(eye[1], eye[5])
    # y2 = distance(eye[2], eye[4])
    # x1 = distance(eye[0], eye[3])
    #
    # EAR = (y1 + y2) / x1
    #
    # We do NOT divide by 2 here.
    # =============================================================

    @staticmethod
    def eye_aspect_ratio(eye):
        y1 = dist.euclidean(
            eye[1],
            eye[5],
        )

        y2 = dist.euclidean(
            eye[2],
            eye[4],
        )

        x1 = dist.euclidean(
            eye[0],
            eye[3],
        )

        if x1 == 0:
            return 0.0

        return (y1 + y2) / x1

    # =============================================================
    # GET EYE LANDMARKS
    # =============================================================

    def get_eye_points(self, landmarks, indexes):
        return [
            (
                landmarks[index].x,
                landmarks[index].y,
            )
            for index in indexes
        ]

    # =============================================================
    # CALCULATE EAR
    # =============================================================

    def calculate_ear(self, landmarks):
        left_eye = self.get_eye_points(
            landmarks,
            self.LEFT_EYE,
        )

        right_eye = self.get_eye_points(
            landmarks,
            self.RIGHT_EYE,
        )

        left_ear = self.eye_aspect_ratio(
            left_eye
        )

        right_ear = self.eye_aspect_ratio(
            right_eye
        )

        return left_ear, right_ear

    # =============================================================
    # BLINK DETECTION
    #
    # This follows the supplied reference logic:
    #
    # avg = (left_EAR + right_EAR) / 2
    #
    # if avg < blink_thresh:
    #     count_frame += 1
    #
    # else:
    #     if count_frame >= succ_frame:
    #         Blink Detected
    #     else:
    #         count_frame = 0
    #
    # The only addition is blink_in_progress so that one prolonged
    # eye closure produces one blink rather than repeated blinks.
    # =============================================================

    def detect_blink(
        self,
        left_ear,
        right_ear,
    ):
        # Exact reference logic:
        avg = (
            left_ear + right_ear
        ) / 2.0

        blink_detected = False

        # Reference:
        #
        # if avg < blink_thresh:
        #     count_frame += 1

        if avg < self.blink_threshold:
            self.blink_closed_frames += 1
            self.blink_in_progress = True

        else:
            # Reference:
            #
            # if count_frame >= succ_frame:
            #     Blink Detected
            #
            # else:
            #     count_frame = 0

            if (
                self.blink_in_progress
                and self.blink_closed_frames
                >= self.blink_success_frames
            ):
                self.blink_count += 1
                blink_detected = True

            self.blink_closed_frames = 0
            self.blink_in_progress = False

        return blink_detected

    # =============================================================
    # GAZE
    # =============================================================

    def calculate_gaze(self, landmarks):
        left_iris = np.mean(
            [
                [
                    landmarks[index].x,
                    landmarks[index].y,
                ]
                for index in self.LEFT_IRIS
            ],
            axis=0,
        )

        right_iris = np.mean(
            [
                [
                    landmarks[index].x,
                    landmarks[index].y,
                ]
                for index in self.RIGHT_IRIS
            ],
            axis=0,
        )

        left_outer = np.array(
            [
                landmarks[33].x,
                landmarks[33].y,
            ]
        )

        left_inner = np.array(
            [
                landmarks[133].x,
                landmarks[133].y,
            ]
        )

        right_inner = np.array(
            [
                landmarks[362].x,
                landmarks[362].y,
            ]
        )

        right_outer = np.array(
            [
                landmarks[263].x,
                landmarks[263].y,
            ]
        )

        left_eye_width = np.linalg.norm(
            left_inner - left_outer
        )

        right_eye_width = np.linalg.norm(
            right_outer - right_inner
        )

        if (
            left_eye_width <= 0
            or right_eye_width <= 0
        ):
            return {
                "horizontal": 0.0,
                "vertical": 0.0,
                "direction": "unknown",
            }

        left_horizontal = (
            left_iris[0] - left_outer[0]
        ) / left_eye_width

        right_horizontal = (
            right_iris[0] - right_inner[0]
        ) / right_eye_width

        horizontal_position = (
            left_horizontal
            + right_horizontal
        ) / 2.0

        left_top = np.mean(
            [
                landmarks[159].y,
                landmarks[160].y,
            ]
        )

        left_bottom = np.mean(
            [
                landmarks[144].y,
                landmarks[145].y,
            ]
        )

        right_top = np.mean(
            [
                landmarks[386].y,
                landmarks[387].y,
            ]
        )

        right_bottom = np.mean(
            [
                landmarks[373].y,
                landmarks[374].y,
            ]
        )

        left_eye_height = (
            left_bottom - left_top
        )

        right_eye_height = (
            right_bottom - right_top
        )

        if (
            left_eye_height <= 0
            or right_eye_height <= 0
        ):
            vertical_position = 0.5
        else:
            left_vertical = (
                left_iris[1] - left_top
            ) / left_eye_height

            right_vertical = (
                right_iris[1] - right_top
            ) / right_eye_height

            vertical_position = (
                left_vertical
                + right_vertical
            ) / 2.0

        horizontal = (
            horizontal_position - 0.5
        )

        raw_vertical = (
            vertical_position - 0.5
        )

        if self.vertical_gaze_baseline is None:
            self.gaze_calibration_samples.append(
                raw_vertical
            )

            if (
                len(self.gaze_calibration_samples)
                >= self.gaze_calibration_frames
            ):
                self.vertical_gaze_baseline = float(
                    np.median(
                        self.gaze_calibration_samples
                    )
                )

        if self.vertical_gaze_baseline is None:
            calibrated_vertical = 0.0
        else:
            calibrated_vertical = (
                raw_vertical
                - self.vertical_gaze_baseline
            )

        horizontal = float(
            np.clip(
                horizontal,
                -0.5,
                0.5,
            )
        )

        calibrated_vertical = float(
            np.clip(
                calibrated_vertical,
                -0.5,
                0.5,
            )
        )

        if horizontal < -0.08:
            horizontal_direction = "left"
        elif horizontal > 0.08:
            horizontal_direction = "right"
        else:
            horizontal_direction = "center"

        if calibrated_vertical < -0.12:
            vertical_direction = "up"
        elif calibrated_vertical > 0.12:
            vertical_direction = "down"
        else:
            vertical_direction = "center"

        return {
            "horizontal": horizontal,
            "vertical": calibrated_vertical,
            "direction": (
                f"{horizontal_direction}-"
                f"{vertical_direction}"
            ),
        }

    # =============================================================
    # HEAD POSE
    # =============================================================

    def calculate_head_pose(
        self,
        landmarks,
        frame_width,
        frame_height,
    ):
        image_points = np.array(
            [
                [
                    landmarks[self.NOSE_TIP].x
                    * frame_width,
                    landmarks[self.NOSE_TIP].y
                    * frame_height,
                ],
                [
                    landmarks[self.CHIN].x
                    * frame_width,
                    landmarks[self.CHIN].y
                    * frame_height,
                ],
                [
                    landmarks[self.LEFT_EYE_CORNER].x
                    * frame_width,
                    landmarks[self.LEFT_EYE_CORNER].y
                    * frame_height,
                ],
                [
                    landmarks[self.RIGHT_EYE_CORNER].x
                    * frame_width,
                    landmarks[self.RIGHT_EYE_CORNER].y
                    * frame_height,
                ],
                [
                    landmarks[self.LEFT_MOUTH].x
                    * frame_width,
                    landmarks[self.LEFT_MOUTH].y
                    * frame_height,
                ],
                [
                    landmarks[self.RIGHT_MOUTH].x
                    * frame_width,
                    landmarks[self.RIGHT_MOUTH].y
                    * frame_height,
                ],
            ],
            dtype=np.float64,
        )

        model_points = np.array(
            [
                [0.0, 0.0, 0.0],
                [0.0, -63.6, -12.5],
                [-43.3, 32.7, -26.0],
                [43.3, 32.7, -26.0],
                [-28.9, -28.9, -24.1],
                [28.9, -28.9, -24.1],
            ],
            dtype=np.float64,
        )

        focal_length = frame_width

        camera_matrix = np.array(
            [
                [
                    focal_length,
                    0,
                    frame_width / 2,
                ],
                [
                    0,
                    focal_length,
                    frame_height / 2,
                ],
                [0, 0, 1],
            ],
            dtype=np.float64,
        )

        distortion_coefficients = np.zeros(
            (4, 1),
            dtype=np.float64,
        )

        success, rotation_vector, _ = cv2.solvePnP(
            model_points,
            image_points,
            camera_matrix,
            distortion_coefficients,
            flags=cv2.SOLVEPNP_ITERATIVE,
        )

        if not success:
            return {
                "yaw": 0.0,
                "pitch": 0.0,
                "roll": 0.0,
            }

        rotation_matrix, _ = cv2.Rodrigues(
            rotation_vector
        )

        angles, _, _, _, _, _ = cv2.RQDecomp3x3(
            rotation_matrix
        )

        yaw = float(angles[1])
        pitch = float(angles[0])
        roll = float(angles[2])

        yaw = float(
            np.clip(
                yaw,
                -90.0,
                90.0,
            )
        )

        pitch = float(
            np.clip(
                pitch,
                -90.0,
                90.0,
            )
        )

        roll = float(
            np.clip(
                roll,
                -90.0,
                90.0,
            )
        )

        return {
            "yaw": yaw,
            "pitch": pitch,
            "roll": roll,
        }

    # =============================================================
    # MAIN FRAME PROCESSING
    # =============================================================

    def process(self, frame):
        rgb_frame = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB,
        )

        image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb_frame,
        )

        self.timestamp_ms += 200

        result = self.landmarker.detect_for_video(
            image,
            self.timestamp_ms,
        )

        if not result.face_landmarks:
            self.blink_closed_frames = 0
            self.blink_in_progress = False

            return {
                "face_detected": False,
                "landmark_count": 0,
                "left_ear": 0.0,
                "right_ear": 0.0,
                "blink_detected": False,
                "blink_count": self.blink_count,
                "gaze": {
                    "horizontal": 0.0,
                    "vertical": 0.0,
                    "direction": "unknown",
                },
                "head_pose": {
                    "yaw": 0.0,
                    "pitch": 0.0,
                    "roll": 0.0,
                },
            }

        landmarks = result.face_landmarks[0]

        # ---------------------------------------------------------
        # EAR
        # ---------------------------------------------------------

        left_ear, right_ear = self.calculate_ear(
            landmarks
        )

        # ---------------------------------------------------------
        # BLINK
        # ---------------------------------------------------------

        blink_detected = self.detect_blink(
            left_ear,
            right_ear,
        )

        # ---------------------------------------------------------
        # GAZE
        # ---------------------------------------------------------

        gaze = self.calculate_gaze(
            landmarks
        )

        # ---------------------------------------------------------
        # HEAD POSE
        # ---------------------------------------------------------

        head_pose = self.calculate_head_pose(
            landmarks,
            frame.shape[1],
            frame.shape[0],
        )

        return {
            "face_detected": True,
            "landmark_count": len(landmarks),
            "left_ear": round(
                left_ear,
                4,
            ),
            "right_ear": round(
                right_ear,
                4,
            ),
            "blink_detected": blink_detected,
            "blink_count": self.blink_count,
            "gaze": gaze,
            "head_pose": head_pose,
        }

    # =============================================================
    # CLEANUP
    # =============================================================

    def close(self):
        self.landmarker.close()
