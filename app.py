import yt_dlp
import whisper
import gradio as gr
import os
from langchain_groq import ChatGroq
from wordcloud import WordCloud
from wordcloud import STOPWORDS
import matplotlib.pyplot as plt
from dotenv import load_dotenv

WHISPER_MODEL = whisper.load_model("base")
load_dotenv(".env")


def download_audio(url, output_path='downloaded_audio'):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        return None, f"Error downloading audio: {e}"
    
    final_path = output_path + ".mp3"
    if not os.path.exists(final_path):
        return None, "Download succeeded but file not found. Check FFmpeg output."
    
    return final_path, None

def transcribe_audio(audio_path):
    try:
        result = WHISPER_MODEL.transcribe(audio_path)
        transcription = result.get("text", "")
    except Exception as e:
        return None, f"Error in transcription: {e}"
    return transcription, None

def summarize_text(text):
    try:
        model = ChatGroq(model_name="llama-3.3-70b-versatile", api_key=os.getenv("GROQ_API_KEY"))
        messages = [
            {"role": "system", "content": "You are a helpful summarizer. Summarize the transcript clearly with bullet points, key ideas, and final takeaway."},
            {"role": "user", "content": text}
        ]
        summary = model.invoke(messages)
        summary_text = summary.content
    except Exception as e:
        return None, f"Error in summarization: {e}"
    return summary_text, None

def generate_wordcloud(text):
    try:
        stopwords = set(STOPWORDS)

        wc = WordCloud(
            width=800,
            height=400,
            background_color='white',
            stopwords=stopwords
        ).generate(text)
        
        plt.figure(figsize=(10, 5))
        plt.imshow(wc, interpolation='bilinear')
        plt.axis('off')
        wc_path = "wordcloud.png"
        plt.savefig(wc_path)
        plt.close()
        return wc_path, None
    except Exception as e:
        return None, f"Error generating word cloud: {e}"

def process_video(url):
    audio_file, error = download_audio(url)
    if error:
        return error, None
    
    transcription, error = transcribe_audio(audio_file)
    if os.path.exists(audio_file):
        os.remove(audio_file)
    if error:
        return error, None

    summary, error = summarize_text(transcription)
    if error:
        return error, None

    wc_image, error = generate_wordcloud(transcription)
    if error:
        return summary, None

    return summary, wc_image

iface = gr.Interface(
    fn=process_video,
    inputs=gr.Textbox(label="YouTube Video URL", placeholder="Enter the YouTube video URL here"),
    outputs=[
        gr.Textbox(label="Summary"),
        gr.Image(label="Word Cloud")
    ],
    title="YouTube Video Summarizer",
    description="Downloads audio from a YouTube video, transcribes it with Whisper, summarizes it with LLaMA-3, and generates a word cloud of the transcript."
)

if __name__ == "__main__":
    iface.launch()
