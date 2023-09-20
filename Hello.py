import streamlit as st
from gtts import gTTS
import os
import json
import pandas as pd
import time
from langdetect import detect
from pydub import AudioSegment
from pydub.playback import play
import io
import tempfile
import random
import string
import moviepy.editor as mpy

def load_data():
    try:
        with open('data.json') as f:
            words = json.load(f)
    except FileNotFoundError:
        words = {}
    return words

def save_data(words):
    with open('data.json', 'w') as f:
        json.dump(words, f)

def add_word(words, word, meaning):
    words[word] = meaning
    save_data(words)

def delete_selected_words(words, selected_rows):
    for i in selected_rows:
        words.pop(i, None)
    save_data(words)

def get_random_string(length):
    result_str = "".join(random.choice(string.ascii_letters) for i in range(length))
    return result_str

def convert_to_audio(words):
    audio_segments = []  # List to store audio segments
    
    for w, m in words.items():
        # Generate audio for the word
        detectLanguage(w)
        tts_word = gTTS(text=f'{w}. means.', lang=detectLanguage(w))
        file_path = "file_generated/" + get_random_string(10) + ".mp3"
        tts_word.save(os.path.abspath(file_path))
        w_audio = mpy.AudioFileClip(os.path.abspath(file_path))
        # Generate audio for the meaning
        tts_meaning = gTTS(text=m, lang=detectLanguage(m))
        m_tempfile = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        tts_meaning.save(m_tempfile.name)
        m_audio = AudioSegment.from_mp3(m_tempfile.name)
        # Append the word and meaning audio to the list
        audio_segments.append(w_audio)
        audio_segments.append(m_audio)

    # Combine all audio segments into a single audio file
    combined_audio = AudioSegment.empty()
    for segment in audio_segments:
        combined_audio += segment

    # Save the combined audio to a file
    combined_audio.export('output.mp3', format='mp3')

def detectLanguage(text):
    lang = detect(text)
    return lang

def main():
    st.title('From Ha Noi With Love')
    words = load_data()
    col1 = st.empty()
    col2 = st.empty()
    word = col1.text_input('Word').strip()
    meaning = col2.text_input('Meaning').strip()

    if st.button('Add'):
        add_word(words, word, meaning)
        col1.empty()
        col2.empty()
        st.experimental_rerun()

    selected_rows = []
    df = pd.DataFrame(words.items(), columns=['Word', 'Meaning'])
    df['Select'] = [False] * len(df)

    for i, row in df.iterrows():
        row['Select'] = st.checkbox(
            f'{row["Word"]} : {row["Meaning"]}', key=f'checkbox_{i}')
        if row['Select']:
            selected_rows.append(row["Word"])  # Store the selected words, not indices

    if st.button('Delete Selected'):
        delete_selected_words(words, selected_rows)  # Pass selected words, not DataFrame
        st.success('Data deleted successfully.')
        time.sleep(0.5)
        st.experimental_rerun()


    if st.button('Delete All'):
        words = {}  # Clear the words dictionary
        save_data(words)
        st.success('Data deleted successfully.')
        time.sleep(0.5)
        st.experimental_rerun()

        
    if st.button('Convert to Audio'):
        convert_to_audio(words)
        print('done')
        with open('output.mp3', 'rb') as f:
            st.download_button('Download Audio', f.read(), 'output.mp3')

if __name__ == "__main__":
    main()
