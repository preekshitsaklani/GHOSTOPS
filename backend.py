import os
import json
from typing import List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from file_processor import extract_text_from_file
from dotenv import load_dotenv

# Load environment variables from .env.local
load_dotenv('.env.local')

app = FastAPI(title="ClarityOS API")

# Allow CORS for local testing/injection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- NVIDIA NIM CONFIGURATION ---
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
NVIDIA_BASE_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
MODEL_ID = os.getenv("NVIDIA_MODEL_ID", "openai/gpt-oss-20b")

client = OpenAI(
    base_url=NVIDIA_BASE_URL,
    api_key=NVIDIA_API_KEY
)

print(f"Connected to NVIDIA NIM")
print(f"Model Loaded: {MODEL_ID}")

# --- MOCK DB & CONFIG ---
try:
    with open("mentor_knowledge_base.json", "r") as f:
        MENTOR_DB = json.load(f)
except FileNotFoundError:
    MENTOR_DB = [] # Fallback if scraper hasn't run

SYSTEM_PROMPT_DIAGNOSIS = """
You are ClarityOS, an AI startup advisor. Your job is to gather enough information to create a comprehensive "Mentor Context Pack" document.

## CONVERSATION FLOW:

**PHASE 1: Information Gathering (Messages 1-7 MAX)**
- Ask focused questions to understand the problem
- You may ask UP TO 7 questions, but STOP EARLIER if you have enough info
- Cover these areas:
  1. User type (Founder/Professional/Business)
  2. Specific challenge they're facing
  3. Current metrics (revenue, users, runway)
  4. What they've tried already
  5. What outcome they want
  6. Any constraints (time, budget, resources)
  7. Timeline urgency
- Encourage file uploads: "📎 Upload your pitch deck or metrics for better analysis"
- After gathering enough info, set ready_for_document = true

**PHASE 2: Document Review**
- When ready_for_document = true, we generate the Mentor Context Pack
- User reviews and can request changes
- Listen for confirmation words: "done", "looks good", "perfect", "no changes", "finalize"
- If user requests changes, incorporate them and regenerate

**PHASE 3: Mentor Matching**
- After document finalized, show mentor recommendations
- Each mentor should have a specific reason why they match

## INTELLIGENCE RULES:
1. MAXIMUM 7 questions across the conversation
2. Ask 2-3 questions per message to be efficient
3. If user provides detailed info upfront, skip to document faster
4. Analyze uploaded files and mention specific insights
5. When enough info gathered, say: "I have enough information to create your Mentor Context Pack!"

## DETECTING "DONE" SIGNALS:
Finalize document when user says: "done", "looks good", "perfect", "that's fine", 
"no changes", "all good", "finalize", "save it", "confirmed", "approved", or similar.

## OUTPUT FORMAT (JSON):
{
    "reply": "Your response (be concise)",
    "category": "Fundraising" | "Growth" | "Product-Market Fit" | "General",
    "conversation_state": "gathering_info" | "reviewing_doc" | "finalized",
    "question_count": 1-7,
    "ready_for_document": true/false,
    "document_finalized": true/false,
    "problem_summary": "Summary of user's problem",
    "insights": ["insight1", "insight2", "insight3"],
    "metrics": {"key": "value"},
    "questions_for_mentor": ["question1", "question2", "question3"],
    "keywords": ["keyword1", "keyword2"]
}
"""

SYSTEM_PROMPT_SCRIBE = """
You are the Session Scribe. 
Extract 3 distinct Action Items from the transcript.
Return JSON: {"action_plan": [{"task": "...", "why": "...", "due": "...", "metric": "..."}], "clarity_score": 0-100, "reason": "..."}
"""



# --- MODELS ---
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    history: List[ChatMessage]
    file_context: Optional[str] = None

class AnalysisRequest(BaseModel):
    transcript: str


# --- HELPER FUNCTIONS ---
def simple_rag_search(query: str, category: str):
    """
    MVP Semantic Search Simulation.
    In prod, use OpenAIEmbeddings + Faiss.
    """
    results = []
    query_terms = set(query.lower().split())
    
    for mentor in MENTOR_DB:
        # Simple weighted scoring
        score = 0
        text_blob = (mentor['name'] + " " + mentor['bio'] + " " + mentor['outcomes']).lower()
        
        # Category boost
        if category and category.lower() in text_blob:
            score += 5
            
        # Keyword match
        for term in query_terms:
            if term in text_blob:
                score += 1
                
        if score > 0:
            results.append({"mentor": mentor, "score": score})
            
    # Sort by score
    results.sort(key=lambda x: x['score'], reverse=True)
    return [r['mentor'] for r in results[:3]]

# --- ENDPOINTS ---

@app.get("/")
def health_check():
    return {"status": "ClarityOS Online", "mentors_indexed": len(MENTOR_DB), "model": MODEL_ID}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload and parse a file (PDF, DOCX, CSV, XLSX, PPTX, TXT, MD).
    Saves to Neo4j and JSON file.
    Returns extracted text content.
    """
    import os
    import re
    from database import db
    
    try:
        content = await extract_text_from_file(file)
        
        # Get filename without extension
        filename_base = os.path.splitext(file.filename)[0]
        filename_safe = re.sub(r'[^\w\-]', '_', filename_base)
        file_type = os.path.splitext(file.filename)[1].replace('.', '')
        
        # Create folder and save JSON
        folder_name = f"data_extracted_from_file_from_{filename_safe}"
        folder_path = os.path.join(os.path.dirname(__file__), folder_name)
        os.makedirs(folder_path, exist_ok=True)
        
        json_path = os.path.join(folder_path, f"{filename_safe}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            import json as json_module
            json_module.dump({
                "filename": file.filename,
                "file_type": file_type,
                "content": content,
                "extracted_at": str(import_datetime())
            }, f, indent=2, ensure_ascii=False)
        
        # Save to Neo4j
        doc_id = db.save_file_content(file.filename, content, file_type)
        
        return {
            "filename": file.filename,
            "content": content,
            "status": "success",
            "saved_to": {
                "neo4j_doc_id": doc_id,
                "json_path": json_path
            }
        }
    except Exception as e:
        print(f"Upload error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

def import_datetime():
    from datetime import datetime
    return datetime.now().isoformat()

@app.post("/chat/message")
async def chat_handler(request: ChatRequest):
    """
    Main conversational loop with document generation flow.
    States: gathering_info -> reviewing_doc -> finalized -> show_mentors
    """
    import re
    from document_generator import create_addressible_docx, extract_document_data
    
    user_msg = request.history[-1].content
    sanitized = [{"role": "assistant" if m.role == "bot" else m.role, "content": m.content} for m in request.history]
    
    # Count user messages
    user_message_count = len([m for m in request.history if m.role == "user"])
    
    # Detect "done" signals for document finalization
    done_signals = ["done", "looks good", "perfect", "no changes", "all good", 
                    "finalize", "save it", "confirmed", "approved", "that's fine", 
                    "great", "yes", "correct", "save", "proceed"]
    is_done_signal = any(signal in user_msg.lower() for signal in done_signals)
    
    # Inject context into system prompt
    system_content = SYSTEM_PROMPT_DIAGNOSIS
    system_content += f"\n\nCONVERSATION STATE: This is user message #{user_message_count}."
    
    if user_message_count >= 7:
        system_content += " You MUST now generate the document. No more questions!"
    
    if is_done_signal:
        system_content += " User indicated they're satisfied. Set document_finalized=true."
    
    if request.file_context:
        system_content += f"\n\nUSER FILE CONTEXT (analyze and mention insights):\n{request.file_context[:6000]}"
    
    messages = [{"role": "system", "content": system_content}] + sanitized

    # NVIDIA NIM Call
    try:
        completion = client.chat.completions.create(
            model=MODEL_ID,
            messages=messages,
            temperature=0.3,
            max_tokens=1500
        )
        llm_raw = completion.choices[0].message.content
        
        # Parse JSON from LLM response
        try:
            json_match = re.search(r'\{[\s\S]*\}', llm_raw)
            if json_match:
                ai_data = json.loads(json_match.group())
            else:
                raise ValueError("No JSON found")
        except:
            ai_data = {
                "reply": llm_raw,
                "category": "General",
                "conversation_state": "gathering_info",
                "ready_for_document": False
            }
        
    except Exception as e:
        print(f"NVIDIA API Error: {e}")
        ai_data = {
            "reply": "I'm having trouble processing. Could you describe your main challenge in a few sentences?",
            "category": "General",
            "conversation_state": "gathering_info"
        }

    # Extract AI response data
    reply = ai_data.get("reply", "Tell me more about your challenge.")
    category = ai_data.get("category", "General")
    conversation_state = ai_data.get("conversation_state", "gathering_info")
    ready_for_document = ai_data.get("ready_for_document", False)
    document_finalized = ai_data.get("document_finalized", False)
    keywords = ai_data.get("keywords", [])
    
    # Force document generation after 7 messages
    if user_message_count >= 7 and conversation_state == "gathering_info":
        ready_for_document = True
        conversation_state = "reviewing_doc"
    
    # Detect done signal - finalize document
    if is_done_signal and conversation_state == "reviewing_doc":
        document_finalized = True
        conversation_state = "finalized"

    # Category detection fallback
    if category == "General":
        if any(w in user_msg.lower() for w in ["fund", "investor", "raise", "pitch", "vc"]):
            category = "Fundraising"
        elif any(w in user_msg.lower() for w in ["growth", "scale", "customer", "marketing"]):
            category = "Growth"
        elif any(w in user_msg.lower() for w in ["pmf", "product", "validate"]):
            category = "Product-Market Fit"

    # Build base response
    response_payload = {
        "reply": reply,
        "cards": [],
        "conversation_state": conversation_state,
        "message_count": user_message_count
    }

    # Handle document generation
    if ready_for_document and conversation_state != "finalized":
        # Generate document preview
        doc_data = extract_document_data(
            [{"role": m.role, "content": m.content} for m in request.history],
            ai_data
        )
        _, doc_preview = create_addressible_docx(**doc_data)
        
        response_payload["document_preview"] = doc_preview
        response_payload["show_review_buttons"] = True
        response_payload["reply"] = "📄 Here's your **Mentor Context Pack** preview:\n\n" + doc_preview + "\n\n✅ **Does this look good?** Or let me know what changes you'd like!"

    # Handle document finalization
    if document_finalized:
        doc_data = extract_document_data(
            [{"role": m.role, "content": m.content} for m in request.history],
            ai_data
        )
        file_path, doc_preview = create_addressible_docx(**doc_data, filename="addressible.docx")
        
        response_payload["document_saved"] = True
        response_payload["document_path"] = file_path
        response_payload["reply"] = f"✅ **Document saved!** (`{file_path}`)\n\n🎯 Now let me recommend the perfect mentors for your situation..."
        
        # Get mentor matches with reasons
        matches = simple_rag_search(user_msg + " " + " ".join(keywords), category)
        for m in matches:
            m["why_this_mentor"] = generate_mentor_reason(m, category, ai_data.get("problem_summary", ""))
        response_payload["cards"] = matches
        response_payload["show_mentors"] = True

    return response_payload


def generate_mentor_reason(mentor: dict, category: str, problem_summary: str) -> str:
    """Generate a specific reason why this mentor matches the user's needs."""
    name = mentor.get("name", "This mentor")
    bio = mentor.get("bio", "")
    outcomes = mentor.get("outcomes", "")
    
    if "fundraising" in category.lower():
        return f"{name} has deep experience in fundraising. {outcomes} Their background in {bio[:50]}... makes them ideal for your funding needs."
    elif "growth" in category.lower():
        return f"{name} specializes in scaling businesses. {outcomes} Perfect for tackling your growth challenges."
    else:
        return f"{name} is a proven expert. {outcomes} Their experience aligns well with your situation."

@app.post("/generate-pdf")
async def generate_context_pdf(
    user_summary: str,
    category: str,
    mentors: List[str]
):
    """
    Generate a Mentor Context Pack PDF.
    Returns a simple HTML version (can be converted to PDF with a library).
    """
    from datetime import datetime
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><title>Mentor Context Pack</title></head>
    <body style="font-family: Arial, sans-serif; padding: 40px; max-width: 800px; margin: auto;">
        <h1 style="color: #2563EB;">🎯 Mentor Context Pack</h1>
        <p style="color: #6B7280;">Generated on {datetime.now().strftime('%B %d, %Y')}</p>
        <hr>
        
        <h2>Problem Summary</h2>
        <p style="background: #F3F4F6; padding: 16px; border-radius: 8px;">{user_summary}</p>
        
        <h2>Category: {category}</h2>
        
        <h2>Recommended Mentors</h2>
        <ul>
            {"".join([f"<li><b>{m}</b></li>" for m in mentors])}
        </ul>
        
        <h2>Questions to Prepare</h2>
        <ul>
            <li>What specific outcome do you want from this session?</li>
            <li>What have you already tried?</li>
            <li>What constraints are you working with?</li>
        </ul>
        
        <hr>
        <p style="color: #9CA3AF; font-size: 12px;">Powered by ClarityOS | ExpertBells</p>
    </body>
    </html>
    """
    
    return {"html": html_content, "status": "success"}


async def analyze_session(request: AnalysisRequest):
    """
    The Scribe: Generates Action Plan from text using NVIDIA NIM.
    """
    try:
        completion = client.chat.completions.create(
            model=MODEL_ID,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_SCRIBE},
                {"role": "user", "content": request.transcript}
            ],
            temperature=0.1
        )
        # Assuming the model returns valid JSON string
        content = completion.choices[0].message.content
        # In prod: validation logic here
        return json.loads(content)
        
    except Exception as e:
        print(f"Error: {e}")
        # Fallback for demo
        return {
            "action_plan": [
                {"task": "Review pitch deck narrative", "due": "2 days"},
                {"task": "Identify 10 target VCs", "due": "5 days"}
            ]
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
