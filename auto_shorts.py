import os
import random
import time
import gc
import requests
import subprocess
import numpy as np
from gtts import gTTS
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv
import google.generativeai as genai

from youtube_uploader import upload_video

# ==============================
# ENV
# ==============================
load_dotenv(".env", override=True)

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

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
# NICHE ROTATION
# ==============================
NICHES = {
    "psychology": ["overthinking", "fake confidence", "people pleasing"],
    "money": ["saving habits", "rich mindset", "money mistakes"],
    "fitness": ["fat loss", "gym mistakes", "discipline"],
    "social": ["why people ignore you", "respect", "confidence"],
    "facts": ["brain facts", "human behavior", "daily habits"]
}

SCRIPT_STYLES = ["curiosity", "list", "story", "warning", "question", "fact"]

# ==============================
# SCRIPT ENGINE (DIVERSIFIED)
# ==============================
def generate_script(topic):
    style = random.choice(SCRIPT_STYLES)

    prompt = f"""
Create a HIGHLY viral YouTube Shorts script.

Topic: {topic}
Style: {style}

Rules:
- 20–35 words
- First sentence MUST hook instantly
- Create curiosity gap
- Make viewer feel they are missing something important
- Fast pacing
- No emojis or hashtags

Style meanings:
- curiosity → mystery
- list → "3 signs..."
- story → short relatable moment
- warning → "never ignore this"
- question → hook with question
- fact → surprising truth
"""

    try:
        res = model.generate_content(prompt)
        text = res.text.strip()

        if len(text.split()) < 10:
            raise Exception("Too short")

        return text
    except:
        return f"Stop scrolling. If you {topic}, this reveals something most people miss."

# ==============================
# TITLE ENGINE
# ==============================
def generate_title(topic):
    return random.choice([
        f"If you do this, watch this…",
        f"This explains {topic}",
        f"Nobody talks about this",
        f"3 signs of {topic}",
        f"Stop doing this immediately",
        f"This is why you {topic}",
        f"Hidden meaning of {topic}",
        f"You didn’t notice this about {topic}"
    ])

# ==============================
# AUDIO (FAST 1.2–1.5x)
# ==============================
def generate_audio(text, path):
    raw = path.replace(".mp3", "_raw.mp3")

    gTTS(text=text, lang="en").save(raw)

    speed = random.uniform(1.2, 1.5)

    cmd = f'ffmpeg -y -i "{raw}" -filter:a "atempo={speed}" "{path}"'
    subprocess.call(cmd, shell=True)

    os.remove(raw)

# ==============================
# VIDEO SEARCH (VARIED)
# ==============================
def get_query(topic):
    return random.choice([
        f"{topic} cinematic",
        f"{topic} emotional scene",
        f"{topic} human behavior",
        f"{topic} lifestyle",
        f"{topic} dark aesthetic",
        f"{topic} real life"
    ])

def download_clips(query, count=3):
    url = "https://api.pexels.com/videos/search"
    headers = {"Authorization": PEXELS_API_KEY}

    try:
        r = requests.get(url, headers=headers, params={"query": query, "per_page": count})
        data = r.json()
    except:
        return []

    paths = []

    for i, v in enumerate(data.get("videos", [])):
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
# CAPTIONS (BOTTOM CLEAN)
# ==============================
def captions(text, duration):
    words = text.split()
    per = duration / len(words)

    clips = []

    for i, w in enumerate(words):
        img = Image.new("RGBA", (1080, 150), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("arial.ttf", 40)
        except:
            font = ImageFont.load_default()

        draw.rectangle([(200, 30), (880, 120)], fill=(0, 0, 0, 160))
        draw.text((540, 75), w.upper(), font=font, fill=(255,255,255), anchor="mm")

        clip = ImageClip(np.array(img)).set_duration(per)
        clip = clip.set_start(i * per).set_position(("center", 1550))

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

    base = concatenate_videoclips(parts).set_audio(audio).set_duration(duration)

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

# ==============================
# MAIN ENGINE
# ==============================
def main():
    n = int(input("How many videos? "))

    for i in range(n):
        niche = random.choice(list(NICHES.keys()))
        topic = random.choice(NICHES[niche])

        print(f"\n🎬 {i+1}: [{niche}] {topic}")

        script = generate_script(topic)
        query = get_query(topic)

        audio = f"{AUDIO}/voice_{i}.mp3"
        output = f"{OUTPUT}/{niche}_{topic.replace(' ','_')}_{i}.mp4"

        clips = download_clips(query)

        if not clips:
            print("⚠️ No clips found")
            continue

        generate_audio(script, audio)
        build_video(audio, output, clips, script)

        video_id = upload_video(
            file_path=output,
            title=generate_title(topic),
            description=f"{niche} insights #shorts #viral",
            tags=[niche, "shorts", "viral"]
        )

        print("✅ Uploaded:", video_id)

        cleanup([audio] + clips)

        time.sleep(30)

    print("\n🚀 DONE")

if __name__ == "__main__":
    main()
