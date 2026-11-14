import requests, random, re, asyncio, glob, os, time, json
import edge_tts
from moviepy import (VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip,
                     CompositeAudioClip, vfx, afx)

FONT = next(iter(glob.glob("/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf")
                 + glob.glob("/usr/share/fonts/**/NotoSansDevanagari*.ttf", recursive=True)))
SPEED = 1.
MUSIC_VOLUME = 0.25
INTRO = "हे पार्थ, मेरी बात ध्यान से सुनो। भगवद्गीता में यह लिखा है कि"
OUTRO = "जय श्री कृष्ण।"
GEMINI_MODEL = "gemini-2.5-flash"   # error aaye to AI Studio mein current model naam dekho

COUNTS = {2:72, 3:43, 4:42, 5:29, 6:47, 7:30, 8:28, 9:34, 10:42,
          11:55, 12:20, 13:35, 14:27, 15:20, 16:24, 17:28, 18:78}

def clean(s):
    s = re.sub(r'[॥।|]*\s*[\d०-९]+\s*[.\-:]\s*[\d०-९]+\s*[॥।|]*', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()

def pick_shlok():
    used = set()
    if os.path.exists("used.txt"):
        used = set(open("used.txt", encoding="utf-8").read().split())
    allv = [(c, v) for c, n in COUNTS.items() for v in range(1, n + 1)]
    left = [x for x in allv if f"{x[0]}.{x[1]}" not in used]
    if not left:
        used = set(); left = allv
        open("used.txt", "w").write("")
    random.shuffle(left)
    for c, v in left[:40]:
        try:
            r = requests.get(f"https://vedicscriptures.github.io/slok/{c}/{v}", timeout=15).json()
            slok = clean(r["slok"])
            ht = clean(r.get("tej", {}).get("ht", ""))
            if len(ht) < 20 or len(ht) > 350:
                continue
            with open("used.txt", "a", encoding="utf-8") as f:
                f.write(f"{c}.{v}\n")
            return c, v, slok, ht
        except Exception as e:
            print("shlok fail", c, v, e)
    return 2, 47, "कर्मण्येवाधिकारस्ते मा फलेषु कदाचन।", "तुम्हारा अधिकार केवल कर्म करने में है, फल में कभी नहीं।"

def gemini(slok, ht):
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        return None
    prompt = (f"भगवद्गीता का शुद्ध श्लोक: {slok}\nहिंदी अर्थ: {ht}\n\n"
              "श्लोक को बिल्कुल मत बदलो। सिर्फ JSON दो, इन keys के साथ:\n"
              '"hook": 12 शब्दों से छोटा एक रोचक सवाल या बात (हिंदी),\n'
              '"meaning": 1-2 छोटे आसान वाक्यों में अर्थ, 200 अक्षर से कम (हिंदी),\n'
              '"caption": 2 छोटी पंक्तियाँ हिंदी में और अंत में 4 प्रासंगिक hashtags।')
    try:
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent",
            headers={"x-goog-api-key": key},
            json={"contents": [{"parts": [{"text": prompt}]}],
                  "generationConfig": {"responseMimeType": "application/json"}},
            timeout=60).json()
        d = json.loads(r["candidates"][0]["content"]["parts"][0]["text"])
        if d.get("hook") and d.get("meaning") and d.get("caption"):
            return d
    except Exception as e:
        print("gemini fail:", e)
    return None

def make_voice(text):
    for i in range(5):
        try:
            asyncio.run(edge_tts.Communicate(text, "hi-IN-MadhurNeural",
                        rate="+40%", pitch="-20Hz").save("voice.mp3"))
            return
        except Exception as e:
            print("edge-tts fail", i, e)
            time.sleep(8)
    from gtts import gTTS
    gTTS(text=text, lang="hi").save("voice.mp3")

ch, vs, slok, ht = pick_shlok()
g = gemini(slok, ht)
if g:
    meaning = g["meaning"].strip()
    caption = g["hook"].strip() + "\n\n" + g["caption"].strip()
else:
    meaning = ht
    caption = "भगवद्गीता का संदेश\n\n" + ht + "\n\n#bhagavadgita #geeta #krishna #motivation"
caption += f"\n\nगीता {ch}.{vs} | जय श्री कृष्ण 🙏"
full = INTRO + " " + meaning + " " + OUTRO

with open("caption.txt", "w", encoding="utf-8") as f:
    f.write(caption)

make_voice(full)
voice = AudioFileClip("voice.mp3")
dur = voice.duration + 0.5
 mp3s = [f for f in glob.glob("*.mp3") if f != "voice.mp3"]
if mp3s:
    music = AudioFileClip(random.choice(mp3s))
    music = music.with_effects([afx.AudioLoop(duration=dur), afx.MultiplyVolume(MUSIC_VOLUME)])
    audio = CompositeAudioClip([music, voice])
else:
    audio = voice

BG = random.choice(glob.glob("bg*.mp4"))
print("BG:", BG)
bg = VideoFileClip(BG).without_audio()
bg = bg.with_effects([vfx.MultiplySpeed(SPEED)])
if bg.duration < dur:
    bg = bg.with_effects([vfx.Loop(duration=dur)])
else:
    bg = bg.subclipped(0, dur)
bg = bg.resized(height=1920)
bg = bg.cropped(x_center=bg.w / 2, width=1080)

def bold(t, size, y, start, d):
    shadow = TextClip(font=FONT, text=t, font_size=size, color="black",
                      stroke_color="black", stroke_width=12,
                      method="caption", size=(950, None), text_align="center")
    main = TextClip(font=FONT, text=t, font_size=size, color="white",
                    stroke_color="white", stroke_width=4,
                    method="caption", size=(950, None), text_align="center")
    return [c.with_position(("center", y)).with_start(start).with_duration(d)
            for c in (shadow, main)]

layers = [bg]
layers += bold(slok, 50, 180, 0, dur)
words = full.split()
chunks = [" ".join(words[i:i+4]) for i in range(0, len(words), 4)]
t = 0
for c in chunks:
    d = voice.duration * len(c.split()) / len(words)
    layers += bold(c, 95, 800, t, d)
    t += d

final = CompositeVideoClip(layers).with_audio(audio)
final.write_videofile("output.mp4", fps=24, codec="libx264", audio_codec="aac")
print("DONE")
