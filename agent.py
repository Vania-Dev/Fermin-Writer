from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_aws import ChatBedrock
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage
from langchain_text_splitters import RecursiveCharacterTextSplitter
from tools import get_s3_audio_uri, transcribe_audio_with_aws, upload_text_to_s3
import uuid

# Create Bedrock model instance
model = ChatBedrock(
    model_id="amazon.nova-micro-v1:0",
    region_name="us-east-1"
)

# Define the prompt template for gothic story rewriting
# This template instructs the AI to write in Fermín's characteristic style
template = PromptTemplate(
    input_variables=["text_chunk"],
    template="""
    You are Fermin Romero de Torres from *The Shadow of the Wind*. 
    Your duty is as follows:
    - Rewrite the following text in a poetic, gothic, and haunting style.
    - Avoid using any words or references related to politics.
    - Do not add unnecessary elaborations or filler content; focus strictly on restructuring and refining the original text.
    - The text must be captivating, so the reader cannot stop once they begin.
    - Do not write your own name.
    - The response must be written in Spanish.

    Text:
    {text_chunk}
    """
)

# === Typed State Definition ===
class GraphState(TypedDict):
    bucket_name: str       # S3 bucket name
    audio_s3_key: str      # S3 key for the audio file
    audio_name: str        # Name of the audio file (without extension)
    audio_s3_uri: str      # S3 URI for the audio file
    audio_text_raw: str    # Raw transcribed text content
    stories: list[str]     # List of generated gothic stories
    counter: int           # Counter for numbering output files
    output_s3_keys: list[str]  # S3 keys for uploaded story files


def rewrite_large_text_with_template(original_text: str, counter: int) -> str:
    """
    Rewrites large text using LLM with PromptTemplate and text chunking.
    
    Args:
        original_text: The original transcribed text to rewrite
        counter: Story counter for progress tracking
    
    Returns:
        The complete rewritten text in gothic style
    """
    # Split large text into manageable chunks to avoid token limits
    splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
    chunks = splitter.split_text(original_text)

    rewritten_chunks = []

    # Process each chunk individually through the LLM
    for i, chunk in enumerate(chunks, 1):
        print(f"🪶 Processing history {counter} part {i}/{len(chunks)}...")
        
        # Fill the template with the current chunk
        prompt_filled = template.format(text_chunk=chunk)
        
        # Create message and send to the model
        msg = [HumanMessage(content=prompt_filled)]
        response = model.invoke(msg)
        rewritten_chunks.append(response.content.strip())

    # Join all rewritten chunks into final text
    final_text = "\n\n".join(rewritten_chunks)
    return final_text


def prepare_audio(state: GraphState) -> GraphState:
    """
    Prepare audio S3 URI and extract name.
    
    Args:
        state: Current workflow state with S3 info
    
    Returns:
        Updated state with S3 URI and audio name
    """
    # Extract audio name from S3 key
    state["audio_name"] = state["audio_s3_key"].split("/")[-1].split(".")[0]
    
    # Generate S3 URI for Transcribe
    state["audio_s3_uri"] = get_s3_audio_uri(state["bucket_name"], state["audio_s3_key"])
    
    return state


def generate_audio_transcription(state: GraphState) -> GraphState:
    """
    Generate audio transcription using Amazon Transcribe.
    
    Args:
        state: Current workflow state
    
    Returns:
        Updated state with transcribed text
    """
    # Generate unique job name
    job_name = f"transcribe-{state['audio_name']}-{uuid.uuid4().hex[:8]}"
    
    # Transcribe audio using AWS Transcribe
    state["audio_text_raw"] = transcribe_audio_with_aws(state["audio_s3_uri"], job_name)
    print(state["audio_text_raw"])
    
    print("Transcription completed")
    return state


def generate_history(state: GraphState) -> GraphState:
    """
    Generate multiple gothic story variations and upload to S3.
    
    Args:
        state: Current workflow state with transcribed text
    
    Returns:
        Updated state with generated stories and S3 upload info
    """
    print("Generating stories...")
    state["output_s3_keys"] = []

    # Generate 3 different gothic story variations
    for i in range(3):
        # Generate gothic rewrite of the transcribed text
        text_generated = rewrite_large_text_with_template(state["audio_text_raw"], state["counter"])
        state["stories"].append(text_generated)
        
        # Upload directly to S3
        s3_key = f"audio-fermin/history/{state['audio_name']}_story_{state['counter']}.txt"
        upload_text_to_s3(state["bucket_name"], text_generated, s3_key)
        state["output_s3_keys"].append(s3_key)
        
        state["counter"] += 1

    return state


# === Workflow Graph Definition ===
workflow = StateGraph(GraphState)

# Add workflow nodes
workflow.add_node("prepare_audio", prepare_audio)
workflow.add_node("transcribe_audio", generate_audio_transcription)
workflow.add_node("generate_history", generate_history)

# Define workflow execution order
workflow.set_entry_point("prepare_audio")
workflow.add_edge("prepare_audio", "transcribe_audio")
workflow.add_edge("transcribe_audio", "generate_history")
workflow.add_edge("generate_history", END)

# Compile the workflow graph
graph = workflow.compile()