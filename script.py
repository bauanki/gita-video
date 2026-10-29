import requests, random, re, asyncio, glob, os
import edge_tts
from moviepy import (VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip,
                     CompositeAudioClip, vfx, afx)

FONT = next(iter(glob.glob("/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf")
                 + glob.glob("/usr/share/fonts/**/NotoSansDevanagari*.ttf", recursive=True)))
BG = "bg.mp4"
SPEED = 1.2
MUSIC_VOLUME = 0.30
INTRO = "हे पार्थ, मेरी बात ध्यान से सुनो और समझो भगवद्गीता में यह लिखा है कि" god

def clean(s):
    s = re.sub(r'[॥।|]*\s*[\d०-९]+\s*[.\-:]\s*[\d०-९]+\s*[॥।|]*', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()

def get_shlok():
    try:
        ch, v = random.choice([(2,47),(2,48),(2,14),(3,35),(4,7),(6,5),(18,66),(2,20),(9,22),(12,15)])
        r = requests.get(f"https://vedicscriptures.github.io/slok/{ch}/{v}", timeout=15).json()
        return clean(r["slok"]), clean(r["tej"]["ht"])
    except Exception as e:
        print("API fail:", e)
        return ("कर्मण्येवाधिकारस्ते मा फलेषु कदाचन।",
                "तुम्हारा अधिकार केवल कर्म करने में है, फल में कभी नहीं।")

slok, meaning = get_shlok()
full = INTRO + " " + meaning

with open("caption.txt", "w", encoding="utf-8") as f:
    f.write(slok + "\n\n" + meaning + "\n\n#bhagavadgita #geeta #krishna #motivation #hindu #reels")

asyncio.run(edge_tts.Communicate(full, "hi-IN-MadhurNeural",
                                 rate="+40%", pitch="-20Hz").save("voice.mp3"))
voice = AudioFileClip("voice.mp3")
dur = voice.duration + 0.5

mp3s = [f for f in glob.glob("*.mp3") if f != "voice.mp3"]
if mp3s:
    music = AudioFileClip(mp3s[0])
    music = music.with_effects([afx.AudioLoop(duration=dur), afx.MultiplyVolume(MUSIC_VOLUME)])
    audio = CompositeAudioClip([music, voice])
else:
    audio = voice

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
