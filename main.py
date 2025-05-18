import my_funcs
from flask import Flask, request, send_file
from zipfile import ZipFile
import time
import os
import threading
import io

app = Flask(__name__)

@app.route('/file/create', methods=['POST'])
def upload_file():
    if 'metronome_speed' not in request.form:
        return 'No metronome_speed part', 400
    metronome_speed = int(request.form['metronome_speed'])
    if 'file' not in request.files:
        return 'No file part', 400
    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400
    file = request.files['file']
    unique_id = str(int(time.time() * 10))
    output_directory = "D:/!KPI/KP/extra/" + unique_id
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    pdf_file_path = output_directory + "/" + unique_id + ".pdf"
    file.save(pdf_file_path)
    thread = threading.Thread(target=my_funcs.convert_pdf_to_musicxml, args=(unique_id,metronome_speed))
    thread.start()
    return unique_id, 200

@app.route('/file/update/<unique_id>', methods=['PUT'])
def update_file(unique_id):
    if 'metronome_speed' not in request.form:
        return 'No metronome_speed part', 400
    metronome_speed = int(request.form['metronome_speed'])
    unique_id = str(unique_id)
    my_funcs.create_midi_mp34(unique_id,metronome_speed)
    return unique_id, 200

@app.route('/file/<unique_id>', methods=['GET'])
def get_file(unique_id):
    unique_id=str(unique_id)
    output_directory = "D:/!KPI/KP/extra/" + unique_id
    mp3_file_path = output_directory + "/" + unique_id + ".mp3"
    mp4_file_path = output_directory + "/" + unique_id + ".mp4"
    if not os.path.exists(mp4_file_path):
        return 'No file yet', 404
    file_paths = [mp3_file_path,mp4_file_path]
    memory_file = io.BytesIO()
    with ZipFile(memory_file, 'w') as zipf:
        # Writing each file to the zip
        for file in file_paths:
            zipf.write(file, os.path.basename(file))
    memory_file.seek(0)
    return send_file(memory_file, mimetype='zip', download_name="files.zip", as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)