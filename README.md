# YouTube Video Summarizer

A Streamlit app that fetches captions from any YouTube video and produces a concise summary using Hugging Face's `facebook/bart-large-cnn` model.

## Features
- Accepts full YouTube URLs and extracts the video ID automatically.
- Retrieves transcripts via `youtube-transcript-api`, handling disabled or missing captions gracefully.
- Summarizes long transcripts with tokenizer-aware chunking to avoid model limits.
- Optional GPU acceleration when PyTorch detects CUDA.
- Displays key timestamps and allows downloading the generated summary.

## Quick Start
```bash
# Create and activate the conda env (already set up in this repo)
conda activate d:\youtube_summ\.conda

# Install dependencies (if needed)
python -m pip install -r requirements.txt

# Launch the app
streamlit run app.py
```
Then open the provided local URL in your browser (default: http://localhost:8501), paste a YouTube link, and hit **Summarize**.

## Project Structure
- `app.py` – Streamlit UI orchestrating extraction, summarization, and display.
- `extractor.py` – Helpers to parse video IDs and fetch transcripts.
- `summazier.py` – Summarization logic built on Hugging Face transformers.
- `requirements.txt` – Python dependencies.
- `README.md` – You are here.

## Notes
- Hugging Face caches models under your user profile; the first run downloads ~1 GB.
- Some videos block transcript access; the app surfaces clear error messages in those cases.
- To avoid committing local environments, keep `.conda/` in `.gitignore` (already configured).

Happy summarizing! 🎥📝
