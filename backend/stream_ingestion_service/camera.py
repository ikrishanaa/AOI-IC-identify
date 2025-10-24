"""
Camera stream management with OpenCV.
Supports IP cameras (RTSP/HTTP), USB cameras, and video files.
"""
import cv2
import threading
import time
import logging
from queue import Queue, Empty
from typing import Optional
import numpy as np

logger = logging.getLogger(__name__)


class CameraStream:
    """Thread-safe camera stream with auto-reconnect."""
    
    def __init__(self, source: str, max_queue_size: int = 5):
        """
        Initialize camera stream.
        
        Args:
            source: Camera source URL or device ID
                - RTSP: rtsp://192.168.1.100:8080/h264
                - HTTP MJPEG: http://192.168.1.100:8080/video
                - USB camera: 0, 1, 2...
                - Video file: /path/to/video.mp4
            max_queue_size: Maximum frames to buffer (prevents memory issues)
        """
        self.source = source
        self.max_queue_size = max_queue_size
        self.frame_queue: Queue = Queue(maxsize=max_queue_size)
        self.cap: Optional[cv2.VideoCapture] = None
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.last_frame_time = 0
        self.frame_count = 0
        self.error_count = 0
        self.max_errors = 10  # Stop after 10 consecutive errors
        
    def start(self) -> bool:
        """
        Start camera capture in background thread.
        
        Returns:
            True if started successfully, False otherwise
        """
        if self.running:
            logger.warning("Camera already running")
            return True
            
        try:
            # Try to open camera
            self.cap = cv2.VideoCapture(self.source)
            
            # Configure for network streams
            if isinstance(self.source, str) and self.source.startswith(('rtsp://', 'http://')):
                # Minimize buffering for low latency
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                # Set timeout (5 seconds)
                self.cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
                
            # Check if camera opened successfully
            if not self.cap.isOpened():
                logger.error(f"Failed to open camera: {self.source}")
                return False
                
            # Get one frame to verify it works
            ret, frame = self.cap.read()
            if not ret or frame is None:
                logger.error(f"Failed to read from camera: {self.source}")
                self.cap.release()
                return False
                
            logger.info(f"Camera opened successfully: {self.source}")
            logger.info(f"Frame size: {frame.shape[1]}x{frame.shape[0]}")
            
            # Start capture thread
            self.running = True
            self.error_count = 0
            self.thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"Error starting camera: {e}")
            if self.cap:
                self.cap.release()
            return False
    
    def _capture_loop(self):
        """Background thread that continuously captures frames."""
        logger.info("Camera capture loop started")
        
        while self.running:
            try:
                ret, frame = self.cap.read()
                
                if not ret or frame is None:
                    self.error_count += 1
                    logger.warning(f"Failed to read frame (error {self.error_count}/{self.max_errors})")
                    
                    if self.error_count >= self.max_errors:
                        logger.error("Too many errors, stopping camera")
                        self.running = False
                        break
                    
                    # Try to reconnect
                    time.sleep(1)
                    self._reconnect()
                    continue
                
                # Reset error count on successful read
                self.error_count = 0
                self.frame_count += 1
                self.last_frame_time = time.time()
                
                # Add to queue (discard oldest if full)
                if self.frame_queue.full():
                    try:
                        self.frame_queue.get_nowait()  # Remove oldest frame
                    except Empty:
                        pass
                
                self.frame_queue.put(frame)
                
            except Exception as e:
                logger.error(f"Error in capture loop: {e}")
                time.sleep(1)
        
        logger.info("Camera capture loop stopped")
    
    def _reconnect(self):
        """Attempt to reconnect to camera."""
        try:
            if self.cap:
                self.cap.release()
            
            logger.info(f"Attempting to reconnect to {self.source}")
            self.cap = cv2.VideoCapture(self.source)
            
            if isinstance(self.source, str) and self.source.startswith(('rtsp://', 'http://')):
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                self.cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
            
            if self.cap.isOpened():
                logger.info("Reconnection successful")
            else:
                logger.warning("Reconnection failed")
                
        except Exception as e:
            logger.error(f"Reconnection error: {e}")
    
    def get_frame(self, timeout: float = 0.5) -> Optional[np.ndarray]:
        """
        Get the latest frame from the queue.
        
        Args:
            timeout: Maximum time to wait for a frame (seconds)
            
        Returns:
            Frame as numpy array, or None if no frame available
        """
        try:
            return self.frame_queue.get(timeout=timeout)
        except Empty:
            return None
    
    def stop(self):
        """Stop camera capture and cleanup."""
        logger.info("Stopping camera stream")
        self.running = False
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        
        if self.cap:
            self.cap.release()
            self.cap = None
        
        # Clear queue
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except Empty:
                break
        
        logger.info("Camera stream stopped")
    
    def is_running(self) -> bool:
        """Check if camera is running."""
        return self.running and self.thread and self.thread.is_alive()
    
    def get_stats(self) -> dict:
        """Get camera statistics."""
        return {
            "running": self.is_running(),
            "source": self.source,
            "frame_count": self.frame_count,
            "queue_size": self.frame_queue.qsize(),
            "max_queue_size": self.max_queue_size,
            "error_count": self.error_count,
            "last_frame_time": self.last_frame_time,
        }
