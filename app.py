# app.py
import streamlit as st
from extractor import extract_video_id, get_transcript
from summazier import summarize_transcript_text
from pytube import YouTube

# Initialize
if 'summarizer' not in st.session_state:
    st.session_state.summarizer = summarize_transcript_text

# UI Configuration
st.set_page_config(
    page_title="YouTube Summarizer",
    page_icon="🎥",
    layout="wide"
)

# Title and description
st.title("🎥 YouTube Video Summarizer")
st.markdown("Get AI-powered summaries of any YouTube video in seconds!")

# Sidebar for settings
with st.sidebar:
    st.header("⚙️ Settings")
    summary_length = st.slider("Summary Length", 100, 500, 250)
    show_timestamps = st.checkbox("Show Key Timestamps", value=True)
    
    st.markdown("---")
    st.markdown("### About")
    st.markdown("Built with Transformers & Streamlit")

# Main input
url_input = st.text_input(
    "Enter YouTube Video URL",
    placeholder="https://www.youtube.com/watch?v=..."
)

if st.button("🚀 Summarize", type="primary"):
    if not url_input:
        st.error("Please enter a YouTube URL")
    else:
        with st.spinner("Processing video..."):
            # Extract video ID
            video_id = extract_video_id(url_input)
            
            if not video_id:
                st.error("Invalid YouTube URL")
            else:
                # Get video metadata
                metadata_error = None
                yt_metadata = None

                try:
                    yt = YouTube(url_input)
                    yt_metadata = {
                        "thumbnail_url": yt.thumbnail_url,
                        "title": yt.title,
                        "author": yt.author,
                        "length_minutes": yt.length // 60,
                    }
                except Exception as exc:
                    metadata_error = str(exc)
                    yt_metadata = None

                if metadata_error:
                    st.warning("Could not load some video details; continuing with transcript lookup.")

                if yt_metadata:
                    col1, col2 = st.columns([1, 2])

                    with col1:
                        st.image(yt_metadata["thumbnail_url"], use_container_width=True)

                    with col2:
                        st.subheader(yt_metadata["title"])
                        st.caption(f"👤 {yt_metadata['author']} | ⏱️ {yt_metadata['length_minutes']} min")

                    st.markdown("---")

                # Get transcript
                with st.status("Fetching transcript..."):
                    transcript_payload, transcript_error = get_transcript(video_id)

                if transcript_error:
                    st.error(transcript_error)
                elif transcript_payload:
                    transcript_text = transcript_payload.get('full_text', '')
                    timestamps = transcript_payload.get('timestamped', [])

                    # Generate summary
                    with st.status("Generating summary..."):
                        summary = st.session_state.summarizer(transcript_text)

                    # Display results
                    st.success("✅ Summary Generated!")

                    # Summary section
                    st.markdown("### 📝 Summary")
                    st.markdown(summary)

                    # Download button
                    file_name_title = yt_metadata["title"] if yt_metadata else video_id
                    st.download_button(
                        label="📥 Download Summary",
                        data=summary,
                        file_name=f"{file_name_title}_summary.txt",
                        mime="text/plain"
                    )

                    # Timestamps section
                    if show_timestamps and timestamps:
                        st.markdown("---")
                        st.markdown("### ⏰ Key Timestamps")

                        # Sample every 10th timestamp for key moments
                        key_moments = timestamps[::10][:10]

                        for moment in key_moments:
                            minutes = int(moment['time'] // 60)
                            seconds = int(moment['time'] % 60)
                            st.markdown(
                                f"**[{minutes}:{seconds:02d}]** {moment['text']}"
                            )

                    # Full transcript (collapsible)
                    with st.expander("📄 View Full Transcript"):
                        st.text_area(
                            "Transcript",
                            transcript_text,
                            height=300,
                            disabled=True
                        )

                    if metadata_error:
                        st.caption(f"⚠️ Metadata warning: {metadata_error}")
                else:
                    st.error("Could not fetch transcript. Video may not have captions.")

# Footer
st.markdown("---")
st.markdown("Made with ❤️ using Streamlit & Transformers")
