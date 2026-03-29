import streamlit as st
import os
import plotly.graph_objects as go
import random

st.set_page_config(page_title="InterviewCoach AI", page_icon="🎤", layout="wide")
st.title("🎤 InterviewCoach AI")
st.caption("Mock interview practice with instant AI feedback and scoring.")

GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")

QUESTION_BANK = {
    "Software Engineer": [
        "Tell me about yourself and your technical background.",
        "Explain the difference between a stack and a queue. When would you use each?",
        "Describe a challenging bug you fixed. How did you approach it?",
        "What is your experience with system design? Design a URL shortener.",
        "How do you handle code reviews — giving and receiving feedback?",
        "Explain Big O notation with an example from your own code.",
        "Tell me about a project you're most proud of. What was your contribution?",
        "How would you approach debugging a production outage at 2 AM?",
    ],
    "Data Scientist": [
        "Walk me through your end-to-end ML project workflow.",
        "How do you handle class imbalance in a classification problem?",
        "Explain the bias-variance tradeoff in simple terms.",
        "What's the difference between L1 and L2 regularization?",
        "How would you explain a complex model result to a non-technical stakeholder?",
        "Describe a time your model failed in production. What did you learn?",
        "How do you decide which ML algorithm to use for a problem?",
    ],
    "ML Engineer": [
        "How do you deploy a machine learning model to production?",
        "What is model drift and how do you detect and handle it?",
        "Explain the difference between batch and online learning.",
        "How would you optimize inference latency for a deep learning model?",
        "What MLOps tools have you used and why?",
        "How do you ensure reproducibility in ML experiments?",
        "Walk me through fine-tuning a pre-trained LLM for a custom task.",
    ],
    "Product Manager": [
        "Tell me about a product you love and how you'd improve it.",
        "How do you prioritize features when everything seems urgent?",
        "Walk me through how you'd launch a new feature end-to-end.",
        "How do you measure the success of a product feature?",
        "Tell me about a time you had to say no to a stakeholder request.",
        "How do you balance user needs vs business requirements?",
    ],
    "HR / Behavioral": [
        "Tell me about yourself.",
        "Describe a time you faced a conflict with a teammate. How did you resolve it?",
        "Tell me about a time you failed. What did you learn?",
        "Where do you see yourself in 5 years?",
        "Why do you want to work here?",
        "Describe your biggest strength and weakness honestly.",
        "Tell me about a time you led a team or initiative.",
    ],
}

def get_feedback(question, answer, role, gemini_key):
    if gemini_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel('gemini-2.0-flash')
            prompt = f"""You are an expert interviewer evaluating a {role} candidate.

Question: {question}
Candidate's Answer: {answer}

Score out of 10 for each (be strict but fair):
1. Clarity (was the answer clear and structured?)
2. Technical Depth (did they demonstrate real knowledge?)
3. Communication (professional, confident tone?)
4. Relevance (did they actually answer the question?)
5. Specificity (did they use real examples, numbers, specifics?)

Then provide:
- STRENGTH: What they did well (1-2 sentences)
- IMPROVE: What to improve (1-2 sentences)
- IDEAL: A sample ideal answer opening (2-3 sentences)
- FOLLOWUP: One natural follow-up question

Format EXACTLY:
CLARITY: [score]
TECHNICAL: [score]
COMMUNICATION: [score]
RELEVANCE: [score]
SPECIFICITY: [score]
STRENGTH: [text]
IMPROVE: [text]
IDEAL: [text]
FOLLOWUP: [text]"""
            resp = model.generate_content(prompt)
            return resp.text
        except Exception as e:
            return f"API Error: {e}"
    else:
        return """CLARITY: 6
TECHNICAL: 5
COMMUNICATION: 7
RELEVANCE: 6
SPECIFICITY: 4
STRENGTH: You structured your answer well and showed enthusiasm for the topic.
IMPROVE: Add specific numbers and examples — "I improved performance" is vague. Say by how much, using what technique.
IDEAL: "In my last internship, I reduced API latency by 40% by implementing Redis caching on frequently-queried endpoints, which I identified using profiling with cProfile."
FOLLOWUP: Can you walk me through the specific data structures you used and why you chose them?"""

def parse_feedback(text):
    result = {}
    for key in ['CLARITY','TECHNICAL','COMMUNICATION','RELEVANCE','SPECIFICITY',
                'STRENGTH','IMPROVE','IDEAL','FOLLOWUP']:
        for line in text.split('\n'):
            if line.startswith(key+':'):
                result[key] = line[len(key)+1:].strip()
    return result

# Session state
if 'question_idx' not in st.session_state:
    st.session_state.question_idx = 0
    st.session_state.session_scores = []
    st.session_state.history = []
    st.session_state.role = "Software Engineer"
    st.session_state.questions = []
    st.session_state.started = False

col1, col2 = st.columns([1, 1])

with col1:
    if not st.session_state.started:
        st.subheader("Setup Interview")
        role = st.selectbox("Interview Type", list(QUESTION_BANK.keys()))
        num_q = st.slider("Number of Questions", 3, 8, 5)
        if st.button("Start Interview", type="primary"):
            st.session_state.role = role
            q_pool = QUESTION_BANK[role].copy()
            random.shuffle(q_pool)
            st.session_state.questions = q_pool[:num_q]
            st.session_state.question_idx = 0
            st.session_state.session_scores = []
            st.session_state.history = []
            st.session_state.started = True
            st.rerun()
    else:
        idx = st.session_state.question_idx
        questions = st.session_state.questions
        
        if idx < len(questions):
            st.subheader(f"Question {idx+1} / {len(questions)}")
            st.info(questions[idx])
            
            answer = st.text_area("Your Answer", height=180,
                placeholder="Type your answer here. Be specific, use examples, mention metrics...")
            
            if not GEMINI_KEY:
                key_in = st.text_input("Gemini API Key (optional)", type="password")
                active_key = key_in
            else:
                active_key = GEMINI_KEY
            
            if st.button("Submit Answer", type="primary", disabled=not answer.strip()):
                with st.spinner("Analyzing your answer..."):
                    raw = get_feedback(questions[idx], answer, st.session_state.role, active_key)
                    parsed = parse_feedback(raw)
                    
                scores = [int(parsed.get(k, 5)) for k in
                          ['CLARITY','TECHNICAL','COMMUNICATION','RELEVANCE','SPECIFICITY']]
                avg = round(sum(scores)/len(scores), 1)
                
                st.session_state.session_scores.append(avg)
                st.session_state.history.append({
                    'q': questions[idx], 'a': answer, 'feedback': parsed, 'score': avg
                })
                st.session_state.question_idx += 1
                
                with col2:
                    st.subheader("Feedback")
                    st.metric("Answer Score", f"{avg}/10",
                              delta="good" if avg >= 7 else "needs work")
                    
                    dims = ['Clarity','Technical','Communication','Relevance','Specificity']
                    fig = go.Figure(go.Scatterpolar(
                        r=scores, theta=dims, fill='toself',
                        fillcolor='rgba(0,200,83,0.2)',
                        line=dict(color='#00c853', width=2)
                    ))
                    fig.update_layout(polar=dict(radialaxis=dict(range=[0,10])),
                                      height=220, showlegend=False,
                                      margin=dict(l=30,r=30,t=10,b=10),
                                      paper_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.success(f"**Strength:** {parsed.get('STRENGTH','')}")
                    st.warning(f"**Improve:** {parsed.get('IMPROVE','')}")
                    st.info(f"**Ideal opening:** {parsed.get('IDEAL','')}")
                    
                    if st.session_state.question_idx < len(questions):
                        if st.button("Next Question ➜"):
                            st.rerun()
                    else:
                        st.balloons()
                        if st.button("View Final Results ➜"):
                            st.rerun()
        else:
            # Final results
            scores = st.session_state.session_scores
            final = round(sum(scores)/len(scores)*10) if scores else 0
            st.subheader("Interview Complete!")
            st.metric("Final Readiness Score", f"{final}/100",
                      delta="Ready to apply!" if final >= 70 else "Keep practicing")
            
            for i, item in enumerate(st.session_state.history):
                with st.expander(f"Q{i+1}: {item['q'][:60]}... — Score: {item['score']}/10"):
                    st.write("**Your answer:**", item['a'])
                    st.write("**Feedback:**", item['feedback'].get('IMPROVE',''))
            
            if st.button("Start New Interview"):
                st.session_state.started = False
                st.rerun()

st.caption("Puru Mehra | github.com/purumehra1/interviewcoach-ai")
