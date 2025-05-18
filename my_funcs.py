import io
import subprocess
import os
from music21 import converter, environment, midi, tempo
import partitura as pt
import moviepy
from moviepy.editor import ImageClip, AudioFileClip, VideoClip
from pydub import AudioSegment
from PIL import Image
import threading

soundfont = 'C:/ProgramData/soundfonts/ad.sf3'
audiveris_path ='C:/Program Files/Audiveris/bin/Audiveris.bat'
musescore_path= 'C:/Program Files/MuseScore 4/bin/MuseScore4.exe'

def convert_pdf_to_musicxml(unique_id, metronome_speed):
    output_directory = "D:/!KPI/KP/extra/" + unique_id
    any_file = output_directory + "/" + unique_id
    pdf_file_path = any_file + ".pdf"
    mxl_file_path = any_file + ".mxl"
    midi_file_path = any_file + ".mid"
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    command = [audiveris_path, '-batch', pdf_file_path, '-output', output_directory, '-export']
    command2 = [musescore_path, mxl_file_path, '-o', mxl_file_path]
    try:
        subprocess.run(command, shell=True, check=True)
        subprocess.run(command2, check=True)
        print("Conversion completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")
    create_midi_mp34(unique_id, metronome_speed)

def create_midi_mp34(unique_id, metronome_speed):
    output_directory = "D:/!KPI/KP/extra/" + unique_id
    any_file = output_directory + "/" + unique_id
    mxl_file_path = any_file + ".mxl"
    png_file_path = any_file+".png"
    mp3_file_path = any_file+".mp3"
    mp4_file_path = any_file+".mp4"
    midi_file_path = any_file+".mid"
    create_midi(mxl_file_path, metronome_speed, midi_file_path)
    midi_to_mp3(midi_file_path, soundfont, mp3_file_path)
    create_png(mxl_file_path,png_file_path)
    create_mp4(png_file_path,mp3_file_path,mp4_file_path)

def create_midi(mxl_file_path, metronome_speed, midi_file_path):
    score = converter.parse(mxl_file_path)
    metronome_mark = tempo.MetronomeMark(number=metronome_speed)
    score.insert(0, metronome_mark)
    score.write('midi', fp=midi_file_path)

def midi_to_mp3(midi_file, soundfont, mp3_file):
    wav_file = mp3_file.replace('.mp3', '.wav')
    os.system(f'fluidsynth -ni {soundfont} {midi_file} -F {wav_file} -r 44100')
    audio = AudioSegment.from_wav(wav_file)
    audio.export(mp3_file, format='mp3')
    os.remove(wav_file)

def create_png(mxl_file_path,png_file_path):
    score = pt.load_musicxml(mxl_file_path)
    part = score.parts[0]
    pt.render(part, out_fn=png_file_path)

def create_mp4(png_file_path,mp3_file_path,mp4_file_path):
    audio_clip = AudioFileClip(mp3_file_path)
    image_clip = ImageClip(resize_image_for_video(png_file_path))
    video_clip = image_clip.set_audio(audio_clip)
    video_clip.duration = audio_clip.duration
    video_clip.fps = 2
    video_clip.write_videofile(mp4_file_path, codec='libx264',audio_codec='aac')

def resize_image_for_video(image_path):
    with Image.open(image_path) as img:
        width, height = img.size
        # Ensure the dimensions are even
        if width % 2 != 0:
            width += 1
        if height % 2 != 0:
            height += 1
        resized_img = img.resize((width, height), Image.Resampling.LANCZOS)
        resized_img_path = image_path.replace('.','_resized.')
        resized_img.save(resized_img_path)
        os.remove(image_path)
        return resized_img_path