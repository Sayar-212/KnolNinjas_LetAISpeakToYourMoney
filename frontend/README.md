# Run and deploy your AI Studio app

This contains everything you need to run your app locally.

## Run Locally

**Prerequisites:**  Node.js, Backend server running


1. Install dependencies:
   `npm install`
2. Set the `GEMINI_API_KEY` in [.env.local](.env.local) to your Gemini API key
3. Set the `REACT_APP_BACKEND_URL` in [.env.local](.env.local) to your backend server URL (default: http://localhost:8000)
4. Make sure your backend server is running
5. Run the app:
   `npm run dev`
