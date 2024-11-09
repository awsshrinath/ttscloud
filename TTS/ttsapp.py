import os
from google.oauth2 import service_account
from google.cloud import storage, texttospeech
from flask import Flask, request, jsonify

app = Flask(__name__)
credentials = service_account.Credentials.from_service_account_file(r"C:\Users\MY PC\Documents\TTS\tts-service-pro1-cf81f6a8c62f.json")
# Specify your project ID
project_id = "tts-service-pro1"
@app.route("/generate-audio", methods=["POST"])
def generate_audio():
    try:
        # Parse JSON request data
        request_data = request.get_json()
        text = request_data.get("text", "")
        
        # Ensure that the 'text' field is present
        if not text:
            return jsonify({"error": "No text provided"}), 400
        
        language_code = "en-US"
        voice_name = "en-US-Wavenet-D"

        # Initialize TTS client
        tts_client = texttospeech.TextToSpeechClient(credentials=credentials)

        # Configure TTS request
        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice_params = texttospeech.VoiceSelectionParams(
            language_code=language_code, name=voice_name
        )
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

        # Generate audio
        response = tts_client.synthesize_speech(
            input=synthesis_input, voice=voice_params, audio_config=audio_config
        )

        # Save audio to Google Cloud Storage
        storage_client = storage.Client(credentials=credentials, project=project_id)
        bucket = storage_client.bucket("tts-audio-storage-first")
        blob = bucket.blob("output.mp3")
        blob.upload_from_string(response.audio_content)
        return jsonify({"audio_url": blob.public_url} ) 
    except Exception as e:
        # Return detailed error message for debugging
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)