import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load environment variables from .env.local
load_dotenv('.env.local')

# Neo4j credentials from environment
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")

class Database:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    def close(self):
        self.driver.close()

    def get_mentor_matches(self, category: str, keywords: list):
        """
        Finds mentors based on category (Vertical) and specific keywords in their outcomes/bio.
        """
        query = """
        MATCH (m:Mentor)-[:HAS_EXPERTISE]->(e:Expertise)
        WHERE toLower(e.name) CONTAINS toLower($category)
        OR toLower(m.bio) CONTAINS toLower($category)
        OPTIONAL MATCH (m)-[:ACHIEVED]->(o:Outcome)
        WITH m, e, o,
             reduce(score = 0, word IN $keywords | 
                CASE WHEN toLower(m.bio) CONTAINS toLower(word) OR toLower(o.description) CONTAINS toLower(word) 
                THEN score + 1 ELSE score END) AS keyword_score
        WITH m, keyword_score, collect(DISTINCT o.description) as outcomes, collect(DISTINCT e.name) as expertise
        RETURN m.name as name, m.bio as bio, m.id as id, m.link as link, outcomes, expertise, keyword_score
        ORDER BY keyword_score DESC
        LIMIT 3
        """
        
        with self.driver.session() as session:
            result = session.run(query, category=category, keywords=keywords)
            return [record.data() for record in result]

    def add_mentor(self, mentor_data):
        """
        Adds a mentor and their relationships to the graph.
        """
        query = """
        MERGE (m:Mentor {id: $id})
        SET m.name = $name, m.bio = $bio, m.link = $link
        WITH m
        FOREACH (exp IN $expertise | 
            MERGE (e:Expertise {name: exp})
            MERGE (m)-[:HAS_EXPERTISE]->(e)
        )
        FOREACH (out IN $outcomes | 
            MERGE (o:Outcome {description: out})
            MERGE (m)-[:ACHIEVED]->(o)
        )
        """
        with self.driver.session() as session:
            session.run(query, **mentor_data)

    def verify_connection(self):
        try:
            with self.driver.session() as session:
                session.run("RETURN 1")
            return True
        except Exception as e:
            print(f"Database Connection Error: {e}")
            return False

    def save_file_content(self, filename: str, content: str, file_type: str):
        """
        Saves uploaded file content to Neo4j as a Document node.
        Returns the document ID.
        """
        import uuid
        doc_id = str(uuid.uuid4())[:8]
        
        query = """
        CREATE (d:Document {
            id: $doc_id,
            filename: $filename,
            content: $content,
            file_type: $file_type,
            created_at: datetime()
        })
        RETURN d.id as id
        """
        
        try:
            with self.driver.session() as session:
                result = session.run(query, doc_id=doc_id, filename=filename, content=content[:50000], file_type=file_type)
                record = result.single()
                return record["id"] if record else doc_id
        except Exception as e:
            print(f"Error saving to Neo4j: {e}")
            return doc_id

    def get_document(self, doc_id: str):
        """
        Retrieves a document by ID.
        """
        query = """
        MATCH (d:Document {id: $doc_id})
        RETURN d.filename as filename, d.content as content, d.file_type as file_type
        """
        
        with self.driver.session() as session:
            result = session.run(query, doc_id=doc_id)
            record = result.single()
            return record.data() if record else None

# Global instance
db = Database()
