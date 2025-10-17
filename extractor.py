# transcript_extractor.py
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api import TranscriptsDisabled, NoTranscriptFound
import re
from urllib.parse import urlparse, parse_qs


def extract_video_id(url):
    """Return a YouTube video ID parsed from supported URL formats."""
    if not url:
        return None

    parsed = urlparse(url.strip())
    hostname = (parsed.hostname or '').lower()

    if hostname in {'youtu.be', 'www.youtu.be'}:
        video_id = parsed.path.lstrip('/')
        return video_id or None

    if hostname.endswith('youtube.com'):
        path_parts = parsed.path.strip('/').split('/')

        if parsed.path == '/watch':
            return parse_qs(parsed.query).get('v', [None])[0]

        if len(path_parts) >= 2 and path_parts[0] in {'embed', 'shorts'}:
            return path_parts[1] or None

    match = re.search(r'(?:v=|/)([0-9A-Za-z_-]{11})', url)
    if match:
        return match.group(1)

    return None

def get_transcript(video_id):
    """Fetch transcript data via YouTubeTranscriptApi.fetch and return raw snippets."""
    if not video_id:
        return None, "Error: missing video id"

    try:
        fetched_transcript = YouTubeTranscriptApi().fetch(video_id)
        raw_segments = fetched_transcript.to_raw_data()

        full_text = " ".join(segment.get('text', '').strip() for segment in raw_segments).strip()

        timestamped_text = [
            {
                'time': segment.get('start', 0.0),
                'duration': segment.get('duration', 0.0),
                'text': segment.get('text', '').strip(),
            }
            for segment in raw_segments
        ]

        return {
            'segments': raw_segments,
            'full_text': full_text,
            'timestamped': timestamped_text,
            'language': getattr(fetched_transcript, 'language', None),
            'language_code': getattr(fetched_transcript, 'language_code', None),
            'is_generated': getattr(fetched_transcript, 'is_generated', None),
        }, None

    except TranscriptsDisabled:
        return None, "Error: transcripts are disabled for this video"
    except NoTranscriptFound:
        return None, "Error: no transcript available for this video"
    except Exception as exc:
        return None, f"Error: {exc}"

# Quick manual test
video_url = "https://www.youtube.com/watch?v=mQ7e6Q3WYGk"
parsed_video_id = extract_video_id(video_url)
transcript_payload, transcript_error = get_transcript(parsed_video_id)
print(f"Extracted video ID: {parsed_video_id}")
if transcript_error:
    print(transcript_error)
else:
    print(f"Transcript segments: {(transcript_payload['full_text'])}")
