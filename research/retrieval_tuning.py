import random
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from backend.repositories.vector_db import InMemoryVectorStore, VectorStore
from langchain.schema import QuestionAnswerPair
from langchain.vectorstores import OpenAIEmbeddings

from utils import calculate_metric_avg, evaluate_retrieval

HYPERPARAMETERS = {
    "chunk_size": [250, 500, 1000],
    "chunk_overlap": [100, 150, 200],
    "embeddings": ["text-embedding-3-small", "text-embedding-3-large"],
    "retriever": ["k-nearest-neighbors", "similarity-search"],
    "k": [3, 5, 10],
}


@dataclass
class TrialResult:
    hyperparameters: Dict[str, Any]
    metrics: Dict[str, float]

class RetrievalEvaluationPipeline:
    def __init__(
        self,
        hyperparameter_space: Dict[str, List] = HYPERPARAMETERS,
        retriever: Optional[Any] = None,
        vector_store: Optional[VectorStore] = None,
    ):
        self.hyperparameter_space = hyperparameter_space
        self.retriever = retriever
        self.vector_store = vector_store
        self._raw_retrieval_metrics = []
        self._avg_retrieval_metrics = {}
        self.trial_results: List[TrialResult] = []
        self.current_hyperparameters = self._sample_hyperparameters()
        
        if not retriever or not vector_store:
            self._init_vector_store()
            self._init_retriever()

    def _sample_hyperparameters(self) -> Dict[str, Any]:
        """Randomly sample a set of hyperparameters from the defined space."""
        return {
            key: random.choice(values)
            for key, values in self.hyperparameter_space.items()
        }

    def run_trial(self, qa_pairs: List[QuestionAnswerPair]) -> TrialResult:
        """Run a single trial with randomly sampled hyperparameters."""
        self.current_hyperparameters = self._sample_hyperparameters()
        self._init_vector_store()
        self._init_retriever()
        
        metrics = self.evaluate(qa_pairs)
        trial = TrialResult(
            hyperparameters=self.current_hyperparameters.copy(),
            metrics=metrics
        )
        self.trial_results.append(trial)
        return trial

    def run_random_search(self, qa_pairs: List[QuestionAnswerPair], n_trials: int) -> List[TrialResult]:
        """Run multiple trials with different hyperparameter combinations."""
        for _ in range(n_trials):
            self.run_trial(qa_pairs)
        return self.trial_results

    def get_best_trial(self, metric: str = "mean_reciprocal_rank") -> TrialResult:
        """Get the trial with the best performance on the specified metric."""
        if not self.trial_results:
            raise ValueError("No trials have been run yet")
        
        return max(
            self.trial_results,
            key=lambda x: x.metrics.get(metric, float("-inf"))
        )
        
    def _init_retriever(self):
        search_type = "similarity_search" if self.current_hyperparameters["retriever"] == "similarity-search" else "knn"
        self.retriever = self.vector_store.as_retriever(
            search_type=search_type,
            search_kwargs={
                "k": self.current_hyperparameters["k"],
            }
        )
    
    def _init_vector_store(self):
        embeddings = OpenAIEmbeddings(model=self.current_hyperparameters["embeddings"])
        self.vector_store = InMemoryVectorStore(embeddings=embeddings)

    def evaluate(self, qa_pairs: List[QuestionAnswerPair]) -> Dict:
        self._raw_retrieval_metrics = evaluate_retrieval(qa_pairs, self.retriever)
        self._avg_retrieval_metrics = calculate_metric_avg(self._raw_retrieval_metrics)
        return self._avg_retrieval_metrics
    
    @property
    def retrieval_metrics(self):
        return self._raw_retrieval_metrics if self._raw_retrieval_metrics else "No retrieval metrics available"
    
    @property
    def avg_retrieval_metrics(self):
        return self._avg_retrieval_metrics if self._avg_retrieval_metrics else "No average retrieval metrics available"
