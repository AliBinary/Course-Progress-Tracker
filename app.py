import sys
import streamlit as st
import os
import re
import pandas as pd
import plotly.express as px
import random

# ──────────────────────────────────────────────
# Helper: Natural sort key function
# ──────────────────────────────────────────────


def natural_sort_key(s):
    """Split string into numbers and non-numbers for human-friendly sorting."""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]


# ──────────────────────────────────────────────
# Page configuration
# ──────────────────────────────────────────────
VIDEO_EXT = ('.mp4', '.mkv', '.webm', '.avi')


# Use argv to pass root path from .bat
default_path = sys.argv[-1] if len(sys.argv) > 1 and os.path.isdir(
    sys.argv[-1]) else r"F:\Learning"
course_root = st.text_input(
    "🗂️ Path to main course folder",
    value=default_path,
    help="The folder containing your course chapters."
)


if not course_root.strip():
    st.info("Please enter a valid course folder path.")
    st.stop()

if not os.path.exists(course_root):
    st.error("Folder not found. Please check the path.")
    st.stop()

# ──────────────────────────────────────────────
# Validate watched folder name
# ──────────────────────────────────────────────


def validate_folder_name(name: str, default="(🌸)") -> str:
    """Ensure folder name does not contain invalid filesystem characters."""
    # Invalid characters for Windows: \ / : * ? " < > |
    # Linux is more permissive, but we'll remove / and null char
    invalid_chars = r'<>:"/\|?*'  # common invalid chars
    if any(c in invalid_chars for c in name) or not name.strip():
        st.warning(
            f"Watched folder name `{name}` contains invalid characters. Using default `{default}` instead."
        )
        return default
    return name.strip()

# ──────────────────────────────────────────────
# Auto-detect watched folder (optional)
# ──────────────────────────────────────────────


def detect_watched_folder(root_path):
    """Auto-detect the 'watched' folder in root based on pattern (X)"""
    pattern = re.compile(r'^\([^\)]+\)$')  # matches (🌸), (w), (💪), etc.

    for entry in os.scandir(root_path):
        if entry.is_dir() and not entry.name.startswith('.'):
            if pattern.match(entry.name.strip()):
                return entry.name.strip()

    # fallback if nothing found
    return "(🌸)"


# Try to detect watched folder
auto_watched = detect_watched_folder(default_path)

watched_folder_name = st.text_input(
    "Watched folder name (for marking completed videos)",
    value=auto_watched,
    help="This folder inside each chapter marks watched videos."
)

# Validate input
watched_folder_name = validate_folder_name(watched_folder_name)


# ──────────────────────────────────────────────
# Scan course structure: normal + fully-watched chapters
# ──────────────────────────────────────────────


def scan_course(root_path: str, video_ext, watched_subfolder):
    chapters = {}
    total_videos = 0
    watched_videos = 0
    total_size_gb = 0.0
    watched_size_gb = 0.0

    def list_videos(folder):
        files = []
        for f in os.scandir(folder):
            if f.is_file() and f.name.lower().endswith(video_ext):
                files.append(f)
        return files

    # Normal chapters
    for entry in os.scandir(root_path):
        if not entry.is_dir() or entry.name.strip() == watched_subfolder:
            continue

        chap_name = entry.name.strip()
        chap_path = entry.path

        all_files = list_videos(chap_path)
        watched_sub = os.path.join(chap_path, watched_subfolder)
        if os.path.isdir(watched_sub):
            all_files += list_videos(watched_sub)

        all_files = list({f.path: f for f in all_files}.values())

        chapter_total = 0
        chapter_watched = 0
        chapter_size = 0.0
        chapter_watched_size = 0.0

        for f in all_files:
            size = f.stat().st_size / (1024 ** 3)
            chapter_total += 1
            chapter_size += size
            if os.path.basename(os.path.dirname(f.path)) == watched_subfolder:
                chapter_watched += 1
                chapter_watched_size += size

        percent = (chapter_watched / chapter_total *
                   100) if chapter_total else 0.0

        chapters[chap_name] = {
            "total": chapter_total,
            "watched": chapter_watched,
            "percent": round(percent, 1),
            "size_gb": round(chapter_size, 3),
            "watched_size_gb": round(chapter_watched_size, 3),
        }

        total_videos += chapter_total
        watched_videos += chapter_watched
        total_size_gb += chapter_size
        watched_size_gb += chapter_watched_size

    # Fully watched chapters in root
    watched_root = os.path.join(root_path, watched_subfolder)
    if os.path.isdir(watched_root):
        for entry in os.scandir(watched_root):
            if not entry.is_dir():
                continue

            chap_name = entry.name.strip()
            chap_path = entry.path

            if chap_name in chapters:
                prev = chapters[chap_name]
                total_videos -= prev["total"]
                watched_videos -= prev["watched"]
                total_size_gb -= prev["size_gb"]
                watched_size_gb -= prev.get("watched_size_gb", 0)

            all_files = list_videos(chap_path)
            chapter_total = len(all_files)
            chapter_size = sum(f.stat().st_size / (1024 ** 3)
                               for f in all_files)

            chapters[chap_name] = {
                "total": chapter_total,
                "watched": chapter_total,
                "percent": 100.0,
                "size_gb": round(chapter_size, 3),
                "watched_size_gb": round(chapter_size, 3),
            }

            total_videos += chapter_total
            watched_videos += chapter_total
            total_size_gb += chapter_size
            watched_size_gb += chapter_size

    return total_videos, watched_videos, chapters, round(total_size_gb, 2), round(watched_size_gb, 2)


# ──────────────────────────────────────────────
total, watched, chapters, total_size, watched_size = scan_course(
    course_root, VIDEO_EXT, watched_folder_name
)
progress_pct = (watched / total * 100) if total > 0 else 0

# ──────────────────────────────────────────────
# Page header with dynamic watched folder
# ──────────────────────────────────────────────
st.set_page_config(
    page_title=f"My Course Progress {watched_folder_name}", layout="wide")
st.title("📊 Course Progress Dashboard 😎")
st.markdown(
    f"**Tracking your watched system `{watched_folder_name}`** – full chapters moved to root `{watched_folder_name}` or partial watched inside chapter subfolder `{watched_folder_name}`"
)

# ──────────────────────────────────────────────
# Dashboard metrics
# ──────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="📦 Watched Size",
              value=f"{watched_size:.2f} / {total_size:.2f} GB")
with col2:
    st.metric(label="🎬 Videos Watched",
              value=f"{watched:,} / {total:,} videos")
with col3:
    st.metric(label="🎯 Overall Progress", value=f"{progress_pct:.1f} %")

# ──────────────────────────────────────────────
# Overall progress bar
# ──────────────────────────────────────────────
st.markdown("### Overall Progress")
progress_html = f"""
<div style="position: relative; background: #e8ecef; border-radius: 999px; height: 50px; overflow: hidden; box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);">
    <div style="
        position: absolute;
        top: 0; left: 0; bottom: 0;
        width: {progress_pct}%;
        background: linear-gradient(90deg, #6366f1, #a855f7);
        transition: width 1s ease-out;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
        font-size: 1.3rem;
    ">
        {progress_pct:.1f}%
    </div>
</div>
"""
st.markdown(progress_html, unsafe_allow_html=True)

# ──────────────────────────────────────────────
# Charts: Bar + Pie
# ──────────────────────────────────────────────
col_left, col_right = st.columns(2)
with col_left:
    if chapters:
        df_bar = pd.DataFrame.from_dict(chapters, orient="index")
        df_bar = df_bar.sort_index(key=lambda x: x.map(natural_sort_key))
        df_bar['Chapter'] = df_bar.index
        fig_bar = px.bar(
            df_bar, y="Chapter", x="percent", orientation="h",
            title="Progress by Chapter",
            text=df_bar["percent"].apply(lambda x: f"{x}%"),
            color="percent", color_continuous_scale="RdYlGn", range_color=[0, 100]
        )
        fig_bar.update_layout(xaxis_title="Progress (%)", yaxis_title="", height=max(
            400, len(df_bar)*35), xaxis_range=[0, 100])
        fig_bar.update_traces(textposition='auto')
        st.plotly_chart(fig_bar, use_container_width=True)

with col_right:
    fig_pie = px.pie(
        values=[watched, total - watched],
        names=["Watched 🌸", "Remaining ⏳"],
        title="Watched vs Remaining",
        hole=0.4,
        color_discrete_sequence=["#e0e0e0", "#00c853"]
    )
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_pie, use_container_width=True)

# ──────────────────────────────────────────────
# Chapter Size vs Progress Vertical Bar Chart
# ──────────────────────────────────────────────
if chapters:
    df_size = pd.DataFrame.from_dict(chapters, orient="index")
    df_size = df_size.sort_index(key=lambda x: x.map(natural_sort_key))
    df_size['Chapter'] = df_size.index
    df_size['Watched Size'] = df_size['watched_size_gb']
    df_size['Remaining Size'] = df_size['size_gb'] - df_size['watched_size_gb']

    fig_chapter = px.bar(
        df_size, x='Chapter',
        y=['Watched Size', 'Remaining Size'],
        title="Chapter Size vs Watched Progress",
        color_discrete_map={'Watched Size': '#6366f1',
                            'Remaining Size': '#e5e7eb'},
        text_auto='.1f'
    )
    fig_chapter.update_layout(
        yaxis_title="Size (GB)", xaxis_title="Chapter", barmode='stack', height=500)
    st.plotly_chart(fig_chapter, use_container_width=True)

# ──────────────────────────────────────────────
# Chapter Breakdown Table with styling
# ──────────────────────────────────────────────
if chapters:
    df = pd.DataFrame.from_dict(chapters, orient="index")
    df = df.sort_index(key=lambda x: x.map(natural_sort_key))
    df = df.rename(columns={"total": "Total", "watched": "Watched",
                   "percent": "Progress %", "size_gb": "Size (GB)"})

    def style_progress(val):
        if pd.isna(val):
            return ''
        val = float(val)
        if val >= 90:
            bg, text = 'linear-gradient(90deg, #a7f3d0, #6ee7b7)', '#065f46'
        elif val >= 75:
            bg, text = 'linear-gradient(90deg, #bbf7d0, #86efac)', '#065f46'
        elif val >= 50:
            bg, text = 'linear-gradient(90deg, #fef08a, #fde047)', '#854d0e'
        elif val >= 30:
            bg, text = 'linear-gradient(90deg, #fecaca, #fca5a5)', '#991b1b'
        else:
            bg, text = 'linear-gradient(90deg, #fecdd3, #fda4af)', '#9f1239'
        return f'background: {bg}; color: {text}; font-weight: 600; border-radius: 4px;'

    styled_df = df.style.format(precision=1).map(style_progress, subset=[
        'Progress %']).format("{:.2f}", subset=['Size (GB)']).hide(axis="index")
    st.subheader("Chapter Breakdown")
    st.dataframe(styled_df, use_container_width=True)

# ──────────────────────────────────────────────
# Motivational message with button
# ──────────────────────────────────────────────
motivations = [
    "You're absolutely crushing it! Keep the fire burning 🔥",
    f"Level {int(progress_pct // 20)} unlocked! Your XP is skyrocketing 🎉",
    "Every 🌸 you add is a step closer to true mastery 💪",
    "Watch. Learn. Code. Conquer. Repeat. You're unstoppable 🌟",
    "You're not just watching — you're building an empire of skills 🏗️",
    "Keep stacking those 🌸 — small efforts compound into greatness 📈",
    "Tiny steps every day = giant leaps tomorrow 🚀",
    "Another 🌸 completed! Your consistency is shining 💎",
    "Consistency > intensity. Keep showing up 💯",
    "Learning never stops — each 🌱 grows into a forest of knowledge 🌱",
    "You're coding your way to greatness — one video at a time 💻",
    "Every watched 🌸 is a win. Celebrate your growth 🎊",
    "Focus, watch, repeat — your future self will thank you 🙏",
    "The more you learn, the more powerful you become 🧠💰",
    "Level up unlocked! Your skill tree expands ✨",
    "Persistence beats resistance. Keep pushing forward 🔧",
    "Stacked 🌸s today, mastery tomorrow 🏆",
    "Don't just watch, absorb and implement! 🌟",
    "Your dedication is inspiring — keep going, Ali! 💜",
    "Every video is a seed — soon you'll have a forest of skills 🌳",
    "Mastery is built one 🌸 at a time — keep planting 🌱",
    "Learning is a marathon, not a sprint. Pace yourself 🏃‍♂️",
    "You're turning knowledge into power — keep going ⚡",
    "Another chapter conquered! You're unstoppable 💥",
    "Remember: code, learn, repeat, succeed 🔄",
    "Your skill tree is growing! More 🌸 unlocked 🌟",
    "Stay curious, stay hungry, stay awesome 😎",
    "Every watched 🌸 is progress in disguise 👀",
    "You're investing in yourself — best ROI ever 💰",
    "Keep your eyes on the prize, one video at a time 🏅",
    "Knowledge is power, but action multiplies it 💡",
    "Code. Debug. Learn. Repeat. Your future is bright 🔮",
    "The forest of 🌸s is growing — you're the gardener 🌿",
    "Each 🌸 you watch is a trophy of effort 🏆",
    "You're leveling up faster than you think ⏩",
    "Your brain is a muscle — and you're lifting heavy today 🧠💪",
    "Step by step, video by video — you're creating magic ✨",
    "Every minute counts. Keep stacking those 🌸 ⏱️",
    "The journey is long, but the progress is undeniable 🌄",
    "One more 🌸 today — tomorrow you'll thank yourself 🙌",
    "You're not just watching — you're building lifelong skills 💼",
    "Your consistency is legendary — keep it going 🏹",
    "Every chapter mastered is a story of perseverance 📖",
    "Watch, learn, implement, repeat — the skill loop 🔁",
    "You're shaping your future one 🌸 at a time 🏗️",
    "Small wins today = massive victories tomorrow 🏔️",
    "Keep your momentum. The compounding effect is strong 💥",
    "Your progress bar is not lying — you're rocking it 📊",
    "Another day, another 🌸 — progress never sleeps 😴",
    "Your dedication is your superpower 🦸‍♂️",
    "Learning + Action = Success Formula ✅",
    "Every 🌸 watched = step closer to mastery 🥇",
    "Celebrate every 🌸 — even tiny wins matter 🌟",
    "Each chapter completed is a medal of effort 🏅",
    "Your curiosity is your compass — keep exploring 🧭",
    "Every line of code you watch is shaping your future 🖥️",
    "You're the architect of your skill universe 🏗️✨",
    "Progress today = freedom tomorrow 🌌",
    "Each 🌸 is a spark lighting the path to mastery 🔥",
    "Keep learning, keep growing, keep glowing 🌱💫",
]

if 'quote' not in st.session_state:
    st.session_state.quote = random.choice(motivations)


def change_quote():
    st.session_state.quote = random.choice(motivations)


quote = st.session_state.quote
st.markdown(f"""
<div style="
    background: linear-gradient(135deg, #1e293b 0%, #111827 100%);
    border-radius: 20px; padding: 40px 32px; margin: 32px auto;
    max-width: 1000px; box-shadow: 0 20px 40px rgba(0,0,0,0.6);
    text-align: center; color: #e2e8f0; border: 1px solid rgba(139, 92, 246, 0.2);">
    <div style="font-size: 1.9rem; font-weight: 700; line-height: 1.35; margin-bottom: 20px; letter-spacing: -0.5px;">
        “ {quote} ”
    </div>
    <div style="font-size: 1.15rem; opacity: 0.9; font-weight: 500;">
        Stay consistent, Ali — greatness is built one 🌸 at a time ✨
    </div>
</div>
""", unsafe_allow_html=True)

cols = st.columns([4, 1, 4])
with cols[1]:
    st.button("🔄 Change Quote", on_click=change_quote,
              help="Click to see a new motivational quote")

# ──────────────────────────────────────────────
# Badges
# ──────────────────────────────────────────────
st.markdown("### Unlocked Badges 🌟")
badges = [
    {"name": "Starter", "emoji": "🌱",
        "gradient": "linear-gradient(135deg, #6ee7b7, #34d399)"},
    {"name": "Growing", "emoji": "🌿",
        "gradient": "linear-gradient(135deg, #6ee7b7, #10b981)"},
    {"name": "Solid", "emoji": "🌳",
        "gradient": "linear-gradient(135deg, #fde047, #f59e0b)"},
    {"name": "Master", "emoji": "🌸",
        "gradient": "linear-gradient(135deg, #a78bfa, #7c3aed)"},
    {"name": "Legend", "emoji": "🔥",
        "gradient": "linear-gradient(135deg, #ef4444, #b91c1c)"},
]

unlocked_count = min(int(progress_pct//20), len(badges)-1)
cols = st.columns(5)
for i, badge in enumerate(badges):
    with cols[i % 5]:
        is_unlocked = i <= unlocked_count
        card_style = (
            f"background: {badge['gradient'] if is_unlocked else '#4b5563'}; "
            f"border-radius: 16px; padding: 16px 12px; margin: 8px 0; text-align: center; "
            f"box-shadow: {'0 10px 25px rgba(0,0,0,0.4)' if is_unlocked else '0 4px 12px rgba(0,0,0,0.3)'}; "
            f"border: 2px solid {'rgba(255,255,255,0.3)' if is_unlocked else 'transparent'}; "
            f"transition: transform 0.3s ease, box-shadow 0.3s ease;"
        )
        if is_unlocked:
            card_style += "cursor: pointer;"
        st.markdown(f"""
        <div style="{card_style}">
            <div style="font-size: 3.2rem; line-height: 1; margin-bottom: 8px; filter: {'drop-shadow(0 0 10px rgba(255,255,255,0.7))' if is_unlocked else 'grayscale(80%)'};">
                {badge['emoji']}
            </div>
            <div style="font-weight: bold; font-size: 1.1rem; color: {'white' if is_unlocked else '#9ca3af'};">
                {badge['name']}
            </div>
            <div style="font-size: 0.85rem; margin-top: 4px; color: {'#e5e7eb' if is_unlocked else '#6b7280'};">
                {'Unlocked!' if is_unlocked else 'Locked'}
            </div>
        </div>
        """, unsafe_allow_html=True)
