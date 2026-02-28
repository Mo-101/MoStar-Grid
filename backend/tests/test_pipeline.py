import asyncio
import os
from datetime import datetime
from uuid import uuid4
from neo4j import GraphDatabase
from models.training import TrainingPipeline, TrainingStatus

logger = logging.getLogger("grid.training")

class GridTrainingPipeline:
    def __init__(self):
        """Initialize the GridTrainingPipeline with a Neo4j driver."""
        self.active_pipelines: Dict[str, TrainingPipeline] = {}
        uri = os.getenv("NEO4J_URI", "neo4j://localhost")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "password")
        self._driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        """Close the Neo4j driver."""
        self._driver.close()

    async def create_pipeline(self, name: str, config: Dict) -> TrainingPipeline:
        """Create a new training pipeline and store it in the database."""
        pipeline_id = str(uuid4())
        pipeline = TrainingPipeline(
            pipeline_id=pipeline_id,
            name=name,
            config=config,
            status=TrainingStatus.PENDING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.active_pipelines[pipeline_id] = pipeline

        with self._driver.session() as session:
            session.write_transaction(
                self._create_pipeline_tx,
                pipeline.pipeline_id,
                pipeline.name,
                json.dumps(pipeline.config),
                pipeline.status.value,
                pipeline.created_at.isoformat(),
                pipeline.updated_at.isoformat(),
            )
        return pipeline

    @staticmethod
    def _create_pipeline_tx(tx, pipeline_id, name, config, status, created_at, updated_at):
        """
        Create a new training pipeline node in the database.

        Parameters:
            tx (neo4j.Transaction): The transaction to write to.
            pipeline_id (str): The unique ID of the pipeline.
            name (str): The name of the pipeline.
            config (str): The configuration of the pipeline as a JSON string.
            status (int): The status of the pipeline as an integer.
            created_at (str): The timestamp when the pipeline was created in ISO format.
            updated_at (str): The timestamp when the pipeline was last updated in ISO format.
        """
        query = """
        CREATE (p:TrainingPipeline {
            pipeline_id: $pipeline_id,
            name: $name,
            config: $config,
            status: $status,
            created_at: $created_at,
            updated_at: $updated_at
        })
        """
        tx.run(query, pipeline_id=pipeline_id, name=name, config=config, status=status, created_at=created_at, updated_at=updated_at)

    async def start_pipeline(self, pipeline_id: str):
        """Start a training pipeline and update its status in the database."""
        pipeline = await self._get_pipeline_from_db(pipeline_id)
        if not pipeline:
            raise ValueError(f"Pipeline {pipeline_id} not found")

        pipeline.status = TrainingStatus.RUNNING
        pipeline.updated_at = datetime.utcnow()
        with self._driver.session() as session:
            session.write_transaction(self._update_pipeline_status_tx, pipeline_id, TrainingStatus.RUNNING.value)

        asyncio.create_task(self._monitor_pipeline(pipeline_id))

    @staticmethod
    def _update_pipeline_status_tx(tx, pipeline_id, status):
        """
        Update the status of a training pipeline in the database.

        :param tx: The Neo4j transaction to execute the query in.
        :param pipeline_id: The ID of the training pipeline to update.
        :param status: The new status of the training pipeline.
        """
        query = """
        MATCH (p:TrainingPipeline {pipeline_id: $pipeline_id})
        SET p.status = $status, p.updated_at = $updated_at
        """
        tx.run(query, pipeline_id=pipeline_id, status=status, updated_at=datetime.utcnow().isoformat())

    async def _get_pipeline_from_db(self, pipeline_id: str) -> Optional[TrainingPipeline]:
        """Retrieve a pipeline from the database."""
        with self._driver.session() as session:
            result = session.read_transaction(self._get_pipeline_tx, pipeline_id)
            if result:
                return TrainingPipeline(
                    pipeline_id=result["pipeline_id"],
                    name=result["name"],
                    config=json.loads(result["config"]),
                    status=TrainingStatus(result["status"]),
                    created_at=datetime.fromisoformat(result["created_at"]),
                    updated_at=datetime.fromisoformat(result["updated_at"]),
                )
            return None

    @staticmethod
    def _get_pipeline_tx(tx, pipeline_id):
        """
        Retrieve a pipeline from the database.

        :param tx: The Neo4j transaction to execute the query in.
        :param pipeline_id: The ID of the training pipeline to retrieve.
        :return: A single result containing the pipeline data, or None if no pipeline is found.
        """
        query = """
        MATCH (p:TrainingPipeline {pipeline_id: $pipeline_id})
        RETURN p.pipeline_id AS pipeline_id, p.name AS name, p.config AS config,
               p.status AS status, p.created_at AS created_at, p.updated_at AS updated_at
        """
        result = tx.run(query, pipeline_id=pipeline_id)
        return result.single()

    async def _monitor_pipeline(self, pipeline_id: str):
        """Monitor the progress of a running pipeline."""
        try:
            while True:
                pipeline = await self._get_pipeline_from_db(pipeline_id)
                if not pipeline or pipeline.status != TrainingStatus.RUNNING:
                    break
                await self._update_metrics(pipeline)
                await asyncio.sleep(10)
        except Exception as e:
            logger.error(f"Pipeline {pipeline_id} failed: {e}")
            with self._driver.session() as session:
                session.write_transaction(self._update_pipeline_status_tx, pipeline_id, TrainingStatus.FAILED.value)

    async def _update_metrics(self, pipeline: TrainingPipeline):
        """Update training metrics for the pipeline."""
        # Add logic to collect and update metrics
        pass
