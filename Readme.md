# InterviewBot

A Python-based interview assistant powered by Streamlit. This tool helps simulate interview scenarios and provides feedback.

## Features

- Interactive interview sessions
- Real-time feedback
- Customizable question sets

## Setup Instructions

### 1. Clone the Repository

```sh
git clone <your-repo-url>
cd interviewbot
```

### 2. Create and Activate a Virtual Environment

```sh
python -m venv venv
venv\Scripts\activate   # On Windows
# source venv/bin/activate   # On macOS/Linux
```

### 3. Install Dependencies

```sh
pip install -r requirements.txt
```

### 4. Run the App

```sh
streamlit run src/interviewbot.py
```


## File Structure

```
root/
├── templates/
│   └── prompt_template.py
├── interviewbot.py
├── requirements.txt
├── README.md
└── venv/
```

