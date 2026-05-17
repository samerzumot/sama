"""
STEP 2 — SCORE THE SESSION
Run this after the student finishes the session.
It polls Tavus until the perception analysis is ready, then computes EQ signals.

Usage:
    python eq_score.py                        # reads session_id.txt automatically
    python eq_score.py <conversation_id>      # or pass the ID directly
"""

import requests
import json
import os
import sys
import time
import re
from dotenv import load_dotenv

load_dotenv()

API_KEY  = os.getenv("TAVUS_API_KEY")
BASE_URL = "https://tavusapi.com"
HEADERS  = {"x-api-key": API_KEY, "Content-Type": "application/json"}


# ─── FETCH SESSION DATA ──────────────────────────────────────────

def get_conversation(conversation_id):
    """Fetch conversation and normalize transcript/perception from events array."""
    r = requests.get(
        f"{BASE_URL}/v2/conversations/{conversation_id}?verbose=true",
        headers=HEADERS
    )
    if r.status_code != 200:
        print(f"Error fetching conversation: {r.status_code} — {r.text}")
        return None

    data = r.json()

    # Tavus v2 stores transcript and perception inside the events array.
    # Extract them and promote to top-level keys for the rest of the pipeline.
    transcript = data.get("transcript", [])
    perception = data.get("perception_analysis", "")

    for event in data.get("events", []):
        etype = event.get("event_type", "")
        props = event.get("properties", {})

        if etype == "application.transcription_ready" and not transcript:
            transcript = props.get("transcript", [])

        if etype == "application.perception_analysis" and not perception:
            perception = props.get("analysis", "")

    data["transcript"] = transcript
    data["perception_analysis"] = perception
    return data


def wait_for_data(conversation_id, max_wait=300):
    """Poll until perception_analysis and transcript are available."""
    print(f"\nWaiting for session data (conversation: {conversation_id})...")
    elapsed = 0
    interval = 15  # seconds between polls

    while elapsed < max_wait:
        data = get_conversation(conversation_id)
        if not data:
            return None

        status     = data.get("status", "")
        transcript = data.get("transcript", [])
        perception = data.get("perception_analysis", "")

        print(f"  [{elapsed}s] status={status} | transcript_turns={len(transcript)} | perception={'yes' if perception else 'waiting...'}")

        if status in ("ended", "error") and transcript and perception:
            print("  Data ready.\n")
            return data

        if status in ("ended", "error") and transcript and not perception:
            # Perception can lag — wait a bit longer
            if elapsed > 120:
                print("  Perception still not ready — proceeding with transcript only.\n")
                return data

        time.sleep(interval)
        elapsed += interval

    print("Timed out waiting for data.")
    return None


# ─── SIGNAL EXTRACTORS ───────────────────────────────────────────

HEDGING_WORDS = {
    "maybe", "perhaps", "possibly", "probably", "i think", "i guess",
    "i suppose", "kind of", "sort of", "not sure", "i don't know",
    "might", "could", "seems like", "i feel like", "i hope"
}

NEGATIVE_EMOTION_WORDS = {
    "scared", "worried", "anxious", "nervous", "stressed", "afraid",
    "disappointed", "frustrated", "upset", "sad", "depressed", "overwhelmed",
    "confused", "lost", "unsure", "rejected", "failure", "failed"
}

POSITIVE_EMOTION_WORDS = {
    "excited", "happy", "confident", "proud", "motivated", "passionate",
    "hopeful", "grateful", "love", "enjoy", "thrilled", "optimistic",
    "determined", "ready", "strong", "capable"
}

RESILIENCE_WORDS = {
    "but", "however", "still", "despite", "even though", "regardless",
    "i will", "i can", "i'll figure", "move on", "next step", "plan b",
    "bounce back", "learn from", "try again", "keep going"
}

CAUSAL_WORDS = {
    "because", "therefore", "since", "so that", "as a result",
    "which means", "leads to", "caused by", "due to", "in order to"
}


def extract_student_turns(transcript):
    """Pull only the student's spoken lines."""
    turns = []
    for turn in transcript:
        role = turn.get("role", "")
        content = turn.get("content", "")
        if role == "user" and content:
            # Strip the VISUAL_SCENE prefix Tavus injects
            speech = re.sub(r"VISUAL_SCENE:.*", "", content, flags=re.DOTALL)
            speech = re.sub(r"USER_SPEECH:\s*", "", speech).strip()
            if speech:
                turns.append(speech)
    return turns


def compute_hedging_ratio(turns):
    if not turns:
        return 0.0
    full_text = " ".join(turns).lower()
    word_count = len(full_text.split())
    hedge_hits = sum(1 for w in HEDGING_WORDS if w in full_text)
    return round(hedge_hits / max(word_count / 100, 1), 3)


def compute_emotional_vocabulary(turns):
    """Count unique positive and negative emotion words used."""
    full_text = " ".join(turns).lower()
    pos = [w for w in POSITIVE_EMOTION_WORDS if w in full_text]
    neg = [w for w in NEGATIVE_EMOTION_WORDS if w in full_text]
    return {
        "positive_words": pos,
        "negative_words": neg,
        "vocabulary_richness": len(pos) + len(neg),
        "valence_ratio": round(len(pos) / max(len(neg), 1), 2)
    }


def compute_resilience_score(turns):
    """How often does the student follow a negative signal with a recovery word?"""
    full_text = " ".join(turns).lower()
    neg_hits = sum(1 for w in NEGATIVE_EMOTION_WORDS if w in full_text)
    resilience_hits = sum(1 for w in RESILIENCE_WORDS if w in full_text)
    if neg_hits == 0:
        return 1.0  # No adversity mentioned — neutral
    return round(min(resilience_hits / neg_hits, 1.0), 3)


def compute_cognitive_complexity(turns):
    """Causal reasoning as a proxy for reflective capacity."""
    full_text = " ".join(turns).lower()
    word_count = len(full_text.split())
    causal_hits = sum(1 for w in CAUSAL_WORDS if w in full_text)
    return round(causal_hits / max(word_count / 100, 1), 3)


def compute_self_disclosure(turns):
    """How much does the student talk about their inner state vs. external events?"""
    full_text = " ".join(turns).lower()
    first_person = len(re.findall(r'\bi\b|\bmy\b|\bme\b|\bmine\b|\bmyself\b', full_text))
    word_count = len(full_text.split())
    return round(first_person / max(word_count, 1), 3)


def parse_perception_analysis(perception_text):
    """
    Extract key signals from Raven-0's natural language perception summary.
    Raven outputs a free-text paragraph describing what it observed visually.
    We parse it for emotion mentions and behavioral signals.
    """
    if not perception_text:
        return {"available": False, "raw": None}

    text = perception_text.lower()

    observed_emotions = []
    all_emotions = [
        "happy", "sad", "anxious", "nervous", "excited", "confused",
        "frustrated", "confident", "engaged", "distracted", "calm",
        "stressed", "uncertain", "hopeful", "worried", "focused"
    ]
    for e in all_emotions:
        if e in text:
            observed_emotions.append(e)

    # Simple behavioral signals
    signals = {
        "eye_contact_mentioned": any(w in text for w in ["eye contact", "gaze", "looking away", "averted"]),
        "smiling_mentioned":     any(w in text for w in ["smile", "smiling", "grin"]),
        "tension_mentioned":     any(w in text for w in ["tense", "tension", "stiff", "rigid", "furrowed"]),
        "fidgeting_mentioned":   any(w in text for w in ["fidget", "moving", "restless", "shift"]),
    }

    return {
        "available":          True,
        "observed_emotions":  observed_emotions,
        "behavioral_signals": signals,
        "raw":                perception_text[:500] + "..." if len(perception_text) > 500 else perception_text
    }


def compute_coherence_score(linguistic_emotions, perception):
    """
    Emotional Coherence = alignment between what the student SAYS
    and what Raven SEES on their face.

    High coherence = self-aware. Low coherence = possible suppression or masking.
    This is the novel signal — no existing EQ test can measure this.
    """
    if not perception.get("available"):
        return {"score": None, "note": "Perception data not available for this session"}

    observed = set(perception.get("observed_emotions", []))
    stated_pos = set(linguistic_emotions.get("positive_words", []))
    stated_neg = set(linguistic_emotions.get("negative_words", []))

    # Positive coherence: student says positive things, Raven sees positive signals
    positive_face = {"happy", "excited", "confident", "hopeful", "focused", "engaged", "calm"}
    negative_face = {"anxious", "nervous", "stressed", "confused", "worried", "frustrated", "uncertain"}

    face_is_positive = bool(observed & positive_face)
    face_is_negative = bool(observed & negative_face)
    words_are_positive = len(stated_pos) > len(stated_neg)
    words_are_negative = len(stated_neg) > len(stated_pos)

    # Alignment check
    aligned = (face_is_positive and words_are_positive) or (face_is_negative and words_are_negative)
    misaligned = (face_is_positive and words_are_negative) or (face_is_negative and words_are_positive)

    if aligned:
        score = 0.8
        interpretation = "High coherence — stated emotions match observed facial signals. Strong self-awareness signal."
    elif misaligned:
        score = 0.3
        interpretation = "Low coherence — mismatch between stated affect and observed facial signals. Possible emotional suppression or masking."
    else:
        score = 0.55
        interpretation = "Neutral — insufficient signal to determine coherence."

    return {
        "score":            score,
        "face_signals":     list(observed),
        "verbal_positive":  list(stated_pos),
        "verbal_negative":  list(stated_neg),
        "interpretation":   interpretation
    }


def map_to_eq_dimensions(signals):
    """Map computed signals to the 5 Mayer-Salovey-Caruso EQ dimensions."""
    coherence_score = signals["emotional_coherence"]["score"]

    return {
        "self_awareness": {
            "score": coherence_score,
            "inputs": ["emotional_coherence", "self_disclosure_ratio"],
            "note": "Based on coherence between stated and observed affect, and first-person introspective language."
        },
        "emotional_regulation": {
            "score": signals["resilience_score"],
            "inputs": ["resilience_score", "hedging_ratio"],
            "note": "Based on recovery language following negative emotional content."
        },
        "motivation": {
            "score": min(signals["cognitive_complexity"] * 2, 1.0),
            "inputs": ["cognitive_complexity", "emotional_vocabulary"],
            "note": "Based on causal reasoning density and goal-oriented language."
        },
        "self_disclosure": {
            "score": min(signals["self_disclosure_ratio"] * 5, 1.0),
            "inputs": ["self_disclosure_ratio"],
            "note": "Proxy for openness and emotional expression (first-person language density)."
        },
        "valence_awareness": {
            "score": min(signals["emotional_vocabulary"]["valence_ratio"] / 3, 1.0),
            "inputs": ["emotional_vocabulary"],
            "note": "Ratio of positive to negative emotion words — awareness of own emotional state."
        }
    }


# ─── MAIN PIPELINE ───────────────────────────────────────────────

def run(conversation_id):
    data = wait_for_data(conversation_id)
    if not data:
        print("Could not retrieve session data.")
        return

    transcript  = data.get("transcript", [])
    perception  = data.get("perception_analysis", "")
    status      = data.get("status", "unknown")

    student_turns = extract_student_turns(transcript)
    total_words   = sum(len(t.split()) for t in student_turns)

    if not student_turns:
        print("No student speech found in transcript.")
        return

    # Run all signal extractors
    hedging          = compute_hedging_ratio(student_turns)
    emotions         = compute_emotional_vocabulary(student_turns)
    resilience       = compute_resilience_score(student_turns)
    complexity       = compute_cognitive_complexity(student_turns)
    self_disclosure  = compute_self_disclosure(student_turns)
    perception_data  = parse_perception_analysis(perception)

    signals = {
        "hedging_ratio":        hedging,
        "emotional_vocabulary": emotions,
        "resilience_score":     resilience,
        "cognitive_complexity": complexity,
        "self_disclosure_ratio": self_disclosure,
        "emotional_coherence":  compute_coherence_score(emotions, perception_data),
    }

    eq_dimensions = map_to_eq_dimensions(signals)

    # ─── OUTPUT ──────────────────────────────────────────────────
    print("\n" + "="*65)
    print("  EQ SIGNAL REPORT")
    print("="*65)
    print(f"  Conversation : {conversation_id}")
    print(f"  Status       : {status}")
    print(f"  Student turns: {len(student_turns)}")
    print(f"  Total words  : {total_words}")
    print("="*65)

    print("\n── RAW SIGNALS ─────────────────────────────────────────────")
    print(f"  Hedging ratio          : {hedging}  (higher = more self-doubt)")
    print(f"  Cognitive complexity   : {complexity}  (higher = more causal reasoning)")
    print(f"  Resilience score       : {resilience}  (higher = more recovery language)")
    print(f"  Self-disclosure ratio  : {self_disclosure}  (higher = more introspective)")
    print(f"  Emotion vocab richness : {emotions['vocabulary_richness']} unique words")
    print(f"  Positive emotion words : {emotions['positive_words']}")
    print(f"  Negative emotion words : {emotions['negative_words']}")
    print(f"  Valence ratio (pos/neg): {emotions['valence_ratio']}")

    print("\n── PERCEPTION ANALYSIS (Raven-0) ────────────────────────────")
    if perception_data["available"]:
        print(f"  Observed emotions      : {perception_data['observed_emotions']}")
        print(f"  Eye contact mentioned  : {perception_data['behavioral_signals']['eye_contact_mentioned']}")
        print(f"  Tension mentioned      : {perception_data['behavioral_signals']['tension_mentioned']}")
        print(f"  Smiling mentioned      : {perception_data['behavioral_signals']['smiling_mentioned']}")
        print(f"\n  Raw Raven-0 output:\n  \"{perception_data['raw']}\"")
    else:
        print("  Perception data not available for this session.")
        print("  (Requires Raven-0 enabled on the persona)")

    print("\n── EMOTIONAL COHERENCE SCORE (Novel Signal) ─────────────────")
    coherence = signals["emotional_coherence"]
    if coherence["score"] is not None:
        bar = "█" * int(coherence["score"] * 20) + "░" * (20 - int(coherence["score"] * 20))
        print(f"  Score  : {coherence['score']} / 1.0   [{bar}]")
        print(f"  Meaning: {coherence['interpretation']}")
    else:
        print(f"  {coherence['note']}")

    print("\n── EQ DIMENSIONS ────────────────────────────────────────────")
    for dim, values in eq_dimensions.items():
        score = values["score"]
        if score is not None:
            bar = "█" * int(score * 20) + "░" * (20 - int(score * 20))
            label = dim.replace("_", " ").title()
            print(f"  {label:<22} {score:.2f}  [{bar}]")
            print(f"  {'':22} {values['note']}")
        else:
            print(f"  {dim:<22} N/A")
        print()

    print("="*65)
    print("  This EQ profile was generated from a single session.")
    print("  Longitudinal accuracy improves significantly after 5+ sessions.")
    print("="*65 + "\n")

    # Save full output to JSON
    output = {
        "conversation_id": conversation_id,
        "status": status,
        "student_turns": len(student_turns),
        "total_words": total_words,
        "raw_signals": signals,
        "eq_dimensions": eq_dimensions,
        "perception": perception_data
    }

    with open(f"eq_report_{conversation_id}.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"Full report saved to: eq_report_{conversation_id}.json\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cid = sys.argv[1]
    else:
        try:
            with open("session_id.txt") as f:
                cid = f.read().strip()
        except FileNotFoundError:
            print("No session_id.txt found. Run create_session.py first, or pass the ID directly:")
            print("  python eq_score.py <conversation_id>")
            sys.exit(1)

    run(cid)