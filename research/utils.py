

from dataclasses import dataclass
from typing import Dict, List

import numpy as np
from langchain.prompts import ChatPromptTemplate
from langchain.schema import AIMessage
from langchain_openai import ChatOpenAI


@dataclass
class QuestionAnswerPair:
    question: AIMessage
    source_chunk: str
    chunk_index: int
    retrieved_chunks: List[str] = None
    answer: str = None

def generate_question(text):
    question_generator = ChatPromptTemplate.from_template(
        """
        Generate a question a user would ask about the following text. 
        The question should be a single sentence and and not use phrases like
        'according to this paper' or 'according to the paper': {text}"""
    )
    question_llm = ChatOpenAI(model="gpt-3.5-turbo")

    question_chain = question_generator | question_llm


    return question_chain.invoke({"text": text})

def evaluate_retrieval(
    qa_pairs: List[QuestionAnswerPair], 
    retriever,
    k: int = 3
) -> Dict:
    """
    Evaluate retriever performance using generated QA pairs
    """
    metrics = {
        "precision": [],
        "recall": [],
        "mrr": [] 
    }
    
    for qa_pair in qa_pairs:
        # Get retrieved chunks
        question = qa_pair.question.content
        retrieved_docs = retriever.invoke(question)
        retrieved_chunks = [doc.page_content for doc in retrieved_docs]
        qa_pair.retrieved_chunks = retrieved_chunks
        
        # Calculate precision and recall
        relevant_retrieved = sum(
            1 for chunk in retrieved_chunks[:k] 
            if chunk == qa_pair.source_chunk
        )
        
        precision = relevant_retrieved / k
        recall = 1 if relevant_retrieved > 0 else 0
        
        # Calculate MRR
        try:
            rank = retrieved_chunks.index(qa_pair.source_chunk) + 1
            mrr = 1 / rank
        except ValueError:
            mrr = 0
            
        metrics["precision"].append(precision)
        metrics["recall"].append(recall)
        metrics["mrr"].append(mrr)
    
    return metrics

def calculate_metric_avg(metrics: Dict) -> Dict:
    metric_names = list(metrics.keys()) 
    results = {}

    for metric in metric_names:
        results[f"avg_{metric}"] = float(np.mean(metrics[metric]))
    
    return results