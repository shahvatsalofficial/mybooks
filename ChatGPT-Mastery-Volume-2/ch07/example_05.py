"""
Production Video Temporal Ingestion & Analysis Engine
Samples video frames at 1 FPS and reasons over temporal action sequences.
Author: Vatsal Shah, Enterprise AI Architect
"""
import cv2
import base64
import os
from typing import List
from openai import OpenAI

client = OpenAI()

def extract_uniform_frames(video_path: str, fps_sample_rate: float = 1.0) -> List[str]:
    """Extracts base64 JPEG frames from video at a uniform temporal interval."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video file {video_path}")

    video_fps = cap.get(cv2.CAP_PROP_FPS)
    frame_interval = int(video_fps / fps_sample_rate)
    base64_frames = []

    frame_count = 0
    while True:
        success, frame = cap.read()
        if not success:
            break

        if frame_count % frame_interval == 0:
            # Resize frame to standard 720p to conserve bandwidth
            resized = cv2.resize(frame, (1280, 720))
            _, buffer = cv2.imencode(".jpg", resized, [cv2.IMWRITE_JPEG_QUALITY, 80])
            b64_str = base64.b64encode(buffer).decode("utf-8")
            base64_frames.append(b64_str)

        frame_count += 1

    cap.release()
    print(f"🎬 Processed {frame_count} raw video frames -> Extracted {len(base64_frames)} sampled frames.")
    return base64_frames

def analyze_surveillance_video(video_path: str) -> str:
    # Extract 1 frame per second
    frames = extract_uniform_frames(video_path, fps_sample_rate=1.0)

    # Construct multi-image message array
    content_payload = [
        {"type": "text", "text": "Analyze this factory security video. Identify any safety protocol violations or equipment anomalies with timestamps."}
    ]

    for idx, b64_frame in enumerate(frames):
        content_payload.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{b64_frame}",
                "detail": "low" # Use low detail for high-volume video frames to minimize cost
            }
        })

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": content_payload}],
        temperature=0.2
    )

    return response.choices[0].message.content
