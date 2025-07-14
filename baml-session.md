# example of a baml session

```bash
$ uv run python -m src.cli.main
Welcome to the Agent Primitives CLI!
What's your question?: I need to calc some math

2025-07-11T12:07:54.075 [BAML INFO] Function DetermineNextStep:
    Client: openai/gpt-4o-mini (gpt-4o-mini-2024-07-18) - 2112ms. StopReason: stop. Tokens(in/out): 257/60
    ---PROMPT---
    system: You are a helpful assistant that can help solve a given task.
    user: You are working on the following thread:
    
    {"type":"user_input","data":"I need to calc some math"}
    assistant: What should the next step be?
    
    Answer in JSON using any of these schemas:
    {
      // why the task needs clarification?
      reasoning: string,
      intent: "request_more_information",
      message: string,
    } or {
      // why the task is done?"
      reasoning: string,
      intent: "done_for_now",
      // message to send to the user about the work that was done.
      message: string,
    } or {
      intent: "add",
      a: int or float,
      b: int or float,
    } or {
      intent: "subtract",
      a: int or float,
      b: int or float,
    } or {
      intent: "multiply",
      a: int or float,
      b: int or float,
    } or {
      intent: "divide",
      a: int or float,
      b: int or float,
    }
    
    First, think about the task at hand, what do you have to solve it, and plan out what to do next.
    
    ---LLM REPLY---
    {
      "reasoning": "The user did not specify what kind of math calculations they need to perform or provide the numbers involved.",
      "intent": "request_more_information",
      "message": "Could you please specify what kind of math calculations you need to perform and the numbers involved?"
    }
    ---Parsed Response (class ClarificationRequest)---
    {
      "reasoning": "The user did not specify what kind of math calculations they need to perform or provide the numbers involved.",
      "intent": "request_more_information",
      "message": "Could you please specify what kind of math calculations you need to perform and the numbers involved?"
    }

Could you please specify what kind of math calculations you need to perform and the numbers involved?? (type 'exit' to quit): I need multiply 156 and 23

2025-07-11T12:08:54.748 [BAML INFO] Function DetermineNextStep:
    Client: openai/gpt-4o-mini (gpt-4o-mini-2024-07-18) - 2033ms. StopReason: stop. Tokens(in/out): 332/61
    ---PROMPT---
    system: You are a helpful assistant that can help solve a given task.
    user: You are working on the following thread:
    
    {"type":"user_input","data":"I need to calc some math"}
    {"type":"system_response","data":{"reasoning":"The user did not specify what kind of math calculations they need to perform or provide the numbers involved.","intent":"request_more_information","message":"Could you please specify what kind of math calculations you need to perform and the numbers involved?"}}
    {"type":"user_input","data":"I need multiply 156 and 23"}
    assistant: What should the next step be?
    
    Answer in JSON using any of these schemas:
    {
      // why the task needs clarification?
      reasoning: string,
      intent: "request_more_information",
      message: string,
    } or {
      // why the task is done?"
      reasoning: string,
      intent: "done_for_now",
      // message to send to the user about the work that was done.
      message: string,
    } or {
      intent: "add",
      a: int or float,
      b: int or float,
    } or {
      intent: "subtract",
      a: int or float,
      b: int or float,
    } or {
      intent: "multiply",
      a: int or float,
      b: int or float,
    } or {
      intent: "divide",
      a: int or float,
      b: int or float,
    }
    
    First, think about the task at hand, what do you have to solve it, and plan out what to do next.
    
    ---LLM REPLY---
    To solve the multiplication task provided by the user, I will respond with the appropriate intent indicating the multiplication operation and the numbers involved.
    
    Here's the next step in JSON format:
    
    json
    {
      "intent": "multiply",
      "a": 156,
      "b": 23
    }
    
    ---Parsed Response (class MultiplyTool)---
    {
      "intent": "multiply",
      "a": 156,
      "b": 23
    }
2025-07-11T12:08:57.162 [BAML INFO] Function DetermineNextStep:
    Client: openai/gpt-4o-mini (gpt-4o-mini-2024-07-18) - 2407ms. StopReason: stop. Tokens(in/out): 363/119
    ---PROMPT---
    system: You are a helpful assistant that can help solve a given task.
    user: You are working on the following thread:
    
    {"type":"user_input","data":"I need to calc some math"}
    {"type":"system_response","data":{"reasoning":"The user did not specify what kind of math calculations they need to perform or provide the numbers involved.","intent":"request_more_information","message":"Could you please specify what kind of math calculations you need to perform and the numbers involved?"}}
    {"type":"user_input","data":"I need multiply 156 and 23"}
    {"type":"tool_call","data":{"intent":"multiply","a":156,"b":23}}
    {"type":"tool_response","data":3588}
    assistant: What should the next step be?
    
    Answer in JSON using any of these schemas:
    {
      // why the task needs clarification?
      reasoning: string,
      intent: "request_more_information",
      message: string,
    } or {
      // why the task is done?"
      reasoning: string,
      intent: "done_for_now",
      // message to send to the user about the work that was done.
      message: string,
    } or {
      intent: "add",
      a: int or float,
      b: int or float,
    } or {
      intent: "subtract",
      a: int or float,
      b: int or float,
    } or {
      intent: "multiply",
      a: int or float,
      b: int or float,
    } or {
      intent: "divide",
      a: int or float,
      b: int or float,
    }
    
    First, think about the task at hand, what do you have to solve it, and plan out what to do next.
    
    ---LLM REPLY---
    The math task of multiplying 156 and 23 has been completed, and the result of that multiplication is 3588. Since the user did not specify any further calculations or additional requests, I will mark the task as done for now.
    
    Here is the response in the appropriate JSON format:
    
    json
    {
      "reasoning": "The multiplication task has been successfully completed.",
      "intent": "done_for_now",
      "message": "The result of multiplying 156 and 23 is 3588. If you need help with anything else, feel free to ask!"
    }
    
    ---Parsed Response (class DoneForNow)---
    {
      "reasoning": "The multiplication task has been successfully completed.",
      "intent": "done_for_now",
      "message": "The result of multiplying 156 and 23 is 3588. If you need help with anything else, feel free to ask!"
    }
The result of multiplying 156 and 23 is 3588. If you need help with anything else, feel free to ask!
```