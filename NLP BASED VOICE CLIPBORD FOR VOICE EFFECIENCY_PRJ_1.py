import keyboard
import sounddevice as sd
import numpy as np
import queue
import pyperclip
import tkinter as tk
from faster_whisper import WhisperModel
import threading
import os
from datetime import datetime, timedelta

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
        show_history()

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

def show_history():
    text_output.delete("1.0", tk.END)  # Clear existing text in the UI
    recent = read_recent_history()

    # Show all history except the latest text
    for line in recent[:-1]:
        text_output.insert(tk.END, line + "\n")

    # Highlight the latest captured text (only the most recent one)
    if recent:
        latest_text = recent[-1]
        text_output.insert(tk.END, latest_text + "\n")
        text_output.tag_add("highlight", "end-1c linestart", "end")
        text_output.tag_configure("highlight", foreground="yellow", font=("Arial", 16, "bold"))

def start_transcription():
    threading.Thread(target=transcribe_audio).start()

def discard_text():
    text_output.delete("1.0", tk.END)
    tk_root.withdraw()

def clear_history():
    if os.path.exists(history_file):
        os.remove(history_file)
    show_history()  # Refresh UI to show empty history

def show_ui():
    tk_root.deiconify()
    show_history()
    start_transcription()

# UI Setup
tk_root = tk.Tk()
tk_root.title("🎤 Voice Clipboard (Whisper)")
tk_root.geometry("500x350")
tk_root.configure(bg="#1e1e1e")
tk_root.withdraw()

# Text output for showing history
text_output = tk.Text(tk_root, bg="#252526", fg="#ffffff", font=("Arial", 12), wrap=tk.WORD)
text_output.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

# Discard button
discard_button = tk.Button(tk_root, text="Discard", command=discard_text, bg="#ff5555", fg="#ffffff")
discard_button.pack(pady=5)

# Clear history button
clear_history_button = tk.Button(tk_root, text="Clear History", command=clear_history, bg="#ffcc00", fg="#ffffff")
clear_history_button.pack(pady=5)

# Set up hotkey for showing UI
keyboard.add_hotkey("alt+ctrl", show_ui)

print("✅ Voice Clipboard ready. Press Alt + Ctrl to speak.")
tk_root.mainloop()
