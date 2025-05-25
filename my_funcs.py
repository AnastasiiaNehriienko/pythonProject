import io
import subprocess
import os
import tempfile
from music21 import converter, stream, tempo
import partitura as pt
from moviepy.editor import AudioFileClip, ImageClip, concatenate_videoclips
from pydub import AudioSegment
from PIL import Image

# Paths to external tools and resources
soundfont = 'C:/ProgramData/soundfonts/ad.sf3'
audiveris_path = 'C:/Program Files/Audiveris/bin/Audiveris.bat'
musescore_path = 'C:/Program Files/MuseScore 4/bin/MuseScore4.exe'

# Number of measures per row
ROW_SIZE = 3
# FPS for video
FPS = 2


def convert_pdf_to_musicxml(unique_id, metronome_speed):
    output_directory = os.path.join("D:/!KPI/KP/extra", unique_id)
    base = os.path.join(output_directory, unique_id)
    pdf = base + ".pdf"
    mxl = base + ".mxl"

    os.makedirs(output_directory, exist_ok=True)
    subprocess.run([audiveris_path, '-batch', pdf, '-output', output_directory, '-export'], shell=True, check=True)
    subprocess.run([musescore_path, mxl, '-o', mxl], check=True)
    create_midi_mp34(unique_id, metronome_speed)


def create_midi_mp34(unique_id, metronome_speed):
    base = os.path.join("D:/!KPI/KP/extra", unique_id, unique_id)
    mxl = base + ".mxl"
    mid = base + ".mid"
    wav = base + ".wav"
    mp3 = base + ".mp3"

    score = converter.parse(mxl)
    score.insert(0, tempo.MetronomeMark(number=metronome_speed))
    score.write('midi', fp=mid)

    os.system(f'fluidsynth -ni {soundfont} {mid} -F {wav} -r 44100')
    AudioSegment.from_wav(wav).export(mp3, format='mp3')
    create_timed_mp4(unique_id, metronome_speed)


def split_score_to_measure_xmls(mxl_file, metronome_speed):
    full = converter.parse(mxl_file)
    parts = full.parts
    secs_per_beat = 60.0 / metronome_speed

    xml_paths = []
    durations = []
    measures = parts[0].getElementsByClass(stream.Measure)
    total = len(measures)

    # Split into chunks of ROW_SIZE
    for start in range(1, total+1, ROW_SIZE):
        end = min(start + ROW_SIZE - 1, total)
        tmp = tempfile.NamedTemporaryFile(suffix='.xml', delete=False)
        tmp.close()

        sc = stream.Score()
        sc.insert(0, tempo.MetronomeMark(number=metronome_speed))
        group_dur = 0
        for p in parts:
            part_copy = stream.Part()
            for idx in range(start, end+1):
                meas = p.measure(idx)
                if meas:
                    part_copy.append(meas)
                    if p == parts[0]:
                        group_dur += meas.barDuration.quarterLength * secs_per_beat
            sc.append(part_copy)

        sc.write('musicxml', fp=tmp.name)
        xml_paths.append(tmp.name)
        durations.append(group_dur)

    return xml_paths, durations


def render_and_merge_rows(xml_paths):
    """
    For every two consecutive xmls, render separate PNGs and merge vertically.
    Returns list of merged PNG paths.
    """
    png_pages = []
    # Render individual row images
    row_images = []
    for xml in xml_paths:
        score = pt.load_musicxml(xml)
        png = xml.replace('.xml', '.png')
        pt.render(score, out_fn=png)
        row_images.append(png)

    # Merge each pair of rows
    for i in range(0, len(row_images), 2):
        top = row_images[i]
        bottom = row_images[i+1] if i+1 < len(row_images) else None
        img_top = Image.open(top)
        if bottom:
            img_bottom = Image.open(bottom)
            width = max(img_top.width, img_bottom.width)
            height = img_top.height + img_bottom.height
            merged = Image.new('RGB', (width, height), color=(255,255,255))
            merged.paste(img_top, (0,0))
            merged.paste(img_bottom, (0, img_top.height))
        else:
            merged = img_top
        merged_path = top.replace('_row', '_page')
        merged.save(merged_path)
        png_pages.append(merged_path)
    return png_pages


def create_timed_mp4(unique_id, metronome_speed):
    base = os.path.join("D:/!KPI/KP/extra", unique_id, unique_id)
    mxl = base + ".mxl"
    mp3 = base + ".mp3"
    mp4 = base + ".mp4"

    xmls, durs = split_score_to_measure_xmls(mxl, metronome_speed)
    # Merge rows into pages
    pages = render_and_merge_rows(xmls)

    # Calculate page durations (sum of two rows)
    page_durs = []
    for i in range(0, len(durs), 2):
        total_d = durs[i] + (durs[i+1] if i+1 < len(durs) else 0)
        page_durs.append(total_d)

    # Video dimensions from first page
    w, h = Image.open(pages[0]).size
    w += w % 2; h += h % 2

    audio = AudioFileClip(mp3)
    clips = [ImageClip(p).set_duration(d).resize((w,h)).set_position('center')
             for p,d in zip(pages, page_durs)]

    video = concatenate_videoclips(clips, method='compose').set_audio(audio)
    video.write_videofile(mp4, fps=FPS, codec='libx264', audio_codec='aac')
