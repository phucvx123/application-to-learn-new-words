import streamlit as st
from gtts import gTTS
import os
import json
import pandas as pd
import time
from langdetect import detect
import random
import string
import moviepy.editor as mpy
import concurrent.futures


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

def convert_to_audio_parallel(words):
    audio_segments = []

    def generate_audio(w, m):
        tts_word = gTTS(text=f'{w}. means.', lang='en')
        file_word_path = "file_generated/" + get_random_string(10) + ".mp3"
        tts_word.save(os.path.abspath(file_word_path))
        w_audio = mpy.AudioFileClip(os.path.abspath(file_word_path))

        tts_meaning = gTTS(text=m, lang='vi')
        file_meaning_path = "file_generated/" + get_random_string(10) + ".mp3"
        tts_meaning.save(file_meaning_path)
        m_audio = mpy.AudioFileClip(file_meaning_path)

        return w_audio, m_audio

    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = [executor.submit(generate_audio, w, m) for w, m in words.items()]

    for result in results:
        w_audio, m_audio = result.result()
        audio_segments.append(w_audio)
        audio_segments.append(m_audio)

    concatenated_audio = mpy.concatenate_audioclips(audio_segments)
    concatenated_audio_file = 'output.mp3'
    concatenated_audio.write_audiofile(concatenated_audio_file)

def detectLanguage(text):
    lang = detect(text)
    return lang

def delete_all_files_in_folder(folder_path):
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")

def main():
    st.title('Học,Học nữa, Học mãi')
    words = load_data()
    col1 = st.empty()
    col2 = st.empty()
    word = col1.text_input('Word').strip()
    meaning = col2.text_input('Meaning').strip()
    if st.button('Add') and meaning:
        if detect(meaning) != 'vi':
            st.error('Data add unsuccessful. Meaning is not in Vietnamese.')
        else:
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
        convert_to_audio_parallel(words)
        with open('output.mp3', 'rb') as f:
            st.download_button('Download Audio', f.read(), 'output.mp3')
        delete_all_files_in_folder("file_generated")
        # Delete the 'output.mp3' file
        try:
            os.remove('output.mp3')
        except FileNotFoundError:
            pass

if __name__ == "__main__":
    main()
