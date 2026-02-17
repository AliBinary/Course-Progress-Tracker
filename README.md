# Course-Progress-Tracker

📊 **Track your offline course progress easily!**

Course-Progress-Tracker lets you monitor watched videos in downloaded offline courses without any coding. Just set it up once, then run it anywhere to see your progress at a glance.

## Features

- User organizes watched content manually:
    - Fully watched chapters can be moved into the main `(🌸)` folder in the course root.
    - Partially watched chapters can keep watched videos in a `(🌸)` folder inside the chapter.
- Displays interactive progress bars, charts, and badges.
- No coding required after initial setup — super easy to use!

## Installation

1. Clone or download this repository.
2. Make sure you have Python and Streamlit installed:

    ```bash
    pip install streamlit pandas plotly
    ```

3. (Optional) Set up a virtual environment.

## Usage

1. Open `run.bat` in a text editor.
2. Update the path to `app.py` inside the .bat file if needed.
3. Copy the `run.bat` file into any course folder you want to track.
4. Double-click the `run.bat` file — the dashboard will open automatically in your browser.
5. Enter or confirm the watched folder name (default `(🌸)`), and watch your progress.

That's it! No coding, no configuration headaches — just run the script in any course folder where your videos are stored.

## Folder Structure

```
YourCourseFolder/
│
├─ run.bat
├─ app.py
├─ Chapter 1/
│   ├─ video1.mp4
│   ├─ video2.mp4
│   └─ (🌸)/   # watched videos (optional)
├─ Chapter 2/
│   └─ ...
└─ (🌸)/       # fully watched chapters (optional)
```

## License

MIT License
