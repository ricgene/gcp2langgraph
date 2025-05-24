"""
Cloud Function (2nd gen) for processing queries with LangGraph.
"""
import os
import json
import logging
import functions_framework
from flask import Request
from typing import Dict, Any
import google.cloud.logging
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import ChatPromptTemplate

# Load environment variables for local development
load_dotenv()

# Set up Cloud Logging (when running in GCP)
try:
    client = google.cloud.logging.Client()
    client.setup_logging()
except Exception:
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

def create_basic_chain():
    """Create a basic LangChain chain for simple queries."""
    llm = ChatOpenAI(
        model_name=os.getenv("MODEL_NAME", "gpt-4"),
        temperature=0
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful AI assistant."),
        ("human", "{input}")
    ])
    return LLMChain(llm=llm, prompt=prompt)

def process_query(query: str) -> Dict[str, Any]:
    """Process a query using the LangGraph agent."""
    try:
        # For now, just use the basic chain
        chain = create_basic_chain()
        response = chain.invoke(query)
        return {
            "success": True,
            "response": response
        }
    except Exception as e:
        logger.exception(f"Error processing query: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@functions_framework.http
def process_with_langgraph(request: Request) -> Dict[str, Any]:
    """
    Cloud Function entry point that processes a request with LangGraph.
    
    Args:
        request: The Flask request object
        
    Returns:
        Dictionary that will be converted to a JSON response
    """
    # Log the function invocation
    logger.info("LangGraph function invoked")
    
    # Parse the request
    try:
        request_json = request.get_json(silent=True)
        if not request_json:
            return {
                "success": False,
                "error": "No JSON data in request",
                "code": 400
            }, 400
        
        # Extract the query from the request
        query = request_json.get("query")
        mode = request_json.get("mode", "agent")  # 'agent' or 'simple'
        
        if not query:
            return {
                "success": False,
                "error": "No query provided in request",
                "code": 400
            }, 400
            
        # Log the query
        logger.info(f"Processing query: {query[:100]}{'...' if len(query) > 100 else ''}")
        
        # Process the query
        if mode == "simple":
            # Use the simple chain for basic processing
            chain = create_basic_chain()
            response = chain.invoke(query)
            result = {
                "success": True,
                "response": response,
                "mode": "simple"
            }
        else:
            # Use the full LangGraph agent
            result = process_query(query)
            result["mode"] = "agent"
        
        # Add timestamp to the response
        result["timestamp"] = str(request.timestamp)
        
        # Log successful processing
        logger.info(f"Successfully processed query")
        
        # Return the result
        return result, 200
        
    except Exception as e:
        # Log the error
        logger.exception(f"Error processing request: {str(e)}")
        
        # Return an error response
        return {
            "success": False,
            "error": f"Internal server error: {str(e)}",
            "code": 500
        }, 500


# This allows running the code locally for testing
if __name__ == "__main__":
    # For local testing
    from functions_framework import create_app
    
    print("Starting local development server...")
    app = create_app(target=process_with_langgraph)
    app.run(host="localhost", port=8080, debug=True)