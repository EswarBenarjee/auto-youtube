import os, random, requests, asyncio, time, textwrap
import numpy as np
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv
import edge_tts
import google.generativeai as genai
from youtube_uploader import upload_video

# ==============================
# ENV
# ==============================
load_dotenv()
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-flash-latest")

# ==============================
# PATHS
# ==============================
ASSETS = "assets"
AUDIO = f"{ASSETS}/audio"
CLIPS = f"{ASSETS}/clips"
OUTPUT = "output"
FONTS = f"{ASSETS}/fonts"

for d in [AUDIO, CLIPS, OUTPUT, FONTS]:
    os.makedirs(d, exist_ok=True)

# ==============================
# FONT
# ==============================
def get_font(size):
    try:
        return ImageFont.truetype(f"{FONTS}/Montserrat-Bold.ttf", size)
    except:
        return ImageFont.load_default()

def clean_text(t):
    return t.replace("“", '"').replace("”", '"').replace("’", "'")

# ==============================
# 🔥 BETTER HOOK ENGINE
# ==============================
def generate_content():
    prompt = """
    Generate 5 EXTREMELY VIRAL YouTube Shorts hooks.

    Style:
    - Aggressive
    - Emotional trigger
    - Make viewer feel attacked or curious

    Examples:
    - You're broke because of this
    - This is why you never win
    - Stop doing this immediately
    - Rich people hide this
    - You're wasting your life

    Rules:
    - Max 6 words
    - No fluff
    - No generic phrases

    Also generate a short motivational script (5-7 lines).

    Output format:
    HOOK1:
    HOOK2:
    HOOK3:
    HOOK4:
    HOOK5:
    SCRIPT:
    """

    try:
        res = model.generate_content(prompt).text

        hooks = [
            res.split("HOOK1:")[1].split("HOOK2:")[0].strip(),
            res.split("HOOK2:")[1].split("HOOK3:")[0].strip(),
            res.split("HOOK3:")[1].split("HOOK4:")[0].strip(),
            res.split("HOOK4:")[1].split("HOOK5:")[0].strip(),
            res.split("HOOK5:")[1].split("SCRIPT:")[0].strip()
        ]

        script = res.split("SCRIPT:")[1].strip()

        return hooks, script

    except:
        return [
            "You're broke because of this",
            "This is why you fail",
            "Stop doing this now",
            "Rich people avoid this",
            "You're wasting your life"
        ], "Success is not luck. It is discipline. Most people quit early. Winners don't."

# ==============================
# AUDIO
# ==============================
async def tts_async(text, path):
    communicate = edge_tts.Communicate(text, "en-US-GuyNeural", rate="-10%")
    await communicate.save(path)

def generate_audio(text, path):
    asyncio.run(tts_async(text, path))

# ==============================
# 🔥 DOWNLOAD MULTIPLE CLIPS
# ==============================
def download_clips(query, count=3):
    url = "https://api.pexels.com/videos/search"
    headers = {"Authorization": PEXELS_API_KEY}

    r = requests.get(url, headers=headers, params={"query": query, "per_page": count})
    data = r.json()

    paths = []

    for i, v in enumerate(data.get("videos", [])):
        try:
            best = min(
                v["video_files"],
                key=lambda x: abs(x.get("height", 720) - 720)
            )

            path = f"{CLIPS}/clip_{time.time()}_{i}.mp4"

            with open(path, "wb") as f:
                f.write(requests.get(best["link"]).content)

            paths.append(path)
        except:
            continue

    return paths

# ==============================
# FORMAT
# ==============================
def format_vertical(clip):
    if clip.w > 1280:
        clip = clip.resize(width=1280)

    target = 9/16
    ratio = clip.w/clip.h

    if ratio > target:
        clip = clip.crop(width=int(clip.h*target), x_center=clip.w/2)
    else:
        clip = clip.crop(height=int(clip.w/target), y_center=clip.h/2)

    return clip.resize((720,1280))

# ==============================
# CAPTIONS
# ==============================
def captions(script, duration):
    words = script.split()
    per = duration / len(words)

    clips = []

    for i, word in enumerate(words):
        word = clean_text(word)

        img = Image.new("RGBA", (1080, 260), (0,0,0,0))
        draw = ImageDraw.Draw(img)

        font = get_font(55)

        draw.rounded_rectangle([(100,20),(980,240)], radius=25, fill=(0,0,0,160))

        draw.text((540,130), word.upper(), font=font, fill=(255,255,255), anchor="mm")

        clip = ImageClip(np.array(img)).set_duration(per)
        clip = clip.set_start(i*per).set_position(("center",1500))

        clips.append(clip)

    return clips

# ==============================
# HOOK
# ==============================
def hook_anim(hook):
    words = clean_text(hook).upper().split()
    per = 2 / len(words)

    clips = []

    for i, w in enumerate(words):
        img = Image.new("RGBA", (1080,1920), (0,0,0,0))
        draw = ImageDraw.Draw(img)

        font = get_font(110)

        draw.text((540,700), w, font=font, fill=(255,255,255), anchor="mm")

        clip = ImageClip(np.array(img)).set_duration(per)
        clip = clip.set_start(i*per)

        clips.append(clip)

    return clips

# ==============================
# BUILD VIDEO
# ==============================
def build_video(audio_path, output_path, script, hook):
    audio = AudioFileClip(audio_path)
    duration = audio.duration

    # 🔥 MULTIPLE CLIPS
    clip_paths = download_clips("success motivation", 5)

    if not clip_paths:
        print("❌ No clips")
        return

    parts = []
    per = duration / len(clip_paths)

    for p in clip_paths:
        clip = VideoFileClip(p, target_resolution=(1280,720))

        if clip.duration > per:
            clip = clip.subclip(0, per)

        clip = format_vertical(clip)

        # ❌ NO FADE
        parts.append(clip)

    base = concatenate_videoclips(parts).set_audio(audio)

    final = CompositeVideoClip([
        base,
        *hook_anim(hook),
        *captions(script, duration)
    ])

    final.write_videofile(output_path, fps=24)

# ==============================
# MAIN
# ==============================
def main():
    n = int(input("How many videos? "))

    for i in range(n):
        print(f"\n🎬 Creating video {i+1}")

        hooks, script = generate_content()
        hook = random.choice(hooks)

        print("🎯 Selected Hook:", hook)

        audio = f"{AUDIO}/voice_{i}.mp3"
        output = f"{OUTPUT}/video_{i}.mp4"

        generate_audio(script, audio)
        build_video(audio, output, script, hook)

        try:
            vid = upload_video(
                file_path=output,
                title=hook,
                description="Billionaire mindset #shorts",
                tags=["success","mindset"]
            )
            print("✅ Uploaded:", vid)
        except Exception as e:
            print("⚠️ Upload failed:", e)

        time.sleep(20)

    print("\n🚀 DONE")

if __name__ == "__main__":
    main()
