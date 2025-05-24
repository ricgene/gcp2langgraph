# Testing the LangGraph Cloud Function

This document outlines the different methods for testing the LangGraph Cloud Function, both locally and in production.

## Prerequisites

- Python 3.11 or higher
- Virtual environment (recommended)
- Required environment variables in `.env.yaml`:
  ```
  LANGGRAPH_DEPLOYMENT_URL: "your-langgraph-deployment-url"
  LANGGRAPH_API_KEY: "your-langgraph-api-key"
  LANGSMITH_API_KEY: "your-langsmith-api-key"
  MODEL_NAME: "gpt-4"
  OPENAI_API_KEY: "your-openai-api-key"
  LANGCHAIN_API_KEY: "your-langchain-api-key"
  ```

## File Structure

- `main.py`: The main Cloud Function code (renamed from gcp2langgraph1.py for Cloud Functions deployment)
- `lg_utils.py`: Utility functions for LangGraph processing
- `requirements.txt`: Python dependencies
- `.env.yaml`: Environment variables for deployment

## Testing Methods

### Method 1: Direct Python Script Testing

Run the script directly using Python:

```bash
python main.py
```

Expected output:
```
Testing graph locally...
Test Result:
{
  "success": true,
  "response": "Graph execution completed",
  "mode": "local_test"
}
```

### Method 2: Local Cloud Function Testing

1. Start the Functions Framework server:
```bash
functions-framework --target=process_with_langgraph --source=main.py --debug --port=8080
```

2. Send a test request using curl:
```bash
curl -X POST http://localhost:8080 -H "Content-Type: application/json" -d '{"query": "test query", "mode": "agent"}'
```

Expected output:
```json
{
  "success": true,
  "response": "Agent processing completed",
  "mode": "agent",
  "graph_output": [
    {
      "attempt": 1,
      "run_id": "1f038458-0467-6c9b-a958-ddca6c309878"
    },
    {
      "__interrupt__": [
        {
          "ns": ["ask_q1:11824756-6c96-54ec-25ba-90c96c552509"],
          "resumable": true,
          "value": {
            "question": "What is your account number?"
          },
          "when": "during"
        }
      ]
    }
  ]
}
```

### Method 3: Deployed Cloud Function Testing

1. Deploy the function to Google Cloud Functions:
```bash
gcloud functions deploy langgraph-function --gen2 --runtime=python311 --region=us-central1 --source=. --entry-point=process_with_langgraph --env-vars-file=.env.yaml --trigger-http --allow-unauthenticated
```

2. Test the deployed function using curl:
```bash
curl -X POST https://langgraph-function-cs64iuly6q-uc.a.run.app -H "Content-Type: application/json" -d '{"query": "test query", "mode": "agent"}'
```

Expected output:
```json
{
  "success": true,
  "response": "Agent processing completed",
  "mode": "agent",
  "graph_output": [
    {
      "attempt": 1,
      "run_id": "1f038458-0467-6c9b-a958-ddca6c309878"
    },
    {
      "__interrupt__": [
        {
          "ns": ["ask_q1:11824756-6c96-54ec-25ba-90c96c552509"],
          "resumable": true,
          "value": {
            "question": "What is your account number?"
          },
          "when": "during"
        }
      ]
    }
  ]
}
```

## Notes

1. The function uses the "superNode" graph name for LangGraph processing
2. All three testing methods use the same core functionality but in different environments
3. The deployed function requires proper environment variables in `.env.yaml`
4. Logging is enabled for all methods to help with debugging
5. The function supports two modes:
   - "agent": Uses LangGraph for complex processing
   - "simple": Uses a basic chain for simple queries

## Troubleshooting

1. If you get a 403 Forbidden error:
   - Check that your LANGGRAPH_API_KEY is correct
   - Verify the LANGGRAPH_DEPLOYMENT_URL is valid

2. If you get a 422 Unprocessable Entity error:
   - Ensure you're using "superNode" as the graph name
   - Check that your input format is correct

3. If you get a 500 Internal Server Error:
   - Check the Cloud Functions logs in the Google Cloud Console
   - Verify all environment variables are set correctly