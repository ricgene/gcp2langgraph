"""
Cloud Function (2nd gen) for processing queries with LangGraph.
https://www.perplexity.ai/search/call-langsmith-from-gcp-SUeirpGwS..iQt1Wb6WiPw
"""
import os
import json
import logging
import functions_framework
from flask import Request
from typing import Dict, Any
import google.cloud.logging
from dotenv import load_dotenv
import asyncio

from lg_utils import process_query, create_basic_chain

# Import the langgraph_sdk client
from langgraph_sdk import get_sync_client

# Load environment variables for local development
load_dotenv()

# Set up Cloud Logging (when running in GCP)
try:
    client = google.cloud.logging.Client()
    client.setup_logging()
except Exception:
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

def test_graph_locally(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Test the LangGraph locally with the given input data.
    
    Args:
        input_data: Dictionary containing user_input and previous_state
        
    Returns:
        Dictionary containing the graph's response
    """
    try:
        # Initialize the langgraph client
        client = get_sync_client(
            url=os.getenv("LANGGRAPH_DEPLOYMENT_URL"),
            api_key=os.getenv("LANGGRAPH_API_KEY")
        )
        
        # Stream the graph execution
        for chunk in client.runs.stream(
            None,  # Threadless run
            "superNode",  # Name of your assistant as defined in langgraph.json
            input=input_data,
            stream_mode="updates",
        ):
            logger.info(f"Receiving new event of type: {chunk.event}...")
            logger.info(chunk.data)
            
        return {
            "success": True,
            "response": "Graph execution completed",
            "mode": "local_test"
        }
        
    except Exception as e:
        logger.exception(f"Error testing graph locally: {str(e)}")
        return {
            "success": False,
            "error": f"Error testing graph: {str(e)}",
            "code": 500
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
            # Use the langgraph_sdk client to call the agent
            client = get_sync_client(
                url=os.getenv("LANGGRAPH_DEPLOYMENT_URL"),
                api_key=os.getenv("LANGGRAPH_API_KEY")
            )
            
            # Collect all chunks of data
            graph_output = []
            for chunk in client.runs.stream(
                None,  # Threadless run
                "superNode",  # Name of your assistant as defined in langgraph.json
                input={
                    "messages": [],
                    "step": "Do you have  minute to discuss Prizm Task <>"
                },
                stream_mode="updates",
            ):
                logger.info(f"Receiving new event of type: {chunk.event}...")
                logger.info(chunk.data)
                graph_output.append(chunk.data)
            
            result = {
                "success": True,
                "response": "Agent processing completed",
                "mode": "agent",
                "graph_output": graph_output
            }
        
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
    raw_input = {
        "messages": [],
        "step": "q1"
    }

    # Your agent input
    test_input = {
        "user_input": "",
        "previous_state": raw_input
    }
    
    # Run the local test
    print("Testing graph locally...")
    result = test_graph_locally(test_input)
    print("\nTest Result:")
    print(json.dumps(result, indent=2))