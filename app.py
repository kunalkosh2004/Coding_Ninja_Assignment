import streamlit as st
import google.generativeai as genai
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain.memory import ConversationBufferMemory
import json
import time
from datetime import datetime
from typing import Dict, List, Any
import re

# Configuration
st.set_page_config(
    page_title="Excel Mock Interviewer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1f4e79, #2e5984);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .interview-container {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #1f4e79;
    }
    .question-box {
        background: #e8f4f8;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #bee5eb;
        margin: 1rem 0;
    }
    .feedback-box {
        background: #d4edda;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #c3e6cb;
        margin: 1rem 0;
    }
    .score-box {
        background: #fff3cd;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #ffeaa7;
        text-align: center;
        font-size: 1.2em;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

class ExcelInterviewer:
    def __init__(self, api_key: str):
        """Initialize the Excel interviewer with Gemini AI"""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        self.conversation_history = []
        self.interview_state = "not_started"
        self.current_question_num = 0
        self.total_questions = 5
        self.candidate_responses = []
        self.question_bank = []
        
    def generate_question_bank(self) -> List[str]:
        """Generate a diverse set of Excel questions using Gemini"""
        prompt = """
        Generate 15 diverse Microsoft Excel interview questions covering different skill levels and topics.
        Include questions about:
        1. Basic formulas and functions (SUM, AVERAGE, COUNT, etc.)
        2. Advanced functions (VLOOKUP, HLOOKUP, INDEX-MATCH, etc.)
        3. Data analysis (Pivot Tables, filtering, sorting)
        4. Data visualization (Charts, conditional formatting)
        5. Excel shortcuts and productivity tips
        6. Problem-solving scenarios
        7. Data validation and error handling
        
        Format each question as a clear, specific question that would be asked in a real interview.
        Make questions practical and job-relevant.
        
        Return exactly 15 questions, one per line, numbered 1-15.
        """
        
        try:
            response = self.model.generate_content(prompt)
            questions = response.text.strip().split('\n')
            # Clean and extract questions
            cleaned_questions = []
            for q in questions:
                q = q.strip()
                if q and len(q) > 10:  # Filter out empty or too short lines
                    # Remove numbering if present
                    q = re.sub(r'^\d+\.\s*', '', q)
                    cleaned_questions.append(q)
            
            return cleaned_questions[:15]  # Ensure exactly 15 questions
        except Exception as e:
            st.error(f"Error generating questions: {str(e)}")
            # Fallback questions
            return [
                "Explain the difference between VLOOKUP and INDEX-MATCH functions.",
                "How would you remove duplicates from a large dataset in Excel?",
                "Describe how to create a dynamic chart that updates automatically.",
                "What are the key benefits of using Pivot Tables for data analysis?",
                "How do you use conditional formatting to highlight specific data patterns?"
            ]
    
    def start_interview(self) -> str:
        """Start the interview session"""
        self.interview_state = "introduction"
        self.question_bank = self.generate_question_bank()
        
        intro_message = """
        Hello! I'm your AI Excel Interview Assistant. I'll be conducting a structured interview to assess your Microsoft Excel skills.
        
        Here's how this will work:
        • I'll ask you 5 questions covering different Excel topics
        • Please provide detailed answers explaining your approach
        • After each response, I'll give you brief feedback
        • At the end, you'll receive a comprehensive evaluation report
        
        The interview should take about 15-20 minutes. Are you ready to begin?
        
        Let's start with your first question!
        """
        
        self.conversation_history.append(("AI", intro_message))
        return intro_message
    
    def get_next_question(self) -> str:
        """Get the next question from the generated question bank"""
        if self.current_question_num >= self.total_questions:
            return self.conclude_interview()
        
        # Randomly select a question from the bank (simulate randomness with time-based selection)
        import random
        available_questions = [q for q in self.question_bank if q not in [resp.get('question', '') for resp in self.candidate_responses]]
        
        if not available_questions:
            available_questions = self.question_bank
        
        question = random.choice(available_questions)
        self.current_question_num += 1
        
        formatted_question = f"**Question {self.current_question_num}/{self.total_questions}:**\n\n{question}"
        
        self.conversation_history.append(("AI", formatted_question))
        return formatted_question
    
    def evaluate_response(self, user_response: str, question: str) -> Dict[str, Any]:
        """Evaluate the user's response using Gemini AI"""
        evaluation_prompt = f"""
        You are an expert Excel interviewer. Evaluate this candidate's response to an Excel interview question.
        
        Question: {question}
        Candidate's Response: {user_response}
        
        Provide evaluation in this JSON format:
        {{
            "score": [score from 1-10],
            "strengths": ["list of strengths shown in the response"],
            "weaknesses": ["list of areas for improvement"],
            "feedback": "Detailed constructive feedback (2-3 sentences)",
            "technical_accuracy": [score from 1-10],
            "completeness": [score from 1-10],
            "clarity": [score from 1-10]
        }}
        
        Consider:
        - Technical accuracy of the information
        - Completeness of the answer
        - Clarity of explanation
        - Practical applicability
        - Best practices mentioned
        """
        
        try:
            response = self.model.generate_content(evaluation_prompt)
            # Try to extract JSON from the response
            response_text = response.text.strip()
            
            # Find JSON block
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                evaluation = json.loads(json_match.group())
            else:
                # Fallback evaluation
                evaluation = {
                    "score": 7,
                    "strengths": ["Provided relevant information"],
                    "weaknesses": ["Could provide more detail"],
                    "feedback": "Good response, consider adding more specific examples.",
                    "technical_accuracy": 7,
                    "completeness": 6,
                    "clarity": 7
                }
                
        except Exception as e:
            st.error(f"Evaluation error: {str(e)}")
            evaluation = {
                "score": 5,
                "strengths": ["Attempted to answer the question"],
                "weaknesses": ["Response needs more technical depth"],
                "feedback": "Please provide more detailed explanations with specific examples.",
                "technical_accuracy": 5,
                "completeness": 5,
                "clarity": 5
            }
        
        return evaluation
    
    def process_response(self, user_response: str) -> str:
        """Process user response and provide feedback"""
        if not user_response.strip():
            return "Please provide a response to continue with the interview."
        
        # Get the last question asked
        last_question = ""
        for speaker, message in reversed(self.conversation_history):
            if speaker == "AI" and "Question" in message:
                last_question = message
                break
        
        # Store the response
        self.conversation_history.append(("Human", user_response))
        
        # Evaluate the response
        evaluation = self.evaluate_response(user_response, last_question)
        
        # Store evaluation
        self.candidate_responses.append({
            "question": last_question,
            "response": user_response,
            "evaluation": evaluation
        })
        
        # Provide immediate feedback
        feedback = f"""
        **Quick Feedback:**
        
        Score: {evaluation['score']}/10
        
        {evaluation['feedback']}
        
        ---
        
        """
        
        self.conversation_history.append(("AI", feedback))
        
        # Get next question or conclude
        if self.current_question_num < self.total_questions:
            next_question = self.get_next_question()
            return feedback + next_question
        else:
            return feedback + self.conclude_interview()
    
    def conclude_interview(self) -> str:
        """Generate final interview report"""
        self.interview_state = "completed"
        
        # Calculate overall scores
        if not self.candidate_responses:
            return "Interview completed. No responses to evaluate."
        
        scores = [resp["evaluation"]["score"] for resp in self.candidate_responses]
        technical_scores = [resp["evaluation"]["technical_accuracy"] for resp in self.candidate_responses]
        completeness_scores = [resp["evaluation"]["completeness"] for resp in self.candidate_responses]
        clarity_scores = [resp["evaluation"]["clarity"] for resp in self.candidate_responses]
        
        overall_score = sum(scores) / len(scores)
        technical_avg = sum(technical_scores) / len(technical_scores)
        completeness_avg = sum(completeness_scores) / len(completeness_scores)
        clarity_avg = sum(clarity_scores) / len(clarity_scores)
        
        # Generate comprehensive report
        report_prompt = f"""
        Generate a comprehensive Excel interview evaluation report for a candidate.
        
        Interview Summary:
        - Questions Asked: {len(self.candidate_responses)}
        - Overall Score: {overall_score:.1f}/10
        - Technical Accuracy: {technical_avg:.1f}/10
        - Completeness: {completeness_avg:.1f}/10
        - Clarity: {clarity_avg:.1f}/10
        
        Individual Question Performance:
        {json.dumps([{
            "question_num": i+1,
            "score": resp["evaluation"]["score"],
            "strengths": resp["evaluation"]["strengths"],
            "weaknesses": resp["evaluation"]["weaknesses"]
        } for i, resp in enumerate(self.candidate_responses)], indent=2)}
        
        Generate a professional interview evaluation report including:
        1. Overall assessment and recommendation (Hire/No Hire/Maybe)
        2. Key strengths demonstrated
        3. Areas for improvement
        4. Specific Excel skills observed
        5. Recommendations for skill development
        
        Keep it professional but constructive.
        """
        
        try:
            response = self.model.generate_content(report_prompt)
            final_report = f"""
            ## 📋 Final Interview Report
            
            **Interview Completed:** {datetime.now().strftime("%Y-%m-%d %H:%M")}
            
            ### 📊 Score Summary
            - **Overall Score:** {overall_score:.1f}/10
            - **Technical Accuracy:** {technical_avg:.1f}/10
            - **Response Completeness:** {completeness_avg:.1f}/10
            - **Communication Clarity:** {clarity_avg:.1f}/10
            
            ### 📝 Detailed Assessment
            
            {response.text}
            
            ---
            
            Thank you for completing the Excel Mock Interview! Use this feedback to improve your Excel skills.
            """
            
        except Exception as e:
            final_report = f"""
            ## 📋 Final Interview Report
            
            **Interview Completed:** {datetime.now().strftime("%Y-%m-%d %H:%M")}
            
            ### 📊 Score Summary
            - **Overall Score:** {overall_score:.1f}/10
            - **Technical Accuracy:** {technical_avg:.1f}/10
            - **Response Completeness:** {completeness_avg:.1f}/10
            - **Communication Clarity:** {clarity_avg:.1f}/10
            
            ### 📝 Assessment
            Based on your responses, you demonstrated solid Excel knowledge with room for improvement.
            Focus on providing more detailed explanations and practical examples in your answers.
            
            Thank you for completing the interview!
            """
        
        self.conversation_history.append(("AI", final_report))
        return final_report

def main():
    """Main Streamlit application"""
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>📊 AI-Powered Excel Mock Interviewer</h1>
        <p>Practice your Excel skills with our intelligent AI interviewer</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("🔧 Configuration")
        
        # API Key input
        api_key = st.text_input(
            "Enter your Gemini API Key",
            type="password",
            help="Get your API key from Google AI Studio: https://makersuite.google.com/app/apikey"
        )
        
        if not api_key:
            st.warning("Please enter your Gemini API key to start the interview")
            st.info("🔗 Get your free API key from [Google AI Studio](https://makersuite.google.com/app/apikey)")
            return
        
        st.success("API Key configured!")
        
        # Interview settings
        st.header("📋 Interview Info")
        st.write("**Duration:** ~15-20 minutes")
        st.write("**Questions:** 5 random questions")
        st.write("**Topics:** Excel functions, formulas, data analysis, charts")
        
    # Initialize interviewer
    if 'interviewer' not in st.session_state:
        st.session_state.interviewer = ExcelInterviewer(api_key)
        st.session_state.messages = []
    
    # Update API key if changed
    if hasattr(st.session_state.interviewer, 'model'):
        try:
            genai.configure(api_key=api_key)
            st.session_state.interviewer.model = genai.GenerativeModel('gemini-pro')
        except:
            pass
    
    # Main interface
    interviewer = st.session_state.interviewer
    
    # Start interview button
    if interviewer.interview_state == "not_started":
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Start Excel Interview", type="primary", use_container_width=True):
                with st.spinner("Initializing interview and generating questions..."):
                    intro_message = interviewer.start_interview()
                    st.session_state.messages.append(("AI", intro_message))
                    # Get first question
                    first_question = interviewer.get_next_question()
                    st.session_state.messages.append(("AI", first_question))
                st.rerun()
    
    # Display conversation
    if st.session_state.messages:
        st.markdown('<div class="interview-container">', unsafe_allow_html=True)
        
        for speaker, message in st.session_state.messages:
            if speaker == "AI":
                st.markdown(f'<div class="question-box">{message}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f"**Your Response:** {message}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Input for user response
    if interviewer.interview_state in ["introduction", "ongoing"] or (interviewer.current_question_num > 0 and interviewer.current_question_num <= interviewer.total_questions):
        
        # Progress bar
        if interviewer.current_question_num > 0:
            progress = interviewer.current_question_num / interviewer.total_questions
            st.progress(progress, f"Question {interviewer.current_question_num}/{interviewer.total_questions}")
        
        # Response input
        user_input = st.text_area(
            "Your Response:",
            height=150,
            placeholder="Type your detailed answer here. Explain your approach, mention specific functions or features, and provide examples if possible."
        )
        
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("Submit Response", type="primary", disabled=not user_input.strip()):
                with st.spinner("Evaluating your response..."):
                    interviewer.interview_state = "ongoing"
                    response = interviewer.process_response(user_input)
                    st.session_state.messages.append(("Human", user_input))
                    st.session_state.messages.append(("AI", response))
                st.rerun()
    
    # Interview completion
    if interviewer.interview_state == "completed":
        st.balloons()
        st.success("🎉 Interview Completed!")
        
        # Download transcript option
        if st.button("📄 Download Interview Transcript"):
            transcript = "\n\n".join([f"{speaker}: {message}" for speaker, message in interviewer.conversation_history])
            st.download_button(
                label="Download Transcript",
                data=transcript,
                file_name=f"excel_interview_transcript_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain"
            )
        
        # Restart option
        if st.button("🔄 Start New Interview"):
            st.session_state.interviewer = ExcelInterviewer(api_key)
            st.session_state.messages = []
            st.rerun()

if __name__ == "__main__":
    main()