import os
from google.cloud import storage, texttospeech
from flask import Flask, request, jsonify

app = Flask(__name__)
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
        try:
            tts_client = texttospeech.TextToSpeechClient()
        except Exception as e:
            return jsonify({"error": f"Failed to initialize Text-to-Speech client: {str(e)}"}), 500

        # Configure TTS request
        try:
            synthesis_input = texttospeech.SynthesisInput(text=text)
            voice_params = texttospeech.VoiceSelectionParams(
                language_code=language_code, name=voice_name
            )
            audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

            # Generate audio
            response = tts_client.synthesize_speech(
                input=synthesis_input, voice=voice_params, audio_config=audio_config
            )
        except Exception as e:
            return jsonify({"error": f"Failed to synthesize speech: {str(e)}"}), 500

        # Save audio to Google Cloud Storage
        try:
            storage_client = storage.Client()
            bucket = storage_client.bucket("tts-audio-storage-first")
            blob = bucket.blob("output.mp3")
            blob.upload_from_string(response.audio_content)
        except Exception as e:
            return jsonify({"error": f"Failed to upload audio to Google Cloud Storage: {str(e)}"}), 500

        # Return the URL of the audio file
        return jsonify({"audio_url": blob.public_url})
    
    except Exception as e:
        # Catch any unexpected errors
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
