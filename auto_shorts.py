import os
import random
import time
import gc
import requests
import numpy as np
from gtts import gTTS
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

from youtube_uploader import upload_video

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

for d in [AUDIO, CLIPS, TEMP, OUTPUT]:
    os.makedirs(d, exist_ok=True)

# ==============================
# NICHE ENGINE
# ==============================
niches = {
    "psychology": {
        "ideas": ["avoid eye contact", "overthinking", "fake confidence"],
        "query": "person thinking emotional"
    },
    "dark": {
        "ideas": ["manipulation tactics", "silent control", "hidden intentions"],
        "query": "dark moody person"
    },
    "facts": {
        "ideas": ["brain tricks", "human behavior", "mind secrets"],
        "query": "science brain thinking"
    }
}

# ==============================
# SCRIPT ENGINE
# ==============================
def generate_script(idea):
    return (
        f"Stop scrolling. If someone {idea}, this means something deeper. "
        f"Most people miss this. "
        f"It reveals hidden emotion. "
        f"And once you see it, you can't unsee it."
    )

# ==============================
# TITLE
# ==============================
def generate_title(idea):
    return f"The truth about {idea} (watch this)"

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
    return clip.resize((1080, 1920))

# ==============================
# CAPTIONS (BOTTOM CLEAN)
# ==============================
def captions(script, duration):
    words = script.split()
    per = duration / len(words)

    clips = []

    for i, w in enumerate(words):
        img = Image.new("RGBA", (1080, 160), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("arial.ttf", 45)
        except:
            font = ImageFont.load_default()

        draw.rectangle([(250, 20), (830, 120)], fill=(0, 0, 0, 160))
        draw.text((540, 70), w.upper(), font=font, fill=(255, 255, 255), anchor="mm")

        clip = ImageClip(np.array(img)).set_duration(per)
        clip = clip.set_start(i * per).set_position(("center", 1550))

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
        parts.append(clip)

    base = concatenate_videoclips(parts).set_audio(audio).set_duration(duration)

    final = CompositeVideoClip([base, *captions(script, duration)])

    final.write_videofile(temp_path, fps=24)

    final.close()
    base.close()
    audio.close()

    os.rename(temp_path, output_path)

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

# ==============================
# MAIN
# ==============================
def main():
    n = int(input("How many videos? "))

    for i in range(n):
        niche = random.choice(list(niches.keys()))
        idea = random.choice(niches[niche]["ideas"])

        print(f"\n🎬 {i+1}: {idea}")

        script = generate_script(idea)

        audio = f"{AUDIO}/voice_{i}.mp3"
        temp_video = f"{TEMP}/temp_{i}.mp4"
        final_video = f"{OUTPUT}/{idea.replace(' ','_')}_{i}.mp4"

        clips = download_clips(niches[niche]["query"])

        if not clips:
            print("No clips found")
            continue

        tts(script, audio)
        build_video(audio, temp_video, final_video, clips, script)

        video_id = upload_video(
            file_path=final_video,
            title=generate_title(idea),
            description="Psychology shorts #viral #shorts",
            tags=["psychology", "viral", "shorts"]
        )

        cleanup([audio] + clips)

        print(f"✅ Uploaded: {video_id}")

        time.sleep(60)

    print("🚀 DONE")

if __name__ == "__main__":
    main()
