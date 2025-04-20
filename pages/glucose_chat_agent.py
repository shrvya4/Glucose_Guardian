from crewai import Agent, Task, Crew
import os
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

glucose_advisor = Agent(
    role="Glucose Management Advisor",
    goal="Provide concise, practical advice for managing glucose levels in different situations",
    backstory="""You are an expert in glucose management, specializing in providing 
    practical, evidence-based advice for everyday situations. You always keep answers 
    brief and actionable, focusing on 1-2 key strategies.""",
    verbose=True,
    llm_config={"model": "gpt-4", "api_key": OPENAI_API_KEY}
)

def get_glucose_advice(question):
    task = Task(
        description=f"Provide a brief, practical 1-2 sentence response to: {question}\n\nFocus on actionable advice for managing glucose levels.",
        expected_output="1-2 sentence practical advice",
        agent=glucose_advisor
    )
    
    crew = Crew(agents=[glucose_advisor], tasks=[task])
    return crew.kickoff()