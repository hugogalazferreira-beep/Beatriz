# Beatriz AI Chatbot Assistant

This chatbot is designed to qualify leads and schedule meetings for Hugo Galaz (IT, Cybersecurity, and AI Consultant).

## Components

1.  **Backend (FastAPI):** Handles the communication with the Google Gemini API and manages the "Beatriz" AI persona.
2.  **Frontend (Vanilla JS):** A standalone, embeddable widget that can be injected into any website.

## How to Run the Backend

### 1. Set up Environment Variables
Create a `.env` file in the root directory (or use `.env.example` as a template):
```env
GEMINI_API_KEY=your_google_gemini_api_key
```

### 2. Local Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run the FastAPI server
uvicorn app:app --host 0.0.0.0 --port 8000
```

### 3. Docker Deployment
```bash
# Build the image
docker build -t beatriz-chatbot .

# Run the container
docker run -p 8000:8000 --env-file .env beatriz-chatbot
```

## How to Embed the Widget

To add the Beatriz chatbot to your website, copy and paste the following `<script>` tag into your HTML (typically before the closing `</body>` tag) or your website's custom code settings (e.g., in Lovable):

```html
<script src="https://your-backend-url.com/static/widget.js" defer></script>
```

**Note:** Replace `https://your-backend-url.com` with the actual URL where you have deployed the FastAPI backend.

### Important Configuration

1.  **CORS:** Ensure your website's domain is added to the `origins` list in `app.py` to allow the widget to communicate with the backend.
2.  **API URL:** Update the `API_URL` constant in `static/widget.js` to point to your deployed backend URL.

## Features

-   **Modern UI:** Dark mode by default with Tech Blue (#3b82f6) accents.
-   **AI Persona:** Beatriz is programmed to qualify visitors and offer a 15-minute diagnostic call.
-   **Session Persistence:** Chat history is maintained as long as the user's browser session is active.
-   **Fully Embeddable:** Uses Tailwind CSS via CDN for styling, requiring no complex frontend build process.
