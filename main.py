# This is the test hello world Python app in the helloworld directory on Google Shell
# WE ARE USING THIS FILE AND PROJECT (FOLDER IS A PROJECT) TO TEST GIT

import streamlit as st
import numpy as np
import pandas as pd
import random

st.set_page_config(page_title="Hello World App", page_icon="🌍")

st.title("Hello World! 👋🌍")
st.markdown(
    """
    This is a demo Streamlit app.
    Enter your name below and explore some fun features!
    """
)

name = st.text_input("Enter your name:", placeholder="e.g. Drew")

# --- Celebrations ---
st.subheader("🎉 Celebrations")
col1, col2 = st.columns(2)

with col1:
    if st.button("Send balloons! 🎈"):
        st.balloons()
        st.success(f"Time to celebrate, {name or 'friend'}! 🎉 You deployed a Streamlit app! 🚀")

with col2:
    if st.button("Send snow! ❄️"):
        st.snow()
        st.info(f"Let it snow, {name or 'friend'}! ☃️ You deployed a Streamlit app! 🚀")

st.divider()

# --- Magic 8-Ball ---
st.subheader("🎱 Magic 8-Ball")
question = st.text_input("Ask the Magic 8-Ball a yes/no question:")
responses = [
    "It is certain.", "Without a doubt.", "Yes, definitely!",
    "You may rely on it.", "As I see it, yes.",
    "Reply hazy, try again.", "Ask again later.", "Cannot predict now.",
    "Don't count on it.", "My sources say no.",
    "Outlook not so good.", "Very doubtful."
]
if st.button("🎱 Shake it!"):
    if question:
        st.markdown(f"**🎱 {random.choice(responses)}**")
    else:
        st.warning("Ask a question first!")

st.divider()

# --- Random Joke ---
st.subheader("😂 Random Dad Joke")
jokes = [
    ("Why don't scientists trust atoms?", "Because they make up everything!"),
    ("Why did the scarecrow win an award?", "Because he was outstanding in his field!"),
    ("I told my wife she was drawing her eyebrows too high.", "She looked surprised."),
    ("Why can't you give Elsa a balloon?", "Because she'll let it go."),
    ("What do you call a fake noodle?", "An impasta!"),
]
if st.button("Tell me a joke 😂"):
    setup, punchline = random.choice(jokes)
    st.write(f"**{setup}**")
    st.write(f"_{punchline}_")

st.divider()

# --- Dice Roller ---
st.subheader("🎲 Dice Roller")
num_dice = st.slider("How many dice?", 1, 6, 2)
if st.button("Roll the dice! 🎲"):
    rolls = [random.randint(1, 6) for _ in range(num_dice)]
    dice_faces = {1:"⚀", 2:"⚁", 3:"⚂", 4:"⚃", 5:"⚄", 6:"⚅"}
    st.write(" ".join(dice_faces[r] for r in rolls))
    st.write(f"Total: **{sum(rolls)}**")

st.divider()

# --- Random Chart ---
st.subheader("📊 Random Data Chart")
if st.button("Generate random chart 📊"):
    df = pd.DataFrame(
        np.random.randn(20, 3).cumsum(axis=0),
        columns=["Series A", "Series B", "Series C"]
    )
    st.line_chart(df)
    st.caption("Random walk data — refresh for a new chart!")