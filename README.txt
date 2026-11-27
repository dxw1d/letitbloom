ASCII FLOWER STUDIO
==================

WEBSITE
- Open index.html in Chrome or Edge. It is standalone: no separate JavaScript file is required.
- In TEXT SOURCE, choose MY OWN TEXT to type your own phrase or RANDOM PHRASE to generate one. Click GENERATE RANDOM TEXT to roll another phrase.
- Your phrase becomes the ASCII character pattern inside the flower, photo or video. No caption is added below the artwork.
- Upload a PNG, JPG, WEBP or GIF. The photo replaces the flower and is converted into ASCII art.
- Upload an MP4, WebM or another video format supported by your browser. The video replaces the flower and is converted into a moving ASCII animation. Use the video controls to pause or resume it.
- Photos and videos are saved locally in this browser's IndexedDB. Use the saved media gallery to load or delete previous uploads.
- Upload an MP3 and press play. The ASCII artwork pulses and glows in response to the audio using the browser's Web Audio API.
- Change original/tint/duotone colors, primary and highlight colors, background and glow. Presets: Pink, Ice, Fire, Matrix.
- EXPORT PNG / SAVE ASCII FRAME saves the current rendered frame as a normal PNG file.
- Media is processed inside the browser. Files are not sent to a server.

LOCAL STORAGE NOTE
Photos and videos are stored in the browser's IndexedDB, not in a normal Windows folder. They remain available in the same browser profile on this device. Clearing browser site data may delete them. Exported PNG files are saved through the browser's normal download flow.

PYTHON TERMINAL VERSION
- Run: python flower_ascii.py
- Keep flower_frames.bin beside flower_ascii.py.
- Enter a custom ASCII phrase to replace “LET IT BLOOM”. You may also enter a tint color such as #FF55B8; leave it blank to keep original colors.
- The terminal version plays the original flower animation. Media uploads, video conversion, audio reactivity and the saved media gallery are features of the website version.
- Keys: SPACE pause/resume, R restart, Q or ESC quit.
- No third-party packages are required.
