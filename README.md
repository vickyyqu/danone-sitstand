# AI-based sit-stand Streamlit web app
This is a streamlit application to count the number of correct and incorrect sit-stands performed by a participant in 30 seconds using the Mediapipe pose model and OpenCV functions.

<hr></hr>

### 1. Setup environment myenv
```
python3 -m venv myenv
```
```
source ./myenv/bin/activate
```
```
pip install -r requirements.txt
```

### 2. Run streamlit app (on macOS)
```
streamlit sitstand.py
```
FYI: preferably run on personal laptop, app runs extremely slow on Danone-issued laptop.

### 3. Sit-stand instructions
<ol>
<li>Set up chair to be about 30-45 degrees slanted from the normal parallel to the computer (half of the body slightly leaning towards the camera)</li>
<li>Back of calf to be fully touching the edge of the chair</li>
<li>Arms crossed in front of chest</li>
<li>Keep back straight and do not lean forward too much</li>
</ol>