from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, join_room, emit
# from transformers import pipeline
# import torch
from groq import Groq
from dotenv import load_dotenv
import os

import json
import random
import uuid
import hashlib
from datetime import datetime
import time

SECRET_KEY = "SUTOCAFE_KIITROAD_2026"

app = Flask(__name__)
load_dotenv()

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    # async_mode="threading"
    async_mode="gevent"
)

print("Loaded API Key:", os.getenv("GROQ_API"))
client = Groq(
    api_key=os.getenv("GROQ_API")
)

def generate_cafe_code():
    today = datetime.now().strftime("%d-%m-%Y")
    raw_string = f"{today}-{SECRET_KEY}"
    hashed = hashlib.sha256(
        raw_string.encode()
    ).hexdigest()
    numeric = int(hashed, 16)
    code = str(numeric)[-6:]
    return code

sessions = {}

def cleanup_sessions():
    expired = []
    for sid, session in sessions.items():
        if time.time() - session["created_at"] > SESSION_EXPIRY:
            expired.append(sid)

    for sid in expired:
        del sessions[sid]

CAFE_CODE = generate_cafe_code()
SESSION_EXPIRY = 3600  # 1 hour

COUPLE_LEVELS = [

    {
        "names": [
            "Butterflies 🦋",
            "Honey Rush 🦋",
            "Soft Chaos 🦋",
            "Pocket Love 🦋"
        ],
        "file": "data/level1.json"
    },

    {
        "names": [
            "Heart Talks ❤️",
            "Unsaid Things ❤️",
            "Heartspace ❤️",
            "Inner Tides ❤️"
        ],
        "file": "data/level2.json"
    },

    {
        "names": [
            "Between Us 🧠",
            "Echo Chamber 🧠",
            "Mirror Mind 🧠",
            "Guess Me Right 🧠"
        ],
        "file": "data/level3.json"
    },

    {
        "names": [
            "After Hours 🌙",
            "Midnight Signals 🌙",
            "Electric Hearts 🌙",
            "Velvet Hours 🌙"
        ],
        "file": "data/level4.json"
    },

    {
        "names": [
            "Cosmic Match ✨",
            "Soul Sync ✨",
            "Star Alignment ✨",
            "Love Frequency ✨"
        ],
        "file": "data/level5.json"
    }
]

FRIEND_LEVELS = [

    {
        "names": [
            "Chaos Starter ⚡",
            "Certified Bakchodi ⚡",
            "Friendly Fire ⚡",
            "Campus Chaos ⚡"
        ],
        "file": "friends_data/level1.json"
    },

    {
        "names": [
            "Bro Code 🍻",
            "Inner Circle 🍻",
            "Bestie Files 🍻",
            "Known Since Forever 🍻"
        ],
        "file": "friends_data/level2.json"
    },

    {
        "names": [
            "Telepathy Test 🧠",
            "Mind Sync 🧠",
            "Guess Mode 🧠",
            "Brainwaves 🧠"
        ],
        "file": "friends_data/level3.json"
    },

    {
        "names": [
            "Expose Chamber 🎭",
            "Leak Department 🎭",
            "Caught In 4K 🎭",
            "Truth Grenade 🎭"
        ],
        "file": "friends_data/level4.json"
    },

    {
        "names": [
            "Vibe Check ✨",
            "Friendship Meter ✨",
            "Chaos Compatibility ✨",
            "Energy Match ✨"
        ],
        "file": "friends_data/level5.json"
    }
]

# RESULTS = [
#     (20, "Still Strangers 😭"),
#     (40, "Situationship Survivors 💀"),
#     (60, "Cute Chaos ❤️"),
#     (80, "Perfectly Imperfect ✨"),
#     (100, "Soulmate Energy 🥹❤️")
# ]

COUPLE_RESULTS = [

    {
        "limit": 20,
        "titles": [
            "Slow Burn Energy ☕",
            "Getting To Know You 🌙",
            "Early Chapter Vibes ✨",
            "Soft Start Connection 💫"
        ]
    },

    {
        "limit": 40,
        "titles": [
            "Mixed Signal Cuties 📡",
            "Cute Confusion Club 🌸",
            "Chaotic Sweethearts 🎧",
            "Almost Reading Minds 🫶"
        ]
    },

    {
        "limit": 60,
        "titles": [
            "Comfort Zone Duo ❤️",
            "Certified Cute Chaos ⚡",
            "Too Real Together 🌹",
            "Emotionally Synced Sometimes 🌙"
        ]
    },

    {
        "limit": 80,
        "titles": [
            "Perfectly Imperfect ✨",
            "Soft Launch Material 📸",
            "Dangerously Comfortable 💞",
            "Golden Retriever Energy 🧸"
        ]
    },

    {
        "limit": 100,
        "titles": [
            "Cosmic Couple Sync 🌌",
            "Main Character Romance 🎬",
            "Soulmate Vibes 🥹",
            "Straight Out Of A Reel 🎞️"
        ]
    }
]

FRIEND_RESULTS = [

    {
        "limit": 20,
        "titles": [
            "New Duo Loading ☕",
            "Friendly Vibes Only ✨",
            "Work Bestie Potential 💻",
            "Still Unlocking Lore 🎮"
        ]
    },

    {
        "limit": 40,
        "titles": [
            "Meme Exchange Partners 📱",
            "Chaotic But Chill ⚡",
            "Lowkey Fun Duo 🎧",
            "Unexpected Combo 🌮"
        ]
    },

    {
        "limit": 60,
        "titles": [
            "Certified Bakchodi Energy 🍻",
            "Campus Chaos Duo 🎭",
            "Same Vibe Different Brain 🧠",
            "Tea Spill Partners ☕"
        ]
    },

    {
        "limit": 80,
        "titles": [
            "Too Comfortable Together 🛋️",
            "Peak Bestie Behaviour 🚀",
            "Telepathic Friendship ✨",
            "Same Braincell Energy ⚡"
        ]
    },

    {
        "limit": 100,
        "titles": [
            "Legendary Duo Status 👑",
            "Built Different Friendship 🌟",
            "Chaos Coordinators 🎬",
            "Friendship Cinematic Universe 🎥"
        ]
    }
]


SYSTEM_PROMPT = """
You are an expert relationship commentator for a modern couple cafe game.

Your job is to generate:
- ONLY 1 short unique commentary line about the couple dynamic
- Based on their answers, guesses, matches, mismatches, habits, and emotional patterns
- Sound like a funny observant friend who knows relationships really well
- Use natural Indian dating-style Hinglish
- Tone should feel:
    - playful
    - emotionally layered
    - slightly teasing
    - soft sarcastic
    - cute
    - romantic
    - highly relatable
- The line should feel screenshot-worthy and Instagram-reel vibe worthy
- Make the response feel human written, not AI generated
- Response should feel like:
    "this is sooo us"

IMPORTANT:
- Partner A answer = what they actually chose
- Partner B guess = what they thought their partner would choose
- Use both matches and mismatches intelligently
- Mismatches should feel cute/funny, not negative
- Observe their dynamic, not just compatibility
- Subtly infer:
    - who overthinks
    - who knows whom better
    - teasing energy
    - emotional comfort
    - drama
    - attachment
    - chaos
    - effort
    - romance
    - understanding

STRICT RULES:
- Keep response under 20 words
- No emojis
- No quotes
- No cringe poetry
- No formal tone
- No generic lines like:
    - "perfect match"
    - "great bonding"
    - "made for each other"
    - "cute couple"
    - "soulmates"
- Avoid repeating or directly mentioning question text
- Do not explain answers
- Avoid sounding motivational
- Avoid AI sounding phrases

The response should feel like:
- a witty relationship observation
- a reel caption
- a playful emotional truth
- something people instantly want to screenshot and share

GOOD EXAMPLES:
- "Tum dono ek dusre ko roast bhi perfectly karte ho aur handle bhi."
- "Arguments frequent hain, par attachment usse bhi zyada dangerous hai."
- "Ek overthink karta hai, dusra ussi mein entertainment dhoond leta hai."
- "Mismatch kaafi hain, but comfort dangerously strong hai."
- "Tum dono ka chaos bhi surprisingly coordinated lagta hai."

BAD EXAMPLES:
- "You both are soulmates."
- "Perfect compatibility."
- "Great bonding between you two."
- "You are made for each other."
"""

FRIEND_SYSTEM_PROMPT = """
You are an expert friendship commentator for a modern Indian friendship game.

Your job is to generate:
- ONLY 1 short unique commentary line about the friendship dynamic
- Based on their answers, guesses, matches, mismatches, habits, roasting energy, and chaos
- Sound like a savage but lovable mutual friend
- Use natural Gen-Z Indian Hinglish
- Tone should feel:
    - funny
    - chaotic
    - teasing
    - witty
    - meme-worthy
    - highly relatable
    - screenshot-worthy
    - playful
    - slightly savage
    - emotionally real underneath the comedy

IMPORTANT:
- Friend A answer = what they actually chose
- Friend B guess = what they thought their friend would choose
- Use both matches and mismatches intelligently
- Mismatches should feel hilarious or exposing
- Observe their friendship dynamic deeply
- Subtly infer:
    - who roasts more
    - who gets exposed easily
    - who knows whom better
    - fake fighting energy
    - emotional closeness hidden behind bakchodi
    - chaotic duo energy
    - inside-joke friendship
    - extrovert vs introvert vibe
    - clown friend energy
    - who carries the friendship

STRICT RULES:
- Keep response under 18 words
- No emojis
- No quotes
- No cringe motivation
- No formal tone
- No poetic lines
- Avoid generic friendship lines like:
    - "best friends forever"
    - "great friendship"
    - "true friends"
    - "strong bond"
- Avoid directly mentioning question text
- Avoid AI sounding phrases
- Avoid sounding wholesome-only
- Make it feel naturally funny

The response should feel like:
- a reel caption
- a funny observation
- an inside joke
- a chaotic friendship truth
- something instantly screenshot-worthy

GOOD EXAMPLES:
- "Tum dono ka friendship toxic nahi hai, bas publicly concerning lagta hai."
- "Ek bakchodi karta hai, dusra usko professionally encourage karta hai."
- "Tum dono ek dusre ki beizzati mein emotional support dhoond lete ho."
- "Arguments fake hote hain, but exposing sessions dangerously real."
- "Ye friendship kam, unlimited content creation zyada lag raha hai."
- "Ek sensible banne ki koshish karta hai, dusra uska career kharab kar deta hai."
- "Tum dono ko saath dekhke lagta hai decision making kabhi hui hi nahi."

BAD EXAMPLES:
- "You both are best friends."
- "Strong friendship bond."
- "Amazing friendship compatibility."
- "You both understand each other well."
"""

def load_questions(file_path):
    print(f"Loading file :: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:

        data = json.load(f)

    questions = list(data.values())

    return random.sample(questions, 5)

def generate_relationship_commentary(
    session,
    category,
    system_prompt
):

    all_questions = []

    for level in session["questions"]:

        for q in level["questions"]:

            all_questions.append(q)

    user_prompt = f"""
    Category: {category}

    """

    for i in range(len(session["answers1"])):

        question = all_questions[i]

        actual = int(session["answers1"][i])

        guessed = int(session["answers2"][i])

        match = (
            "Yes"
            if actual == guessed
            else "No"
        )

        user_prompt += f"""
        Q{i+1}: {question["question"]}
        
        Partner A: {question["options"][actual]}
        Partner B Guess: {question["options"][guessed]}
        Match: {match}
        
        """

    completion = client.chat.completions.create(

        model="llama-3.3-70b-versatile",

        messages=[

            {
                "role":"system",
                "content": system_prompt
            },

            {
                "role":"user",
                "content": user_prompt
            }
        ],

        temperature=0.9,
        max_tokens=100
    )

    generated = completion.choices[0].message.content
    print(f"LLM RESPONSE :: {generated}")
    return generated.strip()


@app.route("/")
def home():

    return render_template("index.html")

@app.route("/create-session", methods=["POST"])
def create_session():
    cleanup_sessions()
    data = request.json
    
    entered_code = data.get("cafe_code")
    if entered_code != CAFE_CODE:
        return jsonify({
            "error": "Invalid Cafe Code"
        }), 403
        
    game_type = data["game_type"] # added this line to get the game type from the request
    session_id = str(uuid.uuid4())[:6]

    selected_questions = []

    levels_to_use = (
        COUPLE_LEVELS
        if game_type == "couple"
        else FRIEND_LEVELS
    )
    
    for level in levels_to_use: # Changed LEVELS to levels_to_use to select based on game type
        selected_questions.append({
            "level": random.choice(level["names"]),
            "questions": load_questions(level["file"]),
            "theme": game_type
        })

    sessions[session_id] = {

        "created_at": time.time(),
        
        "partner1": data["partner1"],
        "partner2": data["partner2"],
        
        "game_type": game_type,

        "questions": selected_questions,

        "current_answers": {},

        "answers1": [],
        "answers2": [],

        "score": 0
    }

    return jsonify({
        "session_id": session_id,
        "link": f"{request.host_url}game/{session_id}",
        "game_type": game_type # added game type
    })

@app.route("/game/<session_id>")
def game(session_id):
    
    if session_id not in sessions:
        return "Session Expired"

    session = sessions[session_id]

    if time.time() - session["created_at"] > SESSION_EXPIRY:
        del sessions[session_id]
        return "This game session has expired."
    
    return render_template(
        "game.html",
        session_id=session_id
    )

@app.route("/get-questions/<session_id>")
def get_questions(session_id):

    if session_id not in sessions:
        return jsonify({"error":"Session expired"}), 403

    session = sessions[session_id]

    if time.time() - session["created_at"] > SESSION_EXPIRY:
        del sessions[session_id]
        return jsonify({"error":"Session expired"}), 403
    
    return jsonify({
        "questions": sessions[session_id]["questions"],
        "theme": sessions[session_id]["game_type"]
    })

@app.route("/submit-answer/<session_id>", methods=["POST"])
def submit_answer(session_id):
    if session_id not in sessions:
        return jsonify({"error":"Session expired"}), 403

    session = sessions[session_id]

    if time.time() - session["created_at"] > SESSION_EXPIRY:
        del sessions[session_id]
        return jsonify({"error":"Session expired"}), 403

    score = 0

    for a1, a2 in zip(
        session["answers1"],
        session["answers2"]
    ):

        if a1 == a2:
            score += 4

    session["score"] = score

    result_name = ""

    result_pool = (
        FRIEND_RESULTS
        if session["game_type"] == "friends"
        else COUPLE_RESULTS
    )

    for result in result_pool:

        if score <= result["limit"]:

            result_name = random.choice(
                result["titles"]
            )

            break

    # return jsonify({
    #     "score": score,
    #     "category": result_name
    # })
    
    # commentary = generate_relationship_commentary(
    #     session,
    #     result_name
    # )
    
    system_prompt = (
        FRIEND_SYSTEM_PROMPT
        if session["game_type"] == "friends"
        else SYSTEM_PROMPT
    )

    commentary = generate_relationship_commentary(
        session,
        result_name,
        system_prompt
    )
    
    print(f"COMMENTARY :: {commentary}")

    return jsonify({
        "score": score,
        "category": result_name,
        "commentary": commentary
    })

# PARTNER RESPONSE API
# @app.route("/get-session-results/<session_id>")
# def get_session_results(session_id):

#     session = sessions[session_id]

#     all_questions = []

#     for level in session["questions"]:

#         for q in level["questions"]:

#             all_questions.append(q)

#     results = []

#     for i in range(len(session["answers1"])):

#         question = all_questions[i]

#         actual = int(session["answers1"][i])

#         guessed = int(session["answers2"][i])

#         results.append({

#             "question": question["question"],

#             "options": question["options"],

#             "partner_answer":
#                 question["options"][actual],

#             "guess_answer":
#                 question["options"][guessed],

#             "matched":
#                 actual == guessed
#         })

#     return jsonify(results)

@app.route("/get-session-results/<session_id>")
def get_session_results(session_id):

    session = sessions[session_id]

    player = request.args.get("player")

    all_questions = []

    for level in session["questions"]:

        for q in level["questions"]:

            all_questions.append(q)

    results = []

    for i in range(len(session["answers1"])):

        question = all_questions[i]

        p1_answer = int(session["answers1"][i])

        p2_guess = int(session["answers2"][i])

        # WHAT EACH PLAYER SHOULD SEE
        if player == "p1":

            primary_label = (
                "Friend Answer"
                if session["game_type"] == "friends"
                else "Partner Answer"
            )

            primary_answer = question["options"][p1_answer]

            secondary_label = "Your Guess"

            secondary_answer = question["options"][p2_guess]

        else:

            primary_label = "Your Guess"

            primary_answer = question["options"][p2_guess]

            secondary_label = (
                "Friend Answer"
                if session["game_type"] == "friends"
                else "Partner Answer"
            )

            secondary_answer = question["options"][p1_answer]

        results.append({

            "question": question["question"],

            "primary_label": primary_label,

            "primary_answer": primary_answer,

            "secondary_label": secondary_label,

            "secondary_answer": secondary_answer,

            "matched":
                p1_answer == p2_guess
        })

    return jsonify(results)

# SOCKET → JOIN ROOM
@socketio.on("join_room")
def handle_join(data):

    room = data["session_id"]

    join_room(room)

    # emit(
    #     "user_joined",
    #     {"message": "Partner joined ❤️"},
    #     room=room
    # )
    
    game_type = sessions[room]["game_type"]

    join_message = (
        "Friend joined 🤝"
        if game_type == "friends"
        else "Partner joined ❤️"
    )

    emit(
        "user_joined",
        {"message": join_message},
        room=room
    )

# SOCKET → LIVE ANSWERS
# @socketio.on("submit_live_answer")
# def handle_live_answer(data):

#     session_id = data["session_id"]

#     player = data["player"]

#     answer = data["answer"]

#     question_index = data["question_index"]

#     session = sessions[session_id]

#     if question_index not in session["current_answers"]:

#         session["current_answers"][question_index] = {}

#     session["current_answers"][question_index][player] = answer

#     answers = session["current_answers"][question_index]

#     if "p1" in answers and "p2" in answers:

#         if len(session["answers1"]) <= len(session["answers2"]):

#             session["answers1"].append(
#                 answers["p1"]
#             )

#             session["answers2"].append(
#                 answers["p2"]
#             )

#         emit(
#             "both_answered",
#             room=session_id
#         )

#     else:

#         # emit(
#         #     "waiting",
#         #     {"message":"Waiting for partner ❤️"},
#         #     room=request.sid
#         # )
        
#         game_type = session["game_type"]

#         waiting_message = (
#             "Waiting for your friend ⚡"
#             if game_type == "friends"
#             else "Waiting for your partner ❤️"
#         )

#         emit(
#             "waiting",
#             {"message": waiting_message},
#             room=request.sid
#         )


@socketio.on("submit_live_answer")
def handle_live_answer(data):

    session_id = data["session_id"]

    player = data["player"]

    answer = data["answer"]

    question_index = data["question_index"]

    session = sessions[session_id]

    if question_index not in session["current_answers"]:

        session["current_answers"][question_index] = {}

    session["current_answers"][question_index][player] = answer

    answers = session["current_answers"][question_index]

    # BOTH ANSWERED
    if "p1" in answers and "p2" in answers:

        # SAVE SAFELY BY QUESTION INDEX
        while len(session["answers1"]) <= question_index:
            session["answers1"].append(None)

        while len(session["answers2"]) <= question_index:
            session["answers2"].append(None)

        session["answers1"][question_index] = answers["p1"]

        session["answers2"][question_index] = answers["p2"]

        emit(
            "both_answered",
            room=session_id
        )
        del session["current_answers"][question_index]

    else:

        game_type = session["game_type"]

        waiting_message = (
            "Waiting for your friend ⚡"
            if game_type == "friends"
            else "Waiting for your partner ❤️"
        )

        emit(
            "waiting",
            {"message": waiting_message},
            room=request.sid
        )

# if __name__ == "__main__":

#     socketio.run(
#         app,
#         debug=True
#     )

if __name__ == "__main__":

    socketio.run(
        app,
        host="0.0.0.0",
        port=5000
    )