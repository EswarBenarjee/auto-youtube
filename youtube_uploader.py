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
# NICHE SYSTEM (V4)
# ==============================
niches = {
    "psychology": {
        "ideas": [
            "avoid eye contact",
            "overthinking",
            "fake confidence",
            "people pleasing"
        ],
        "query": "person thinking emotional",
        "style": "Psychology says"
    },
    "dark_psychology": {
        "ideas": [
            "manipulation tactics",
            "silent control",
            "hidden intentions",
            "power moves"
        ],
        "query": "dark moody person",
        "style": "Dark psychology reveals"
    },
    "motivation": {
        "ideas": [
            "discipline over motivation",
            "never give up",
            "focus in silence",
            "self control"
        ],
        "query": "success mindset",
        "style": "Successful people know"
    },
    "facts": {
        "ideas": [
            "human brain facts",
            "body language secrets",
            "mind tricks",
            "daily habits"
        ],
        "query": "science brain thinking",
        "style": "Fact:"
    },
    "social": {
        "ideas": [
            "why people lie",
            "fear rejection",
            "social anxiety",
            "trust issues"
        ],
        "query": "social interaction people",
        "style": "Social behavior shows"
    }
}

# ==============================
# SCRIPT ENGINE
# ==============================
def generate_script(niche, idea):
    base = niches[niche]["style"]

    return (
        f"{base} when someone {idea}, it reveals something deeper. "
        f"Most people completely miss this. "
        f"The truth is uncomfortable but real. "
        f"And once you see it, you can't unsee it."
    )

# ==============================
# HOOK ENGINE
# ==============================
def generate_hook(idea):
    return random.choice([
        f"Stop scrolling — this explains {idea}.",
        f"If you notice this — {idea} — watch carefully.",
        f"This one sign — {idea} — changes everything."
    ])

# ==============================
# TITLE ENGINE
# ==============================
def generate_title(niche, idea):
    return f"{idea} explained in 20 seconds #shorts"

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
# CAPTIONS (BOTTOM SMALL FIXED)
# ==============================
def captions(script, duration):
    words = script.split()
    per = duration / len(words)

    clips = []

    for i, w in enumerate(words):
        img = Image.new("RGBA", (1080, 180), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("arial.ttf", 45)
        except:
            font = ImageFont.load_default()

        draw.rectangle([(250, 40), (830, 140)], fill=(0, 0, 0, 160))
        draw.text((540, 90), w.upper(), font=font, fill=(255, 255, 255), anchor="mm")

        clip = ImageClip(np.array(img)).set_duration(per)
        clip = clip.set_start(i * per).set_position(("center", 1500))

        clips.append(clip)

    return clips

# ==============================
# VIDEO BUILDER
# ==============================
def build_video(audio_path, output_path, clips, script):
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

    base = concatenate_videoclips(parts).set_audio(audio)

    final = CompositeVideoClip([base, *captions(script, duration)])

    final.write_videofile(output_path, fps=24)

    final.close()
    base.close()
    audio.close()

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
# MAIN ENGINE (NICHE ROTATION)
# ==============================
def main():
    n = int(input("How many videos? "))

    for i in range(n):
        niche = random.choice(list(niches.keys()))
        idea = random.choice(niches[niche]["ideas"])

        print(f"\n🎬 {i+1}: [{niche}] {idea}")

        script = generate_hook(idea) + " " + generate_script(niche, idea)
        query = niches[niche]["query"]

        audio = f"{AUDIO}/voice_{i}.mp3"
        final_video = f"{OUTPUT}/{niche}_{idea.replace(' ','_')}_{i}.mp4"

        clips = download_clips(query)

        if not clips:
            print("⚠️ No clips found")
            continue

        tts(script, audio)
        build_video(audio, final_video, clips, script)

        title = generate_title(niche, idea)

        # 🔥 Upload
        video_id = upload_video(
            file_path=final_video,
            title=title,
            description=f"{niche} insights #shorts #viral",
            tags=[niche, "shorts", "viral"]
        )

        cleanup([audio] + clips)

        print(f"✅ Uploaded: {video_id}")

        time.sleep(60)  # anti-spam delay

    print("\n🚀 DONE")

if __name__ == "__main__":
    main()
