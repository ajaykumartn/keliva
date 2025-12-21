"""
Knowledge Vault Service
RAG-based long-term memory system that stores and retrieves personal context about users.
Uses ChromaDB for vector storage and semantic search.
"""
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import os
import json
import uuid
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from groq import AsyncGroq
from .rate_limiter import get_rate_limiter, GroqModel, RateLimitExceededError


@dataclass
class Fact:
    """Represents a personal fact about the user"""
    id: str
    user_id: str
    entity: str  # "Abhishek", "Mom", "Robotics Project"
    relation: str  # "friend", "family", "project"
    attribute: str  # "annoying", "health issue", "deadline"
    value: str  # "today", "recovering", "next week"
    context: str  # Full sentence where fact was mentioned
    timestamp: datetime
    embedding: Optional[List[float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "entity": self.entity,
            "relation": self.relation,
            "attribute": self.attribute,
            "value": self.value,
            "context": self.context,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Fact":
        """Create from dictionary"""
        return cls(
            id=data["id"],
            user_id=data["user_id"],
            entity=data["entity"],
            relation=data["relation"],
            attribute=data["attribute"],
            value=data["value"],
            context=data["context"],
            timestamp=datetime.fromisoformat(data["timestamp"]) if isinstance(data["timestamp"], str) else data["timestamp"]
        )


@dataclass
class EntityGraph:
    """Represents relationship graph for a specific entity"""
    entity: str
    relationships: Dict[str, List[str]] = field(default_factory=dict)  # relation_type -> [related_entities]
    attributes: Dict[str, str] = field(default_factory=dict)  # attribute_name -> value


class KnowledgeVault:
    """
    RAG-based long-term memory system for storing and retrieving personal context.
    Uses ChromaDB for vector storage and Groq LLM for fact extraction.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        persist_directory: str = "./chroma_db"
    ):
        """
        Initialize Knowledge Vault with ChromaDB and Groq client.
        
        Args:
            api_key: Groq API key (defaults to GROQ_API_KEY env var)
            persist_directory: Directory to persist ChromaDB data
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY must be provided or set in environment")
        
        # Initialize Groq client for fact extraction
        self.client = AsyncGroq(api_key=self.api_key)
        self.model = "llama-3.3-70b-versatile"  # Use 70B for better fact extraction
        self.rate_limiter = get_rate_limiter()
        
        # Initialize ChromaDB with sentence-transformers embedding
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Create ChromaDB client
        self.chroma_client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get or create collection for user facts
        self.collection = self.chroma_client.get_or_create_collection(
            name="user_facts",
            embedding_function=self.embedding_function,
            metadata={"description": "Personal facts and context about users"}
        )
    
    async def extract_facts(
        self,
        user_id: str,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> List[Fact]:
        """
        Extracts structured facts from user message using LLM.
        
        Args:
            user_id: User identifier
            message: User's message text
            conversation_history: Optional recent conversation for context
            
        Returns:
            List of extracted Fact objects
        """
        if not message or not message.strip():
            return []
        
        # Create prompt for fact extraction
        prompt = self._create_extraction_prompt(message, conversation_history)
        
        try:
            # Check rate limit before making API call
            self.rate_limiter.check_and_increment(GroqModel.LLAMA_70B)
            
            # Call Groq API for fact extraction
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_extraction_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,  # Low temperature for consistent extraction
                max_tokens=1000
            )
            
            # Parse LLM response
            llm_output = response.choices[0].message.content
            facts = self._parse_extraction_response(user_id, message, llm_output)
            
            return facts
            
        except RateLimitExceededError:
            # Re-raise rate limit errors
            raise
        except Exception as e:
            print(f"Error extracting facts: {e}")
            return []
    
    def _get_extraction_system_prompt(self) -> str:
        """Returns system prompt for fact extraction"""
        return """You are an expert at extracting personal information from conversations.

Your task is to identify and structure facts about:
- People (names, relationships, characteristics)
- Events (dates, activities, plans)
- Preferences (likes, dislikes, habits)
- Emotions (feelings, concerns, worries)
- Projects (work, hobbies, goals)

Return your response in this EXACT JSON format:
{
  "facts": [
    {
      "entity": "Name or thing being discussed",
      "relation": "friend|family|colleague|project|event|preference|emotion",
      "attribute": "Specific characteristic or detail",
      "value": "The value or description",
      "context": "The exact sentence or phrase from the message"
    }
  ]
}

Guidelines:
- Extract ALL meaningful personal information
- Be specific about entities (use actual names)
- Include emotional context when present
- Capture relationships between entities
- If no facts found, return empty array
- Only extract facts explicitly stated, don't infer"""
    
    def _create_extraction_prompt(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Creates prompt for fact extraction"""
        prompt = f"""Extract personal facts from this message:

"{message}"
"""
        
        if conversation_history:
            history_text = "\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in conversation_history[-3:]  # Last 3 messages for context
            ])
            prompt += f"""
Recent conversation context:
{history_text}
"""
        
        prompt += "\nProvide extracted facts in the JSON format specified."
        return prompt
    
    def _parse_extraction_response(
        self,
        user_id: str,
        original_message: str,
        llm_output: str
    ) -> List[Fact]:
        """
        Parses LLM response and creates Fact objects.
        
        Args:
            user_id: User identifier
            original_message: Original user message
            llm_output: Raw output from LLM
            
        Returns:
            List of Fact objects
        """
        try:
            # Extract JSON from response
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', llm_output, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_match = re.search(r'\{.*\}', llm_output, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    return []
            
            data = json.loads(json_str)
            facts = []
            
            for fact_data in data.get("facts", []):
                fact = Fact(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    entity=fact_data.get("entity", ""),
                    relation=fact_data.get("relation", ""),
                    attribute=fact_data.get("attribute", ""),
                    value=fact_data.get("value", ""),
                    context=fact_data.get("context", original_message),
                    timestamp=datetime.now()
                )
                facts.append(fact)
            
            return facts
            
        except Exception as e:
            print(f"Error parsing extraction response: {e}")
            return []
    
    async def store_fact(self, fact: Fact) -> None:
        """
        Stores fact in vector database with embeddings.
        
        Args:
            fact: Fact object to store
        """
        try:
            # Create document text for embedding
            document = f"{fact.entity} {fact.relation} {fact.attribute}: {fact.value}. Context: {fact.context}"
            
            # Store in ChromaDB (embedding generated automatically)
            self.collection.add(
                documents=[document],
                metadatas=[{
                    "user_id": fact.user_id,
                    "entity": fact.entity,
                    "relation": fact.relation,
                    "attribute": fact.attribute,
                    "value": fact.value,
                    "context": fact.context,
                    "timestamp": fact.timestamp.isoformat()
                }],
                ids=[fact.id]
            )
            
        except Exception as e:
            print(f"Error storing fact: {e}")
            raise
    
    async def retrieve_context(
        self,
        query: str,
        user_id: str,
        top_k: int = 5
    ) -> List[Fact]:
        """
        Retrieves most relevant facts for current conversation using semantic search.
        
        Args:
            query: Current user message or query
            user_id: User identifier
            top_k: Number of facts to retrieve (default: 5)
            
        Returns:
            List of relevant Fact objects
        """
        try:
            # Query ChromaDB with semantic search
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                where={"user_id": user_id}  # Filter by user
            )
            
            # Convert results to Fact objects
            facts = []
            if results and results["metadatas"] and results["metadatas"][0]:
                for i, metadata in enumerate(results["metadatas"][0]):
                    fact = Fact(
                        id=results["ids"][0][i],
                        user_id=metadata["user_id"],
                        entity=metadata["entity"],
                        relation=metadata["relation"],
                        attribute=metadata["attribute"],
                        value=metadata["value"],
                        context=metadata["context"],
                        timestamp=datetime.fromisoformat(metadata["timestamp"])
                    )
                    facts.append(fact)
            
            return facts
            
        except Exception as e:
            print(f"Error retrieving context: {e}")
            return []
    
    async def get_entity_relationships(self, entity_name: str, user_id: str) -> EntityGraph:
        """
        Returns relationship graph for a specific entity.
        
        Args:
            entity_name: Name of the entity to query
            user_id: User identifier
            
        Returns:
            EntityGraph with relationships and attributes
        """
        try:
            # Get all facts for the user first, then filter by entity
            all_facts = self.get_all_facts(user_id)
            
            # Build entity graph
            graph = EntityGraph(entity=entity_name)
            
            # Filter facts for this entity
            entity_facts = [f for f in all_facts if f.entity.lower() == entity_name.lower()]
            
            for fact in entity_facts:
                relation = fact.relation
                attribute = fact.attribute
                value = fact.value
                
                # Add to relationships
                if relation not in graph.relationships:
                    graph.relationships[relation] = []
                if value not in graph.relationships[relation]:
                    graph.relationships[relation].append(value)
                
                # Add to attributes
                graph.attributes[attribute] = value
            
            return graph
            
        except Exception as e:
            print(f"Error getting entity relationships: {e}")
            return EntityGraph(entity=entity_name)
    
    def get_all_facts(self, user_id: str, limit: int = 100) -> List[Fact]:
        """
        Retrieves all facts for a user (for debugging/admin purposes).
        
        Args:
            user_id: User identifier
            limit: Maximum number of facts to retrieve
            
        Returns:
            List of all Fact objects for the user
        """
        try:
            results = self.collection.get(
                where={"user_id": user_id},
                limit=limit
            )
            
            facts = []
            if results and results["metadatas"]:
                for i, metadata in enumerate(results["metadatas"]):
                    fact = Fact(
                        id=results["ids"][i],
                        user_id=metadata["user_id"],
                        entity=metadata["entity"],
                        relation=metadata["relation"],
                        attribute=metadata["attribute"],
                        value=metadata["value"],
                        context=metadata["context"],
                        timestamp=datetime.fromisoformat(metadata["timestamp"])
                    )
                    facts.append(fact)
            
            return facts
            
        except Exception as e:
            print(f"Error getting all facts: {e}")
            return []
    
    def delete_fact(self, fact_id: str) -> bool:
        """
        Deletes a specific fact from the vault.
        
        Args:
            fact_id: ID of the fact to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.collection.delete(ids=[fact_id])
            return True
        except Exception as e:
            print(f"Error deleting fact: {e}")
            return False
    
    def clear_user_facts(self, user_id: str) -> bool:
        """
        Clears all facts for a specific user.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get all fact IDs for this user
            results = self.collection.get(
                where={"user_id": user_id}
            )
            
            if results and results["ids"]:
                self.collection.delete(ids=results["ids"])
            
            return True
        except Exception as e:
            print(f"Error clearing user facts: {e}")
            return False
