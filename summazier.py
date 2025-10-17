import re
from typing import Dict, Iterable, List, Optional, Tuple

import torch
from transformers import pipeline

from extractor import extract_video_id, get_transcript


DEFAULT_MODEL = "facebook/bart-large-cnn"
MAX_INPUT_TOKENS = 880  # stay well below BART's 1024 token encoder limit


_PIPELINE_CACHE: Dict[str, object] = {}


def _get_summarizer(model_name: str = DEFAULT_MODEL):
	"""Reuse the Hugging Face pipeline so we do not re-download on each call."""
	if model_name not in _PIPELINE_CACHE:
		device = 0 if torch.cuda.is_available() else -1
		_PIPELINE_CACHE[model_name] = pipeline(
			"summarization",
			model=model_name,
			tokenizer=model_name,
			device=device,
		)
	return _PIPELINE_CACHE[model_name]


def _chunk_text(
	text: str,
	tokenizer,
	max_tokens: int = MAX_INPUT_TOKENS,
) -> Iterable[str]:
	"""Split transcript into sentence-aware chunks under the token budget."""
	if not text:
		return []

	sentences = re.split(r"(?<=[.!?])\s+", text)
	chunks: List[str] = []
	current: List[str] = []
	current_tokens = 0

	for sentence in sentences:
		sentence = sentence.strip()
		if not sentence:
			continue

		token_count = len(tokenizer.encode(sentence, add_special_tokens=False))

		if token_count > max_tokens:
			# Sentence alone is too large; break it hard to avoid failures.
			words = sentence.split()
			temp_chunk: List[str] = []
			temp_tokens = 0
			for word in words:
				word_tokens = len(tokenizer.encode(word, add_special_tokens=False))
				if temp_chunk and temp_tokens + word_tokens > max_tokens:
					chunks.append(" ".join(temp_chunk))
					temp_chunk = [word]
					temp_tokens = word_tokens
				else:
					temp_chunk.append(word)
					temp_tokens += word_tokens
			if temp_chunk:
				chunks.append(" ".join(temp_chunk))
			continue

		if current and current_tokens + token_count > max_tokens:
			chunks.append(" ".join(current))
			current = [sentence]
			current_tokens = token_count
		else:
			current.append(sentence)
			current_tokens += token_count

	if current:
		chunks.append(" ".join(current))

	return chunks


def summarize_transcript_text(full_text: str, model_name: str = DEFAULT_MODEL) -> Optional[str]:
	"""Generate a concise summary from transcript text."""
	summarizer = _get_summarizer(model_name)
	tokenizer = summarizer.tokenizer

	chunks = list(_chunk_text(full_text, tokenizer))
	if not chunks:
		return None

	partial_summaries: List[str] = []
	for chunk in chunks:
		try:
			result = summarizer(chunk, max_length=220, min_length=60, do_sample=False)
			partial_summaries.append(result[0]["summary_text"].strip())
		except IndexError:
			# Rare case: token estimate was off; break the chunk in half and retry.
			words = chunk.split()
			if len(words) < 2:
				raise
			midpoint = len(words) // 2
			sub_chunks = [" ".join(words[:midpoint]), " ".join(words[midpoint:])]
			for sub_chunk in sub_chunks:
				if not sub_chunk.strip():
					continue
				result = summarizer(sub_chunk, max_length=200, min_length=40, do_sample=False)
				partial_summaries.append(result[0]["summary_text"].strip())

	if len(partial_summaries) == 1:
		return partial_summaries[0]

	combined = " ".join(partial_summaries)
	final_result = summarizer(combined, max_length=240, min_length=80, do_sample=False)
	return final_result[0]["summary_text"].strip()


def summarize_video(url: str, model_name: str = DEFAULT_MODEL) -> Tuple[Optional[Dict[str, str]], Optional[str]]:
	"""Fetch transcript for a YouTube video and return a summarised payload."""
	video_id = extract_video_id(url)
	if not video_id:
		return None, "Error: could not parse video id from URL"

	transcript_payload, transcript_error = get_transcript(video_id)
	if transcript_error:
		return None, transcript_error

	full_text = transcript_payload.get("full_text", "")
	if not full_text:
		return None, "Error: transcript is empty"

	summary_text = summarize_transcript_text(full_text, model_name=model_name)
	if not summary_text:
		return None, "Error: summarisation failed"

	payload: Dict[str, str] = {
		"video_id": video_id,
		"summary": summary_text,
		"language": transcript_payload.get("language"),
		"language_code": transcript_payload.get("language_code"),
	}
	return payload, None


if __name__ == "__main__":
	sample_url = "hhttps://www.youtube.com/watch?v=6zSrvSypsFM"
	summary_payload, summary_error = summarize_video(sample_url)
	if summary_error:
		print(summary_error)
	else:
		print(f"Summary for {summary_payload['video_id']}\n{summary_payload['summary']}")


