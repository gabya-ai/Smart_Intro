# Genie-Hi: AI-Powered Cover Letter Generator

Genie-Hi is a web application that helps users write compelling cover letters. Leveraging the power of Google's Gemini-2.5-Flash model, it takes a user's resume and a job description to generate a tailored cover letter draft.

## Architecture

The application is composed of a Streamlit-based user interface and a backend powered by Google Cloud services.

*   **Frontend/UI**: The main user interface is a [Streamlit](https://streamlit.io/) application (`home.py`).
*   **Authentication**: User authentication is handled by a separate static site (`public/index.html`) hosted on Firebase Hosting, which uses Firebase Authentication (email/password). After a successful login, the user is redirected to the Streamlit app with a Firebase ID token for a secure session.
*   **AI Integration**: The application calls `core_llm.py` to construct a prompt and sends it to a Google Cloud Vertex AI model (`gemini-2.5-flash`) to generate a cover letter draft and resume suggestions.
*   **Database**: All data is persisted in Google Firestore. This includes user profiles, generation sessions, letter drafts, final versions, user feedback (thumbs up/down), and extensive interaction logs for analytics. The Levenshtein distance between the initial AI-generated draft and the user's final version is calculated to measure generation quality.

## Setup

To run this project locally, you will need to configure your environment:

1.  **Service Account Key**: A Google Cloud service account key file named `service-account-genie-hi-front.json` is required to be in the root directory.
2.  **Environment Variables**: Create a `.env` file in the root directory with the following content:
    ```
    GOOGLE_APPLICATION_CREDENTIALS="service-account-genie-hi-front.json"
    ```
3.  **Dependencies**: Install the Python dependencies from `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```
4.  **Prompts**: This project requires a `prompts.py` file, which is currently missing from the repository. This file should contain the prompts used to interact with the language model.

## Data Model

The application uses Google Firestore to store data in the following collections:

*   **users**: Stores user profile information.
*   **sessions**: Records each user session.
*   **letters**: Contains the generated cover letter drafts and final versions.
*   **interaction_logs**: Logs user interactions for analytics and evaluation.

## How to Run

1.  Ensure all the setup steps are completed.
2.  Run the Streamlit application:
    ```bash
    streamlit run home.py
    ```
