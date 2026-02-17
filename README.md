# Blue Dart AWB Status Web App (Flask)

Ye project ek simple Flask web app hai jo Blue Dart AWB number ka status fetch karne ki koshish karta hai.

## Features

- AWB number input form
- Blue Dart tracking page se status parse karne ka attempt
- Recent timeline events extract karne ka attempt
- Agar live fetch fail ho jaye to direct tracking link provide karta hai

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python app.py
```

App: `http://127.0.0.1:5000`

## Test

```bash
python -m pytest -q
```

> Note: Blue Dart website kabhi-kabhi bot protection ya HTML format change ki wajah se parser response fail kar sakta hai.
