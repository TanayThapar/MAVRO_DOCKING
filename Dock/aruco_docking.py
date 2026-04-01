import cv2
import cv2.aruco as aruco
import numpy as np
import math
import time

# ==========================================================
# USER CONFIGURATION
# ==========================================================

CAMERA_INDEX = 0          # USB camera index
MARKER_ID = 10            # ArUco ID on the wall (DICT_4X4_50)
MARKER_SIZE = 0.15        # meters (side length)

DESIRED_DISTANCE = 0.30   # meters from wall

# Speeds
LINEAR_SPEED = 0.20       # m/s
ANGULAR_SPEED = 0.50      # rad/s
SEARCH_ANGULAR_SPEED = 0.3

ANGLE_TOL = 3.0           # degrees
DIST_TOL = 0.05           # meters

# -------------------------
# CAMERA CALIBRATION (OBSBOT MEET SE - 1080p ESTIMATED)
# -------------------------

camera_matrix = np.array([
    [1320.0,    0.0, 960.0],
    [   0.0, 1320.0, 540.0],
    [   0.0,    0.0,   1.0]
], dtype=np.float32)

dist_coeffs = np.zeros((5, 1))

# ==========================================================
# ARUCO SETUP
# ==========================================================

aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
aruco_params = aruco.DetectorParameters()
detector = aruco.ArucoDetector(aruco_dict, aruco_params)

# ==========================================================
# ROBOT COMMAND INTERFACE
# ==========================================================
def send_cmd(linear, angular):
    # Link this to your robot's motor controller / ROS publisher
    print(f"[CMD] linear={linear:.2f}  angular={angular:.2f}")

# ==========================================================
# MAIN
# ==========================================================

def main():
    cap = cv2.VideoCapture(CAMERA_INDEX)
    
    # FORCE 1080P RESOLUTION TO MATCH CALIBRATION
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    
    if not cap.isOpened():
        print("❌ Camera not found")
        return

    print("📷 OBSBOT Meet SE Started at 1080p")
    print("🔍 Searching for ArUco marker...")

    last_seen_time = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        corners, ids, _ = detector.detectMarkers(gray)

        if ids is not None and MARKER_ID in ids:
            last_seen_time = time.time()

            idx = np.where(ids == MARKER_ID)[0][0]
            marker_corners = corners[idx]

            # Estimate Pose
            rvecs, tvecs, _ = aruco.estimatePoseSingleMarkers(
                marker_corners,
                MARKER_SIZE,
                camera_matrix,
                dist_coeffs
            )

            tvec = tvecs[0][0]
            x, y, z = tvec

            distance = z
            # Angle in degrees for the controller
            angle = math.degrees(math.atan2(x, z))

            # Visualization
            aruco.drawDetectedMarkers(frame, corners)
            cv2.drawFrameAxes(frame, camera_matrix, dist_coeffs,
                              rvecs[0], tvecs[0], 0.1)

            cv2.putText(frame,
                        f"Dist: {distance:.2f} m  Angle: {angle:.2f} deg",
                        (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 0),
                        2)

            # --- DOCKING CONTROLLER ---
            if abs(angle) > ANGLE_TOL:
                # 1. ALIGN: Rotate until marker is centered (angle < 3 deg)
                angular = -ANGULAR_SPEED if angle > 0 else ANGULAR_SPEED
                send_cmd(0.0, angular)

            elif abs(distance - DESIRED_DISTANCE) > DIST_TOL:
                # 2. APPROACH: Drive forward once aligned
                linear = LINEAR_SPEED if distance > DESIRED_DISTANCE else -LINEAR_SPEED
                send_cmd(linear, 0.0)

            else:
                # 3. DOCKED: Distance reached
                send_cmd(0.0, 0.0)
                print("✅ Docking successful")
                break

        else:
            # SEARCH MODE: Rotate until marker enters FOV
            send_cmd(0.0, SEARCH_ANGULAR_SPEED)

            if time.time() - last_seen_time > 10.0:
                print("⚠️ Marker lost, continuing search...")
                last_seen_time = time.time()

        cv2.imshow("ArUco Docking", frame)
        if cv2.waitKey(1) & 0xFF == 27: # ESC to exit
            break

    send_cmd(0.0, 0.0)
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()