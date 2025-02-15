import openai
from pinecone import Pinecone, ServerlessSpec
import gradio as gr
import os
import datetime
from pathlib import Path


## Pine cone keys
PINECONE_API_KEY = "pcsk_4hRH9g_ACqpSNynt5Mco3mde1i4B3fDe12wJj23WGzTDd9EutMCG9QtuvzCTxoCgENiQFR"
PINECONE_ENV = "us-east-1"
PINECONE_INDEX_NAME = "martychat"

## OpenAI
OPENAI_API_KEY = "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"

OPENAI_ORG_ID = "org-BfSUBL7mVs5VGzQUKsVA1IoL"

OPENAI_EMBEDDING_MODEL = 'text-embedding-3-small'
OPENAI_QUERY_MODEL = "gpt-4"

## Set Read and Write Data Paths
DATA_PATH = '/Users/douglasalexander/MartyChatPDFs'
WRITE_PATH = '/Users/douglasalexander/MartyChat/martychat_log.txt'

user_name = "Athena Alexander"  ## we will take this from the login later.


# Initialize OpenAI
openai.api_key = OPENAI_API_KEY

# Initialize Pinecone
pc = Pinecone(
    api_key=PINECONE_API_KEY,
    environment=PINECONE_ENV  # e.g., 'gcp-starter', 'us-west1-gcp', etc.
)
index = pc.Index(PINECONE_INDEX_NAME)


# List existing indexes to ensure connection
print("Available Pinecone Indexes:", pc.list_indexes().names())

def preprocess_query(query):
    """
    Enhances query quality through basic text preprocessing and domain-specific augmentation.
    """
    # Define domain-specific terms and their expansions
    psychology_terms = {
        'psychology': 'psychological theory framework',
        'cognitive': 'cognitive processes thinking',
        'behavior': 'behavioral patterns response',
        'emotion': 'emotional response feeling affect',
        'mental': 'mental processes cognition',
        'therapy': 'therapeutic approach treatment',
        'research': 'research study findings evidence',
        'theory': 'theoretical framework concept model',
        'positive': 'positive psychology wellbeing',
        'learned': 'learning conditioning acquired',
        'seligman': 'seligman positive psychology learned helplessness optimism',
        'psychology': 'psychological theory research clinical',
        'compare': 'comparison differences similarities relationship between',
        'performance': 'performance achievement outcome'
    }

    # Basic text preprocessing
    text = query.lower()

    # Remove basic punctuation
    for punct in ',.!?;:':
        text = text.replace(punct, ' ')

    # Split into words
    words = text.split()

    # Remove common stop words while preserving question words
    stop_words = {'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 'has', 'he',
                 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the', 'to', 'was', 'were', 'will', 'with'}

    enhanced_words = [word for word in words if word not in stop_words]

    # Add domain-specific expansions
    for word in words:
        if word in psychology_terms:
            enhanced_words.extend(psychology_terms[word].split())

    # Reconstruct the enhanced query
    enhanced_query = ' '.join(enhanced_words)
    print(f"\nOriginal query: {query}")
    print(f"Enhanced query: {enhanced_query}")

    return enhanced_query

def analyze_query_complexity(query):
    """
    Analyzes query complexity to determine appropriate k value
    """
    # Calculate basic complexity metrics
    word_count = len(query.split())
    contains_comparison = any(word in query.lower() for word in ['compare', 'contrast', 'difference', 'relationship', 'versus', 'impact'])
    contains_theory = any(word in query.lower() for word in ['theory', 'concept', 'framework', 'approach', 'model'])
    contains_specific = any(word in query.lower() for word in ['specific', 'particular', 'exactly', 'precisely'])

    # Determine base k value
    if contains_specific:
        base_k = 3  # More focused retrieval for specific queries
    elif contains_comparison or contains_theory:
        base_k = 7  # Broader retrieval for theoretical or comparative queries
    else:
        base_k = 5  # Default value for standard queries

    # Adjust based on word count
    if word_count > 15:
        base_k += 2  # Increase k for longer, potentially more complex queries

    return base_k

def format_source_metadata(metadata):
    """
    Creates a formatted citation string from metadata
    """
    citation_parts = []

    if metadata['title']:
        citation_parts.append(metadata['title'])
    if metadata['author']:
        citation_parts.append(f"by {metadata['author']}")
    if metadata['year']:
        citation_parts.append(f"({metadata['year']})")
    if metadata['page']:
        citation_parts.append(f"p. {metadata['page']}")
    if metadata['file'] and not citation_parts:  # Use file name only if no other metadata
        citation_parts.append(metadata['file'])

    if not citation_parts:  # If no metadata available
        return "Source document"

    return ", ".join(citation_parts)

def format_citation_date(date_str):
    """
    Convert technical date format to standard year format for citations
    """
    try:
        # Handle the D:YYYYMMDDHHmmSS format
        if date_str.startswith('D:'):
            # Extract just the year portion (first 4 digits after 'D:')
            year = date_str[2:6]
            return year

        # Add additional date format handling if needed
        return date_str
    except:
        return 'n.d.'  # Return "no date" for any unparseable dates

def get_similar_docs(query, k=5):
    """
    Enhanced document retrieval with deduplication and improved citation formatting
    """
    enhanced_query = preprocess_query(query)

    search_queries = [
        f"Seligman theory research findings {enhanced_query}",
        f"Seligman psychological concepts methodology {enhanced_query}",
        f"Seligman research implications applications {enhanced_query}",
        f"Seligman psychology contributions development {enhanced_query}"
    ]

    all_results = []
    for search_query in search_queries:
        embedding = openai.Embedding.create(
            model=OPENAI_EMBEDDING_MODEL,
            input=search_query
        )["data"][0]["embedding"]

        results = index.query(
            vector=embedding,
            top_k=3,
            include_metadata=True
        )
        all_results.extend(results['matches'])

    # Use title as a key for deduplication
    seen_titles = {}
    for match in all_results:
        title = match['metadata'].get('title', '').strip()
        if title not in seen_titles or match['score'] > seen_titles[title]['score']:
            author = match['metadata'].get('Author', 'Unknown')
            year = format_citation_date(match['metadata'].get('Year', 'n.d.'))

            seen_titles[title] = {
                'score': match['score'],
                'content': match['metadata'].get('content', ''),
                'citation_info': {
                    'author': author,
                    'year': year,
                    'title': title
                }
            }

    # Sort by score and create sequential citations
    sorted_results = sorted(seen_titles.values(), key=lambda x: x['score'], reverse=True)[:k]

    citations = {}
    final_results = []

    for idx, result in enumerate(sorted_results, 1):
        citation_id = f"[{idx}]"
        citation = f"{result['citation_info']['author']} ({result['citation_info']['year']}). {result['citation_info']['title']}"

        citations[citation_id] = citation
        final_results.append({
            'score': result['score'],
            'content': result['content'],
            'citation_id': citation_id
        })

    return {
        'matches': final_results,
        'citations': citations
    }

def generate_response(question, context):
    """
    Generate responses that focus on utilizing the provided context
    """
    prompt = f"""Please provide a detailed response based on the information available in the provided context.
    Your response should be grounded in the actual content of the documents, drawing specific details
    and examples from the context. If the context provides limited or no information about certain aspects
    of the question, focus on what can be accurately discussed based on the available information.

    Context: {context}

    Question: {question}

    Important guidelines:
    - Base your response primarily on the information present in the context
    - Draw specific examples and details from the provided documents
    - If certain aspects cannot be addressed from the context, focus on what is well-supported
    - Maintain a clear connection to the documented evidence throughout your response"""

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a knowledgeable assistant who provides accurate, context-based responses. Always ground your answers in the provided documentary evidence."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )

    return response['choices'][0]['message']['content']

def generate_response_with_history(question, context, system_prompt):
    """
    Enhanced response generation that handles conversation flow
    """
    prompt = f"""Based on the provided context and considering any conversation history referenced in the question,
    please provide a thorough and coherent response.

    Context: {context}

    Question: {question}

    Please ensure your response:
    - Addresses any references to previous exchanges
    - Maintains consistent terminology
    - Provides clear connections to earlier discussed concepts when relevant"""

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )

    return response['choices'][0]['message']['content']

def format_citations(citations):
    """
    Format citations with deduplication and clear formatting
    """
    # Create a dictionary of unique sources
    unique_sources = {}
    for cid, source in citations.items():
        source_key = source.strip().lower()
        if source_key not in unique_sources:
            unique_sources[source_key] = cid

    # Format citations using only unique sources
    formatted_citations = []
    for source_key, cid in unique_sources.items():
        original_source = citations[cid]
        formatted_citations.append(f"{cid}: {original_source}")

    return "\n".join(formatted_citations)

def generate_response_with_citations(question, context, citations, system_prompt):
    """
    Generate responses that are positive and strictly based on provided context
    """
    enhanced_system_prompt = """You are a knowledgeable assistant specializing in presenting research and academic work in a constructive and positive manner. When discussing Seligman's work:

1. Focus on his contributions, insights, and the positive impact of his research
2. Present his theories and findings in an appreciative, professional tone
3. Use ONLY information provided in the context - do not reference external knowledge
4. If asked about topics not covered in the provided context, politely indicate that the information is not available in the current document set
5. Maintain academic rigor while highlighting the strengths and value of the work

Format your response with:
- Clear structure and logical flow
- Professional, formal language
- Full sentences and well-developed paragraphs
- Proper citation integration
"""

    prompt = f"""Based solely on the provided context, give a detailed and constructive response that highlights the value and contributions of the work. Do not include any information from outside the provided context.

Context: {context}

Question: {question}

Requirements:
1. Draw exclusively from the provided context
2. Present the information in a positive, appreciative manner
3. Use formal, professional language
4. Include relevant citations for all claims
5. If certain aspects cannot be addressed from the available context, acknowledge this professionally

Available Citations:
{format_citations(citations)}
"""

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": enhanced_system_prompt},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )

    response_text = response['choices'][0]['message']['content']

    # Ensure references are included
    if citations and "References:" not in response_text:
        response_text += "\n\nReferences:\n"
        for cid, source in citations.items():
            response_text += f"{cid}: {source}\n"

    return response_text

def process_query_with_history(question, history):
    """
    Process query with history and citation support
    """
    # Extract recent conversation context
    recent_context = []
    if history:
        for message in history[-3:]:  # Consider last 3 exchanges
            user_msg = message[0]
            assistant_msg = message[1]
            recent_context.append(f"User: {user_msg}")
            recent_context.append(f"Assistant: {assistant_msg}")

    # Enhance the current question with conversation context
    if recent_context:
        context_str = "\n".join(recent_context)
        enhanced_question = f"""Context from previous conversation:
{context_str}

Current question: {question}"""
        print("\nProcessing with conversation context")
    else:
        enhanced_question = question
        print("\nProcessing initial question")

    k = analyze_query_complexity(enhanced_question)
    results = get_similar_docs(enhanced_question, k)

    # Extract content and citations
    contexts = []
    citations = results['citations']

    for match in results['matches']:
        if match['score'] >= 0.45:
            contexts.append(f"{match['content']} {match['citation_id']}")

    combined_context = "\n\n".join(contexts)

    # Generate response with citations
    system_prompt = """You are a knowledgeable assistant providing cited responses.
    When answering:
    1. Use inline citations [1], [2], etc. when referencing specific information
    2. Include a References section at the end listing all cited sources
    3. Ensure every citation in the text corresponds to a reference
    4. Maintain a professional, academic tone
    5. Consider the conversation history for context
    6. Maintain continuity with previous responses"""

    response = generate_response_with_citations(enhanced_question, combined_context, citations, system_prompt)
    return response

def process_query(question):
    """
    Process query with dynamic k value determination.
    """
    k = analyze_query_complexity(question)
    print(f"\nQuery complexity analysis determined k={k}")

    results = get_similar_docs(question, k)

    contexts = []
    for match in results['matches']:
        if match['score'] >= 0.45:
            content = match['metadata'].get('content', match['metadata'].get('text', ''))
            contexts.append(content)

    combined_context = "\n\n".join(contexts)
    response = generate_response(question, combined_context)

    return response

def setup_logging(write_path):
    """
    Configure logging to a single, continuous file at the specified path
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(write_path), exist_ok=True)
    return write_path

def log_conversation(log_file_path, user_name, message, response, is_new_conversation=False):
    """
    Log conversation details to a continuous file with timestamps
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(log_file_path, 'a', encoding='utf-8') as f:
        if is_new_conversation:
            f.write("\n" + "="*50 + "\n")
            f.write(f"New Conversation - User: {user_name}\n")
            f.write(f"Started at: {timestamp}\n")
            f.write("="*50 + "\n\n")

        f.write(f"Time: {timestamp}\n")
        f.write(f"User: {message}\n")
        f.write(f"Assistant: {response}\n")
        f.write("-"*30 + "\n")

def create_chat_interface(user_name, write_path):
    """
    Creates a comprehensive chat interface with history tracking, logging, and citations
    """
    log_file_path = setup_logging(write_path)
    conversation_started = False

    with gr.Blocks(theme=gr.themes.Soft()) as chat_interface:
        gr.Markdown(f"""
        # Intelligent Document Query Assistant

        Welcome, {user_name}! Ask questions about the document collection.
        The system provides cited responses with references to source materials.
        """)

        chatbot = gr.Chatbot(
            label="Conversation",
            height=500,
            container=True,
            show_copy_button=True,
            type="messages"  # Using the modern message format
        )

        with gr.Group():
            query_box = gr.Textbox(
                label="Your Question",
                placeholder="Type your question here...",
                lines=2,
                max_lines=2
            )

            with gr.Row(equal_height=True):
                submit_button = gr.Button("Submit", scale=2, variant="primary")
                clear_button = gr.Button("Clear", scale=1)

        def respond(message, history):
            nonlocal conversation_started

            # Convert history for query processing
            conversation_history = []
            if history is not None:
                conversation_history = [(h["content"] if isinstance(h, dict) else h[0],
                                      h["content"] if isinstance(h, dict) else h[1])
                                     for h in history]

            try:
                # Process query with history and citations
                response = process_query_with_history(message, conversation_history)

                # Update history in message format
                history = history or []
                history.append({"role": "user", "content": message})
                history.append({"role": "assistant", "content": response})

                # Log the conversation
                log_conversation(
                    log_file_path,
                    user_name,
                    message,
                    response,
                    is_new_conversation=not conversation_started
                )
                conversation_started = True

                return "", history

            except Exception as e:
                error_message = "I apologize, but I encountered an error processing your question. Could you please rephrase it?"
                print(f"Error processing query: {str(e)}")

                # Log the error
                log_conversation(
                    log_file_path,
                    user_name,
                    message,
                    f"Error: {str(e)}\nResponse: {error_message}",
                    is_new_conversation=not conversation_started
                )
                conversation_started = True

                return "", history + [
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": error_message}
                ]

        def clear_history():
            """
            Resets the conversation and marks the next message as a new conversation
            """
            nonlocal conversation_started
            conversation_started = False
            return None

        # Connect interface elements to their handlers
        submit_button.click(respond, [query_box, chatbot], [query_box, chatbot])
        query_box.submit(respond, [query_box, chatbot], [query_box, chatbot])
        clear_button.click(clear_history, None, chatbot)

    return chat_interface

def search_content_check(query="Seligman"):
    """
    Diagnostic function to check content retrieval
    """
    print(f"Searching for content about: {query}")

    embedding = openai.Embedding.create(
        model=OPENAI_EMBEDDING_MODEL,
        input=query
    )["data"][0]["embedding"]

    results = index.query(
        vector=embedding,
        top_k=30,  # Increased to get a broader view
        include_metadata=True
    )

    print("\nFound Documents:")
    for idx, match in enumerate(results['matches']):
        print(f"\n--- Document {idx + 1} ---")
        print(f"Similarity Score: {match['score']:.4f}")
        content = match['metadata'].get('content', match['metadata'].get('text', ''))
        print(f"Content Preview: {content[:500]}...")


if __name__ == "__main__":
    # Create and launch the interface
    demo = create_chat_interface(user_name, WRITE_PATH)
    demo.launch(share=False, server_port=7861)
