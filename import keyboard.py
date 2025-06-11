import keyboard
import sounddevice as sd
import queue
import json
import pyperclip
import tkinter as tk
import re
from vosk import Model, KaldiRecognizer

MODEL_PATH = r"C:\Users\sudha\Desktop\models\vosk-model-small-en-us-0.15"
model = Model(MODEL_PATH)

audio_queue = queue.Queue()

def callback(indata, frames, time, status):
    if status:
        print(status)
    audio_queue.put(bytes(indata))

def clean_text(text):
    if len(text) == 1:
        return text
    text = text.capitalize()
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"(\w)([,.!?])", r"\1\2", text)
    if text and text[-1] not in ".!?":
        text += "."
    return text

def listen_and_transcribe():
    recognizer = KaldiRecognizer(model, 16000)
    recognizer.SetWords(True)

    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16', channels=1, callback=callback):
        print("Listening... Speak now!")
        full_text = ""

        while True:
            data = audio_queue.get()
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "").strip()
                if text:
                    full_text = clean_text(text)
                    break
            else:
                partial_result = json.loads(recognizer.PartialResult()).get("partial", "").strip()
                if partial_result:
                    full_text = clean_text(partial_result)

        if full_text:
            print("You said:", full_text)
            pyperclip.copy(full_text)
            text_output.insert(tk.END, full_text + "\n")
            with open("voice_history.txt", "a", encoding="utf-8") as f:
                f.write(full_text + "\n")

def discard_text():
    text_output.delete("1.0", tk.END)
    tk_root.withdraw()

def show_ui():
    tk_root.deiconify()
    try:
        with open("voice_history.txt", "r", encoding="utf-8") as f:
            history = f.read()
        text_output.delete("1.0", tk.END)
        text_output.insert(tk.END, history)
    except FileNotFoundError:
        pass
    listen_and_transcribe()

tk_root = tk.Tk()
tk_root.title("Voice Clipboard")
tk_root.geometry("500x350")
tk_root.configure(bg="#1e1e1e")
tk_root.withdraw()

text_output = tk.Text(tk_root, bg="#252526", fg="#ffffff", font=("Arial", 12), wrap=tk.WORD)
text_output.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

discard_button = tk.Button(tk_root, text="Discard", command=discard_text, bg="#ff5555", fg="#ffffff")
discard_button.pack(pady=5)

keyboard.add_hotkey("alt+ctrl", show_ui)

print("Voice Clipboard running... Press Alt + Ctrl to start speaking.")
tk_root.mainloop()
