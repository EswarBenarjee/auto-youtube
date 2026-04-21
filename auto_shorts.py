import os
import random
import time
import gc
import json
import requests
import numpy as np
from gtts import gTTS
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv
import textwrap

from youtube_uploader import upload_video  # 🔥 AUTO UPLOAD INTEGRATION

# ==============================
# ENV
# ==============================
load_dotenv(".env", override=True)
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

print("API KEY LOADED:", PEXELS_API_KEY[:10] if PEXELS_API_KEY else "None")

# ==============================
# FOLDERS
# ==============================
ASSETS = "assets"
AUDIO = f"{ASSETS}/audio"
CLIPS = f"{ASSETS}/clips"
TEMP = f"{ASSETS}/temp"
OUTPUT = "output"
LOG_FILE = "analytics.json"

for d in [AUDIO, CLIPS, TEMP, OUTPUT]:
    os.makedirs(d, exist_ok=True)

# ==============================
# IDEAS
# ==============================
ideas = [
    "avoid eye contact",
    "judge silently",
    "overthink everything",
    "fake confidence",
    "people please too much",
    "trust too fast",
    "emotional detachment",
    "why people lie",
    "fear rejection",
    "why people change"
]

# ==============================
# PEXELS QUERY MAP
# ==============================
def get_query(idea):
    return {
        "avoid eye contact": "shy person close up",
        "judge silently": "serious thinking face",
        "overthink everything": "stress thinking",
        "fake confidence": "fake smile nervous",
        "people please too much": "nervous smiling",
        "trust too fast": "handshake close",
        "emotional detachment": "emotionless face",
        "why people lie": "nervous talking",
        "fear rejection": "lonely sad person",
        "why people change": "sad transformation"
    }.get(idea, "person thinking moody")

# ==============================
# VIRAL SCRIPT ENGINE
# ==============================
def generate_script(topic):
    return (
        f"Stop scrolling — when someone {topic}, this means something deeper. "
        f"Most people misunderstand this completely. "
        f"Psychology says it reveals hidden emotion or insecurity. "
        f"And the scary part is — they never notice it themselves."
    )

# ==============================
# A/B HOOKS
# ==============================
def generate_hooks(topic):
    return [
        f"Stop scrolling — this is what it means when someone {topic}.",
        f"If someone {topic}, psychology explains THIS.",
        f"This behavior — {topic} — reveals something deep."
    ]

# ==============================
# TITLE ENGINE
# ==============================
def generate_title(topic):
    return random.choice([
        f"This explains why someone {topic}",
        f"The truth behind {topic}",
        f"NOBODY talks about this: {topic}",
        f"If someone {topic}, watch this"
    ])

# ==============================
# HASHTAGS
# ==============================
def generate_tags():
    return "#psychology #facts #mindset #shorts #viral"

# ==============================
# TTS
# ==============================
def tts(text, path):
    gTTS(text=text, lang="en").save(path)

# ==============================
# DOWNLOAD CLIPS
# ==============================
def download_clips(query, count=3):
    url = "https://api.pexels.com/videos/search"
    headers = {"Authorization": PEXELS_API_KEY}

    r = requests.get(url, headers=headers, params={"query": query, "per_page": count})
    data = r.json()

    paths = []

    if "videos" not in data:
        return []

    for i, v in enumerate(data["videos"][:count]):
        try:
            best = max(v["video_files"], key=lambda x: x.get("height", 0))
            path = f"{CLIPS}/clip_{i}.mp4"

            with open(path, "wb") as f:
                f.write(requests.get(best["link"]).content)

            paths.append(path)
        except:
            continue

    return paths

# ==============================
# FORMAT 9:16
# ==============================
def format_vertical(clip):
    target = 1080 / 1920
    ratio = clip.w / clip.h

    if ratio > target:
        clip = clip.crop(width=int(clip.h * target), x_center=clip.w / 2)
    else:
        clip = clip.crop(height=int(clip.w / target), y_center=clip.h / 2)

    return clip.resize((1080, 1920))

# ==============================
# WORD CAPTIONS (RETENTION STYLE)
# ==============================
def word_captions(script, duration):
    words = script.split()
    per = duration / len(words)

    clips = []

    for i, w in enumerate(words):
        img = Image.new("RGBA", (1080, 200), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("arial.ttf", 55)
        except:
            font = ImageFont.load_default()

        draw.rectangle([(320, 40), (760, 140)], fill=(0, 0, 0, 180))
        draw.text((540, 80), w.upper(), font=font, fill=(255, 255, 255), anchor="mm")

        clip = ImageClip(np.array(img)).set_duration(per)
        clip = clip.set_start(i * per).set_position(("center", "bottom")).fadein(0.03)

        clips.append(clip)

    return clips

# ==============================
# VIDEO BUILDER
# ==============================
def build_video(audio_path, temp_path, output_path, clips, script):
    audio = AudioFileClip(audio_path)
    duration = audio.duration

    per_clip = duration / len(clips)

    parts = []

    for c in clips:
        clip = VideoFileClip(c)

        if clip.duration > per_clip:
            start = random.uniform(0, clip.duration - per_clip)
            clip = clip.subclip(start, start + per_clip)

        clip = format_vertical(clip)
        clip = clip.resize(lambda t: 1 + 0.02 * t)

        parts.append(clip)

    base = concatenate_videoclips(parts).set_audio(audio)

    captions = word_captions(script, duration)

    final = CompositeVideoClip([base, *captions])

    final.write_videofile(temp_path, fps=24)

    final.close()
    base.close()
    audio.close()

    # move final to output
    os.rename(temp_path, output_path)

# ==============================
# LOGGING
# ==============================
def log(data):
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            json.dump([], f)

    with open(LOG_FILE, "r") as f:
        logs = json.load(f)

    logs.append(data)

    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)

# ==============================
# CLEANUP
# ==============================
def cleanup(files):
    for f in files:
        try:
            if os.path.exists(f):
                os.remove(f)
        except:
            pass

    gc.collect()
    time.sleep(1)

# ==============================
# MAIN ENGINE (WITH UPLOAD)
# ==============================
def main():
    n = int(input("How many videos? "))

    for i in range(n):
        idea = random.choice(ideas)
        print(f"\n🎬 {i+1}: {idea}")

        hooks = generate_hooks(idea)
        script = random.choice(hooks) + " " + generate_script(idea)

        query = get_query(idea)

        audio = f"{AUDIO}/voice_{i}.mp3"
        temp_video = f"{TEMP}/temp_{i}.mp4"
        final_video = f"{OUTPUT}/{idea.replace(' ','_')}_{i}.mp4"

        clips = download_clips(query)

        if not clips:
            print("⚠️ No clips found")
            continue

        tts(script, audio)
        build_video(audio, temp_video, final_video, clips, script)

        title = generate_title(idea)

        # ==============================
        # 🔥 AUTO UPLOAD TO YOUTUBE
        # ==============================
        video_id = upload_video(
            file_path=final_video,
            title=title,
            description="Psychology facts and human behavior insights #shorts",
            tags=generate_tags().split()
        )

        log({
            "idea": idea,
            "title": title,
            "file": final_video,
            "youtube_id": video_id
        })

        cleanup([audio] + clips)

        print(f"✅ Uploaded: {video_id}")

    print("\n🚀 DONE")

# ==============================
if __name__ == "__main__":
    main()