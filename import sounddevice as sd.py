import keyboard
import sounddevice as sd
import numpy as np
import queue
import pyperclip
import tkinter as tk
from tkinter import font
from faster_whisper import WhisperModel
import threading
import os
from datetime import datetime, timedelta

# Whisper Model Path
MODEL_PATH = "C:/Users/sudha/Desktop/PRACTICALS/PROJECTS!!/whisper-main"
model = WhisperModel(MODEL_PATH, device="cpu", compute_type="int8")

samplerate = 16000
channels = 1
dtype = 'int16'
blocksize = 4000
audio_queue = queue.Queue()
history_file = "history.txt"

def audio_callback(indata, frames, time, status):
    if status:
        print("Status:", status)
    audio_queue.put(indata.copy())

def transcribe_audio():
    buffer = []
    with sd.InputStream(samplerate=samplerate, channels=channels, dtype=dtype, blocksize=blocksize, callback=audio_callback):
        print("🎙️ Listening... Speak now.")
        for _ in range(40):  # ~5 seconds
            audio = audio_queue.get()
            buffer.append(audio)
        print("⏹️ Done recording. Transcribing...")

    audio_data = np.concatenate(buffer, axis=0).flatten().astype(np.float32) / 32768.0
    segments, _ = model.transcribe(audio_data, language="en", beam_size=5)
    full_text = " ".join(segment.text.strip() for segment in segments).strip().capitalize()

    if full_text:
        print("📝 You said:", full_text)
        pyperclip.copy(full_text)
        save_to_history(full_text)
        show_history(full_text)

def save_to_history(text):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    entry = f"{timestamp} {text.strip()}"
    with open(history_file, "a", encoding="utf-8") as f:
        f.write(entry + "\n")

def read_recent_history():
    if not os.path.exists(history_file):
        return []

    with open(history_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    cutoff = datetime.now() - timedelta(days=5)
    recent_lines = []
    for line in reversed(lines):
        try:
            time_str = line.split("]")[0][1:]
            timestamp = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            if timestamp >= cutoff:
                recent_lines.append(line.strip())
        except:
            continue

    return recent_lines

def show_history(latest_text=""):
    text_output.config(state=tk.NORMAL)
    text_output.delete("1.0", tk.END)

    if latest_text:
        text_output.insert(tk.END, f"{latest_text}\n\n", "latest")

    for line in read_recent_history():
        text_output.insert(tk.END, line + "\n")

    text_output.config(state=tk.DISABLED)

def clear_history():
    if os.path.exists(history_file):
        open(history_file, "w").close()
    text_output.config(state=tk.NORMAL)
    text_output.delete("1.0", tk.END)
    text_output.config(state=tk.DISABLED)

def start_transcription():
    threading.Thread(target=transcribe_audio).start()

def discard_text():
    text_output.config(state=tk.NORMAL)
    text_output.delete("1.0", tk.END)
    text_output.config(state=tk.DISABLED)
    tk_root.withdraw()

def show_ui():
    tk_root.deiconify()
    show_history()

# 🪟 UI Setup
tk_root = tk.Tk()
tk_root.title("🎤 Voice Clipboard (Whisper)")
tk_root.geometry("550x400")
tk_root.configure(bg="#1e1e1e")
tk_root.withdraw()

text_output = tk.Text(tk_root, bg="#252526", fg="#ffffff", font=("Arial", 12), wrap=tk.WORD)
text_output.tag_config("latest", foreground="#00ffff", font=("Arial", 16, "bold"))
text_output.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

button_frame = tk.Frame(tk_root, bg="#1e1e1e")
button_frame.pack(pady=5)

discard_button = tk.Button(button_frame, text="Discard", command=discard_text, bg="#ff5555", fg="#ffffff")
discard_button.pack(side=tk.LEFT, padx=10)

clear_button = tk.Button(button_frame, text="Clear History", command=clear_history, bg="#ffaa00", fg="#000000")
clear_button.pack(side=tk.LEFT, padx=10)

keyboard.add_hotkey("alt+ctrl", show_ui)

print("✅ Voice Clipboard ready. Press Alt + Ctrl to speak.")
tk_root.mainloop()
