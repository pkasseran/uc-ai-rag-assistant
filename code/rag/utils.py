import re
import textwrap

def deduplicate_docs(docs):
    """
    When retrieving documents from a vector store, you might get duplicate 
    or near-duplicate documents. This function ensures you only show unique content to the user.
    """
    seen = set()  # Track hashes of documents we've already seen
    unique = []    # Store unique documents

    for doc in docs:
        # Create a hash of the document's content
        digest = hash(doc.page_content.strip())
        
        # If we haven't seen this content before
        if digest not in seen:
            seen.add(digest)        # Remember this hash
            unique.append(doc)      # Add document to unique list
    
    return unique



def format_answer(answer_text):
    """
    Cleans up and formats the AI's response text by removing extra empty lines,
    preserving code blocks, and ensuring code blocks are separated.
    """
    # Updated regex: match code blocks with or without language
    segments = re.split(r'(```[\w]*\n[\s\S]*?```|```\n[\s\S]*?```)', answer_text)
    formatted = []

    for seg in segments:
        if seg.startswith("```") and seg.rstrip().endswith("```"):
            # Remove leading/trailing newlines and dedent code
            lines = seg.strip('\n').split('\n')
            if len(lines) > 1:
                code_header = lines[0]
                code_body = "\n".join(lines[1:])
                code_body = textwrap.dedent(code_body)
                seg = code_header + "\n" + code_body + "\n"
            # Ensure exactly one blank line before and after code block
            if formatted and not formatted[-1].endswith('\n'):
                formatted.append('\n')
            formatted.append(seg)
            formatted.append('\n')
        else:
            # For non-code, collapse multiple blank lines, strip trailing spaces
            cleaned = re.sub(r'\n\s*\n', '\n\n', seg.strip())
            if cleaned:
                if formatted and not formatted[-1].endswith('\n'):
                    formatted.append('\n')
                formatted.append(cleaned)
                formatted.append('\n')

    result = "".join(formatted).strip('\n')

    return result + "\n"

# Test format_answer function
if __name__ == "__main__":
    test_text = """
To use LangChain with Unity Catalog AI, follow these steps:

1. **Prerequisites:**
   - Ensure you have Python 3.10 or higher installed.
   - Install the Unity Catalog AI integration package for LangChain:


```bash
     pip install unitycatalog-langchain
     ```


- If you need to interact with Databricks Unity Catalog, install the optional package dependency:


```bash
     pip install unitycatalog-langchain[databricks]
     ```


2. **Setup:**
   - Initialize your language model (LLM) using LangChain. You can use OpenAI or another LLM of your choice.
   - Define a prompt using `ChatPromptTemplate` to guide the agent's behavior.

3. **Create and Use the Agent:**
   - Define the agent using `create_tool_calling_agent`, specifying the tools from your toolkit.
   - Create an `AgentExecutor` to manage the agent's execution.
   - Invoke the agent with an input to perform tasks using Unity Catalog functions.

   Example code snippet:


```python
   from langchain.agents import AgentExecutor, create_tool_agent
   from langchain.llms import OpenAI
   from langchain.prompts import ChatPromptTemplate

   # Initialize the LLM
   llm = OpenAI(temperature=0)

   # Define the prompt
   prompt = ChatPromptTemplate.from_messages(
   [
   (
   "system",
   "You are a helpful assistant. Make sure to use tool for information.",
   ),
   ("placeholder", "{chat_history}"),
   ("human", "{input}"),
   ("placeholder", "{agent_scratchpad}"),
   ]
   )

   # Define the agent
   agent = create_tool_calling_agent(llm, tools, prompt)

   # Create the agent executor
   agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
   agent_executor.invoke({"input": "What is 36939 * 8922.4?"})
   ```


By following these steps, you can integrate Unity Catalog AI with LangChain to enhance your language model applications with robust and secure tools.
    """
    
    formatted_text = format_answer(test_text)
    print("Formatted Text:\n", formatted_text)