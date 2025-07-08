type HumanTools = ClarificationRequest | DoneForNow

class ClarificationRequest {
  reasoning string @description(#"
    why the task needs clarification?
  "#)
  intent "request_more_information"
  message string 
}

class DoneForNow {
  reasoning string @description(#"
    why the task is done?"
  "#)
  intent "done_for_now"
  message string @description(#"
    message to send to the user about the work that was done. 
  "#)
}

function DetermineNextStep(
    thread: string 
) ->  HumanTools | CalculatorTools {
    client "openai/gpt-4o-mini" 

    prompt #"
        {{ _.role("system") }}

        You are a helpful assistant that can help solve a given task.

        {{ _.role("user") }}

        You are working on the following thread:

        {{ thread }}

        {{ _.role("assistant") }}

        What should the next step be?

        {{ ctx.output_format }}

        First, think about the task at hand, what do you have to solve it, and plan out what to do next.
    "#
}

test HelloWorld {
  functions [DetermineNextStep]
  args {
    thread #"
      {
        "type": "user_input",
        "data": "How're you doing?"
      }
    "#
  }
}

test MathOperation {
  functions [DetermineNextStep]
  args {
    thread #"
      {
        "type": "user_input",
        "data": "can you multiply 3 and 4?"
      }
    "#
  }
  @@assert(intent, {{this.intent == "multiply"}})
}

test LongMath {
  functions [DetermineNextStep]
  args {
    thread #"
      [
        {
          "type": "user_input",
          "data": "can you multiply 3 and 4, then divide the result by 2 and then add 12 to that result?"
        },
        {
          "type": "tool_call",
          "data": {
            "intent": "multiply",
            "a": 3,
            "b": 4
          }
        },
        {
          "type": "tool_response",
          "data": 12
        },
        {
          "type": "tool_call", 
          "data": {
            "intent": "divide",
            "a": 12,
            "b": 2
          }
        },
        {
          "type": "tool_response",
          "data": 6
        },
        {
          "type": "tool_call",
          "data": {
            "intent": "add", 
            "a": 6,
            "b": 12
          }
        },
        {
          "type": "tool_response",
          "data": 18
        }
      ]
    "#
  }
  @@assert(intent, {{this.intent == "done_for_now"}})
  @@assert(answer, {{"18" in this.message}})
}


test MathOperationWithClarification {
  functions [DetermineNextStep]
  args {
    thread #"
          [{"type":"user_input","data":"can you multiply 3 and feee9ff10"}]
      "#
  }
  @@assert(intent, {{this.intent == "request_more_information"}})
}

test MathOperationPostClarification {
  functions [DetermineNextStep]
  args {
    thread #"
        [
        {"type":"user_input","data":"can you multiply 3 and FD*(#F&& ?"},
        {"type":"tool_call","data":{"intent":"request_more_information","message":"It seems like there was a typo or mistake in your request. Could you please clarify or provide the correct numbers you would like to multiply?"}},
        {"type":"human_response","data":"lets try 12 instead"},
      ]
      "#
  }
  @@assert(intent, {{this.intent == "multiply"}})
  @@assert(a, {{this.b == 12}})
  @@assert(b, {{this.a == 3}})
}

