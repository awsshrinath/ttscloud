from flask import Flask, request, jsonify
import subprocess
import os
import tempfile
import uuid
from google.cloud import storage
from google.auth import default

app = Flask(__name__)
credentials, project = default()
# Initialize Google Cloud Storage client
storage_client = storage.Client()
BUCKET_NAME = 'vdocomp'

def download_file_from_gcs(gcs_uri, destination):
    """Helper function to download a file from GCS to a local destination."""
    bucket_name, blob_name = gcs_uri.replace("gs://", "").split("/", 1)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.download_to_filename(destination)

def upload_to_gcs(local_file_path, filename):
    """Uploads a file to Google Cloud Storage and returns the public URL."""
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(filename)
    blob.upload_from_filename(local_file_path)
    blob.make_public()
    return blob.public_url

def get_audio_duration(audio_path):
    """Get the duration of an audio file in seconds."""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    return float(result.stdout.strip())

@app.route('/process_video', methods=['POST'])
def process_video():
    data = request.get_json()
    
    # Extract input from JSON
    image_uris = data.get('images', [])
    audio_uri = data.get('audio')
    srt_uri = data.get('srt')
    resolution = data.get('resolution', '1920x1080')  # Default resolution if not specified

    # Split the resolution into width and height
    width, height = resolution.split('x')

    # Generate a unique identifier for this request
    unique_id = str(uuid.uuid4())

    # Temporary directory for processing
    with tempfile.TemporaryDirectory() as tmpdir:
        # Download images from GCS
        image_files = []
        for i, image_uri in enumerate(image_uris):
            image_path = os.path.join(tmpdir, f'image_{i}_{unique_id}.jpg')
            download_file_from_gcs(image_uri, image_path)
            image_files.append(image_path)
        
        # Download audio from GCS
        audio_path = os.path.join(tmpdir, f'audio_{unique_id}.mp3')
        download_file_from_gcs(audio_uri, audio_path)
        
        # Download SRT file from GCS
        srt_path = os.path.join(tmpdir, f'subtitles_{unique_id}.srt')
        download_file_from_gcs(srt_uri, srt_path)
        
        # Calculate duration per image based on audio length
        audio_duration = get_audio_duration(audio_path)
        image_duration = audio_duration / len(image_files)

        # Create a file list with calculated duration per image
        file_list_path = os.path.join(tmpdir, f'images_{unique_id}.txt')
        with open(file_list_path, 'w') as f:
            for image in image_files:
                f.write(f"file '{image}'\n")
                f.write(f"duration {image_duration}\n")

        # Use FFmpeg to create a slideshow from the file list, applying the specified resolution
        slideshow_path = os.path.join(tmpdir, f'slideshow_{unique_id}.mp4')
        subprocess.run([
            'ffmpeg', '-f', 'concat', '-safe', '0', '-i', file_list_path,
            '-vf', f'scale={width}:{height}', '-vsync', 'vfr', '-pix_fmt', 'yuv420p', slideshow_path
        ], check=True)

        # Combine video with audio and subtitles
        output_path = os.path.join(tmpdir, f'output_{unique_id}.mp4')
        subprocess.run([
            'ffmpeg', '-i', slideshow_path, '-i', audio_path, '-vf', f'subtitles={srt_path}',
            '-c:v', 'copy', '-c:a', 'aac', '-shortest', output_path
        ], check=True)

        # Upload final video to Google Cloud Storage
        output_filename = f'processed_video_{unique_id}.mp4'
        public_url = upload_to_gcs(output_path, output_filename)

        # Gather metadata
        metadata = {
            "url": public_url,
            "duration": audio_duration,
            "resolution": resolution
        }

        return jsonify(metadata)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)