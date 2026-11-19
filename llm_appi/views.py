
import os
import logging
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .rag import retrieve_context


# --------------------------------------------------
# Configuration
# --------------------------------------------------

logger = logging.getLogger(__name__)

# Load the .env file stored inside llm_appi
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None

MODEL_NAME = "gpt-4.1-mini"


# --------------------------------------------------
# Health Check API
# --------------------------------------------------

@api_view(["GET"])
def health_check(request):
    return Response({
        "status": "ok",
        "message": "REVOCATE API is running"
    })


# --------------------------------------------------
# Chat API with Conversation Memory + RAG
# --------------------------------------------------

@api_view(["POST"])
def chat(request):

    # Check whether the API key is configured.
    if client is None:
        return Response(
            {"error": "OpenAI API key is not configured."},
            status=500,
        )

    # Get the current user question.
    question = request.data.get("message", "")

    if not isinstance(question, str):
        return Response(
            {"error": "Message must be a string."},
            status=400,
        )

    question = question.strip()

    if not question:
        return Response(
            {"error": "Please provide a message."},
            status=400,
        )

    try:
        # 1. Retrieve relevant legal information from ChromaDB.
        context = retrieve_context(question)

        # 2. Read conversation history sent by React.
        raw_history = request.data.get("history", [])
        history = []

        if isinstance(raw_history, list):
            for item in raw_history[-12:]:

                if not isinstance(item, dict):
                    continue

                role = item.get("role")
                content = item.get("content")

                # Accept only valid conversation messages.
                if (
                    role in ("user", "assistant")
                    and isinstance(content, str)
                    and content.strip()
                ):
                    history.append({
                        "role": role,
                        "content": content.strip()[:6000],
                    })

        # 3. Add retrieved legal context to the current question.
        current_message = (
            f"Current question:\n{question}\n\n"
            f"Retrieved legal document context:\n{context}"
        )

        # 4. Send conversation history and current question to the AI.
        conversation = history + [
            {
                "role": "user",
                "content": current_message,
            }
        ]

        response = client.responses.create(
            model=MODEL_NAME,

            instructions=(
                "You are REVOCATE, an AI legal information assistant "
                "focused on Indian law.\n\n"

                "CONVERSATION RULES:\n"
                "- Use the previous conversation to understand follow-up "
                "messages such as 'ok bro', 'why?', 'explain that', "
                "'give an example', and 'what next?'.\n"
                "- Do not treat every new message as a new conversation.\n"
                "- If the user acknowledges an answer with 'ok', 'okay', "
                "or 'ok bro', respond naturally and briefly. Do not restart "
                "with a generic greeting.\n"
                "- If the user asks a follow-up, connect it to the relevant "
                "earlier messages when appropriate.\n"
                "- If the user starts a genuinely new topic, answer that "
                "new question normally.\n\n"

                "LEGAL RULES:\n"
                "- Answer clearly and conversationally.\n"
                "- Use retrieved document context when relevant.\n"
                "- Do not invent laws, sections, quotations, or citations.\n"
                "- If the retrieved context is insufficient, say so clearly.\n"
                "- Distinguish general legal information from legal advice.\n"
                "- Ask for jurisdiction or missing facts when necessary.\n"
                "- Do not claim to be a lawyer or guarantee legal outcomes."
            ),

            input=conversation,
        )

        # 5. Return the answer and retrieved sources to React.
        return Response({
            "answer": response.output_text,
            "sources": context,
        })

    except Exception:
        # Log the actual exception in the Django terminal.
        logger.exception("REVOCATE chat request failed")

        # Keep internal exception details out of the public response.
        return Response(
            {
                "error": (
                    "Unable to generate an answer. "
                    "Check the Django server logs."
                )
            },
            status=500,
        )
