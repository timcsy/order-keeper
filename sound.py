# 自動管秩序
# pip install sounddevice numpy gtts pygame

import sounddevice as sd
import numpy as np
import time
from gtts import gTTS
import pygame
import os

# 初始化 pygame 混音器，用於播放音檔
pygame.mixer.init()

# 定義不同音量級別的警告訊息
warning_messages = {
    80: "到底在鬼叫什麼",
    90: "音量太高了，請大家安靜一點！我要生氣了！",
    100: "非常吵，請立刻安靜下來！！我真的要生氣了！"
}

# 儲存已生成的音檔，避免重複生成
audio_files = {}

# 將文字轉為語音並儲存為 mp3 檔案
def text_to_speech(text, filename):
    if not os.path.exists(filename):
        tts = gTTS(text=text, lang='zh-tw')  # 使用繁體中文
        tts.save(filename)
    return filename

# 播放音檔
def play_audio(filename):
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():  # 等待音檔播放完成
        time.sleep(0.1)

# 預先生成所有警告訊息的音檔
def pre_generate_audio_files():
    for level, message in warning_messages.items():
        filename = f"warning_{level}.mp3"
        audio_files[level] = text_to_speech(message, filename)

# 計算 RMS（均方根值）並轉成分貝
def calculate_decibel(audio_data):
    # 計算 RMS
    rms = np.sqrt(np.mean(np.square(audio_data)))
    # 轉成分貝，參考值設為 0.00002（大約是人類聽覺閾值）
    if rms == 0:  # 避免 log(0) 的情況
        return 0
    decibel = 20 * np.log10(rms / 0.00002)
    return decibel

# 監測音量並觸發警告
def monitor_sound(thresholds):
    sample_rate = 44100  # 採樣率
    duration = 0.5  # 每次錄音的時長（秒）

    print("開始監測音量... （按 Ctrl+C 停止）")
    last_warning_time = 0  # 用於控制警告的間隔時間
    warning_cooldown = 5  # 警告間隔至少 5 秒

    while True:
        # 錄音
        audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1)
        sd.wait()  # 等待錄音完成
        audio_data = audio_data.flatten()  # 將錄音資料展平為一維陣列

        # 計算分貝
        db = calculate_decibel(audio_data)
        print(f"目前音量: {db:.2f} 分貝")

        # 檢查是否超過任何閾值，並觸發警告
        current_time = time.time()
        for level in sorted(thresholds.keys(), reverse=True):
            if db > level and (current_time - last_warning_time) > warning_cooldown:
                print(f"音量超過 {level} 分貝，播放警告訊息...")
                play_audio(audio_files[level])
                last_warning_time = current_time
                break

        time.sleep(0.1)  # 短暫休息，避免過度占用 CPU

# 主程式
if __name__ == "__main__":
    try:
        # 預先生成音檔
        pre_generate_audio_files()
        # 開始監測音量
        monitor_sound(warning_messages)
    except KeyboardInterrupt:
        print("\n停止監測...")
    except Exception as e:
        print(f"發生錯誤: {e}")
