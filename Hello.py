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
from tempfile import NamedTemporaryFile
from pydub import AudioSegment

# Set Streamlit page configuration
st.set_page_config(
    page_title="Learning English",
    layout="wide",
    initial_sidebar_state="auto",
)

# Hide Streamlit footer and add custom footer text
hide_streamlit_style = """
<style>
footer {visibility: hidden;}
footer:after {
    content: '\u00A9 Made with Love <3 <3 <3';
    visibility: visible;
    display: block;
    position: relative;
    padding: 5px;
    top: 2px;
}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

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

def add_word(words, word, english_meaning, vietnamese_meaning):
    words[word] = {'English Meaning': english_meaning, 'Vietnamese Meaning': vietnamese_meaning}
    save_data(words)

def delete_selected_words(words, selected_rows):
    for i in selected_rows:
        words.pop(i, None)
    save_data(words)

def get_random_string(length):
    result_str = "".join(random.choice(string.ascii_letters) for i in range(length))
    return result_str

def convert_to_audio_parallel_with_status(words):
    audio_segments = []

    def generate_audio(w, em, vm):
        def save_and_load_audio(text, lang):
            tts = gTTS(text=text, lang=lang)
            temp_file_path = os.path.abspath("file_generated/" + get_random_string(10) + ".mp3")
            tts.save(temp_file_path)
            audio_clip = mpy.AudioFileClip(temp_file_path)
            return audio_clip

        w_audio = save_and_load_audio(f'{w}.', 'en')
        em_audio = save_and_load_audio(f'{em}.', 'en')
        vm_audio = save_and_load_audio(f'{vm}.', 'vi')

        return w_audio, em_audio, vm_audio

    progress_bar = st.progress(0)  # Initialize the progress bar

    def create_silent_audio(duration):
        return AudioSegment.silent(duration=duration)
    
    def create_audio_file_clip(audio_segment):
        temp_file_path = os.path.abspath("file_generated/" + get_random_string(10) + ".wav")
        audio_segment.export(temp_file_path, format="wav")
        
        # Create an AudioFileClip from the temporary file
        audio_file_clip = mpy.AudioFileClip(temp_file_path)
        
        return audio_file_clip
    with concurrent.futures.ThreadPoolExecutor() as executor:
        total_tasks = len(words)
        completed_tasks = 0

        for w, meanings in words.items():
            em = meanings['English Meaning']
            vm = meanings['Vietnamese Meaning']
            result = executor.submit(generate_audio, w, em, vm)
            while not result.done():
                time.sleep(0.1)  # Sleep for a short time
                completed_progress = completed_tasks / total_tasks
                progress_bar.progress(completed_progress)

            completed_tasks += 1
            progress = completed_tasks / total_tasks
            progress_bar.progress(progress)

            w_audio, em_audio, vm_audio = result.result()
            audio_segments.append(w_audio)
            audio_segments.append(create_audio_file_clip(create_silent_audio(500)))
            audio_segments.append(w_audio)
            audio_segments.append(create_audio_file_clip(create_silent_audio(500)))
            audio_segments.append(w_audio)
            audio_segments.append(create_audio_file_clip(create_silent_audio(1000)))
            audio_segments.append(em_audio)
            audio_segments.append(create_audio_file_clip(create_silent_audio(1000)))
            audio_segments.append(vm_audio)
            audio_segments.append(create_audio_file_clip(create_silent_audio(2000)))

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
    st.title('Learning English: If You Don’t Walk Today, You’ll Have To Run Tomorrow.')

    words = load_data()

    col1= st.empty()
    col2 = st.empty()
    col3 = st.empty()
    with col1:
        word = st.text_input('Word', key="Word").strip()
    with col2:
        english_meaning = st.text_input('English Meaning', key="English_Meaning").strip()
    with col3:
        vietnamese_meaning = st.text_input('Vietnamese Meaning', key="Vietnamese_Meaning").strip()
    
    def saveword():
        if vietnamese_meaning:
            if detect(vietnamese_meaning) != 'vi':
                st.error('Data add unsuccessful. Vietnamese meaning is not in Vietnamese.')
            else:
                add_word(words, word, english_meaning, vietnamese_meaning)
                st.success('Word added successfully.')
                st.session_state["Word"] = ""
                st.session_state["English_Meaning"] = ""
                st.session_state["Vietnamese_Meaning"] = ""
    st.button('Add', on_click=saveword) 

    st.header("Word Dictionary")
    df = pd.DataFrame([(word, meanings['English Meaning'], meanings['Vietnamese Meaning']) for word, meanings in words.items()],
                      columns=['Word', 'English Meaning', 'Vietnamese Meaning'])
    df['Select'] = [False] * len(df)

    selected_rows = []
    for i, row in df.iterrows():
        row['Select'] = st.checkbox(
            f'{row["Word"]} : {row["English Meaning"]} : {row["Vietnamese Meaning"]}', key=f'checkbox_{i}')
        if row['Select']:
            selected_rows.append(row["Word"]) 

    button_col1, button_col2 = st.columns(2)
    button_col3, button_col4 = st.columns(2)
    with button_col1:
        if st.button('Delete Selected'):
            delete_selected_words(words, selected_rows) 
            st.success('Data deleted successfully.')
            st.experimental_rerun()

    with button_col2:
        if st.button('Delete All'):
            words = {} 
            save_data(words)
            st.success('All data deleted successfully.')
            st.experimental_rerun()

    with button_col3:
        if st.button('Convert Selected to Audio'):
            selected_words_data = {w: words[w] for w in selected_rows}
            if selected_words_data:
                with st.spinner("Generating Audio..."):
                    convert_to_audio_parallel_with_status(selected_words_data)
                st.success('Audio Generation Complete!')
                with open('output.mp3', 'rb') as f:
                    st.audio(f.read(), format="audio/mp3")
                delete_all_files_in_folder("file_generated")
                try:
                    os.remove('output.mp3')
                except FileNotFoundError:
                    pass

    with button_col4:
        if st.button('Convert All to Audio'):
            with st.spinner("Generating Audio..."):
                convert_to_audio_parallel_with_status(words)
            st.success('Audio Generation Complete!')
            with open('output.mp3', 'rb') as f:
                st.audio(f.read(), format="audio/mp3")
            delete_all_files_in_folder("file_generated")
            try:
                os.remove('output.mp3')
            except FileNotFoundError:
                pass

if __name__ == "__main__":
    main()
