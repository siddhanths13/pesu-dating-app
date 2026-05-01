# PES University Dating App

A full-stack dating web app built with Flask, SQLite, HTML, CSS, and JavaScript.

## Project Structure

```
pesu-dating-app/
├── app.py
├── requirements.txt
├── README.md
└── app/
    ├── static/
    │   ├── css/
    │   │   └── style.css
    │   └── js/
    │       └── swipe.js
    └── templates/
        ├── base.html
        ├── login.html
        ├── register.html
        ├── profile.html
        ├── discover.html
        ├── matches.html
        └── chat.html
```

## Features

- ✅ `@pes.edu` email-only authentication
- ✅ User profiles (name, branch, bio, interests)
- ✅ Swipe system (like/dislike)
- ✅ Match system (mutual likes)
- ✅ Basic one-to-one chat between matched users

## Run Locally

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Set optional secret key:
   ```bash
   export SECRET_KEY="change-me"
   ```
3. Start app:
   ```bash
   python app.py
   ```
4. Open: `http://127.0.0.1:5000`

## Deploy and Share (Render)

You can deploy this app for free and share a public URL:

1. Push this repo to GitHub.
2. Go to Render Dashboard and click **New +** → **Blueprint**.
3. Select your GitHub repo (Render will detect `render.yaml`).
4. Click **Apply** to deploy.
5. After deployment, Render gives a public URL like:
   - `https://pes-dating-app.onrender.com`

Share that URL with others.
