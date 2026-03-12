"""
request.py
----------
Sends the formatted prompt to Groq API (Llama 3) and returns the explanation.
Groq is free, fast, and works without region restrictions.

Member-3 responsibility.
Called by: explainer.py
"""

import time


# -----------------------------
# CONFIGURATION
# -----------------------------

USE_REAL_API = True
GROQ_API_KEY = "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"    # ← Paste your Groq API key here
GROQ_MODEL = "llama-3.3-70b-versatile"               # Free model on Groq


# -----------------------------
# SIMULATED RESPONSES (fallback)
# -----------------------------

SIMULATED_RESPONSES = {
    "Nominal": (
        "Your battery is in excellent condition with stable voltage and a healthy charge level. "
        "Energy is being consumed at a normal rate, so your estimated range is reliable. "
        "No action is needed — continue normal operation and monitor periodically."
    ),
    "Degraded": (
        "Your battery is showing signs of stress, likely due to voltage fluctuations or a moderately high discharge rate. "
        "The estimated range has been reduced as a precaution. "
        "Consider reducing the use of high-power systems like AC or heating to preserve range. "
        "Plan a charging stop sooner than usual."
    ),
    "Critical": (
        "Warning: your battery is in a critical state. "
        "Either the charge is dangerously low or the system has detected severe electrical instability. "
        "Immediately reduce all non-essential loads and find the nearest charging point. "
        "Continuing to drive without action may cause the vehicle to shut down unexpectedly."
    )
}


# -----------------------------
# SIMULATED API CALL
# -----------------------------

def _call_simulated_api(prompt: dict) -> str:
    time.sleep(0.5)
    user_text = prompt.get("user", "")
    if "Critical" in user_text:
        return SIMULATED_RESPONSES["Critical"]
    elif "Degraded" in user_text:
        return SIMULATED_RESPONSES["Degraded"]
    else:
        return SIMULATED_RESPONSES["Nominal"]


# -----------------------------
# REAL GROQ API CALL
# -----------------------------

def _call_groq_api(prompt: dict) -> str:
    from groq import Groq

    client = Groq(api_key=GROQ_API_KEY)

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": prompt["system"]},
            {"role": "user",   "content": prompt["user"]}
        ],
        max_tokens=300,
        temperature=0.7
    )

    return response.choices[0].message.content.strip()


# -----------------------------
# PUBLIC INTERFACE
# -----------------------------

def get_ai_explanation(prompt: dict) -> str:
    try:
        if USE_REAL_API:
            return _call_groq_api(prompt)
        else:
            return _call_simulated_api(prompt)
    except Exception as e:
        print(f"[AI Warning] Groq call failed, falling back to simulation. Error: {e}")
        return _call_simulated_api(prompt)