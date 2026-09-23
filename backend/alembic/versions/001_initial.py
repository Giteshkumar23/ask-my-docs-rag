"""Initial database migration — creates all tables and indexes.

Revision: 001
Depends on: -

Changes
-------
* Enables the ``pgvector`` extension.
* Creates tables: collections, documents, document_chunks, queries,
  query_results, citations, feedback, evaluation_runs, evaluation_results.
* Adds B-tree indexes on frequently queried columns.
* Adds an IVFFLAT vector index on ``document_chunks.embedding``.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

# --------------------------------------------------------------------------- #
# Revision identifiers
# --------------------------------------------------------------------------- #

revision: str = "001_initial"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


# --------------------------------------------------------------------------- #
# Upgrade
# --------------------------------------------------------------------------- #

def upgrade() -> None:
    # 1. Enable pgvector --------------------------------------------------- #
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # 2. collections -------------------------------------------------------- #
    op.create_table(
        "collections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(256), nullable=False, unique=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("color", sa.String(16), nullable=False, server_default="#3b82f6"),
        sa.Column("document_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("ix_collections_name", "collections", ["name"])
    op.create_index("ix_collections_created_at", "collections", ["created_at"])

    # 3. documents ---------------------------------------------------------- #
    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(512), nullable=False),
        sa.Column("original_filename", sa.String(512), nullable=False),
        sa.Column("file_path", sa.String(1024), nullable=False),
        sa.Column("file_type", sa.String(16), nullable=False),
        sa.Column("file_size", sa.Integer, nullable=False),
        sa.Column("num_pages", sa.Integer, nullable=True),
        sa.Column("num_chunks", sa.Integer, nullable=False, server_default="0"),
        sa.Column("status", sa.String(32), nullable=False, server_default="uploading"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("processing_time", sa.Float, nullable=True),
        sa.Column(
            "collection_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("collections.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("metadata", postgresql.JSON, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("ix_documents_name", "documents", ["name"])
    op.create_index("ix_documents_status", "documents", ["status"])
    op.create_index("ix_documents_file_type", "documents", ["file_type"])
    op.create_index("ix_documents_collection_id", "documents", ["collection_id"])
    op.create_index("ix_documents_created_at", "documents", ["created_at"])

    # 4. document_chunks ---------------------------------------------------- #
    op.create_table(
        "document_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("page_number", sa.Integer, nullable=True),
        sa.Column("section", sa.String(512), nullable=True),
        sa.Column("source_type", sa.String(16), nullable=False, server_default="text"),
        sa.Column("token_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("embedding", Vector(384), nullable=True),
        sa.Column("metadata", postgresql.JSON, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("ix_chunks_document_id", "document_chunks", ["document_id"])
    op.create_index("ix_chunks_chunk_index", "document_chunks", ["chunk_index"])
    # IVFFLAT vector index for approximate nearest-neighbour search
    op.execute(
        "CREATE INDEX ix_chunks_embedding_ivfflat "
        "ON document_chunks "
        "USING ivfflat (embedding vector_cosine_ops) "
        "WITH (lists = 100)"
    )

    # 5. queries ------------------------------------------------------------ #
    op.create_table(
        "queries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("question", sa.Text, nullable=False),
        sa.Column("answer", sa.Text, nullable=True),
        sa.Column(
            "collection_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("collections.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("retrieval_time", sa.Float, nullable=True),
        sa.Column("reranking_time", sa.Float, nullable=True),
        sa.Column("generation_time", sa.Float, nullable=True),
        sa.Column("total_time", sa.Float, nullable=True),
        sa.Column("num_chunks_retrieved", sa.Integer, nullable=True),
        sa.Column("confidence", sa.String(16), nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("ix_queries_status", "queries", ["status"])
    op.create_index("ix_queries_collection_id", "queries", ["collection_id"])
    op.create_index("ix_queries_created_at", "queries", ["created_at"])

    # 6. query_results ------------------------------------------------------ #
    op.create_table(
        "query_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "query_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("queries.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "chunk_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("document_chunks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("rank", sa.Integer, nullable=False),
        sa.Column("bm25_score", sa.Float, nullable=True),
        sa.Column("vector_score", sa.Float, nullable=True),
        sa.Column("reranker_score", sa.Float, nullable=True),
        sa.Column("fusion_score", sa.Float, nullable=True),
        sa.Column("used_in_answer", sa.Boolean, nullable=False, server_default="false"),
    )
    op.create_index("ix_query_results_query_id", "query_results", ["query_id"])
    op.create_index("ix_query_results_chunk_id", "query_results", ["chunk_id"])

    # 7. citations ---------------------------------------------------------- #
    op.create_table(
        "citations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "query_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("queries.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "chunk_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("document_chunks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("citation_number", sa.Integer, nullable=False),
        sa.Column("is_valid", sa.Boolean, nullable=False, server_default="true"),
    )
    op.create_index("ix_citations_query_id", "citations", ["query_id"])
    op.create_index("ix_citations_chunk_id", "citations", ["chunk_id"])

    # 8. feedback ----------------------------------------------------------- #
    op.create_table(
        "feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "query_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("queries.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("rating", sa.String(16), nullable=False),
        sa.Column("comment", sa.Text, nullable=True),
        sa.Column("failure_category", sa.String(64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("ix_feedback_query_id", "feedback", ["query_id"])
    op.create_index("ix_feedback_created_at", "feedback", ["created_at"])

    # 9. evaluation_runs ---------------------------------------------------- #
    op.create_table(
        "evaluation_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("dataset_name", sa.String(256), nullable=False),
        sa.Column("recall_at_5", sa.Float, nullable=True),
        sa.Column("precision_at_5", sa.Float, nullable=True),
        sa.Column("mrr", sa.Float, nullable=True),
        sa.Column("hit_rate", sa.Float, nullable=True),
        sa.Column("faithfulness", sa.Float, nullable=True),
        sa.Column("answer_relevance", sa.Float, nullable=True),
        sa.Column("context_relevance", sa.Float, nullable=True),
        sa.Column("citation_accuracy", sa.Float, nullable=True),
        sa.Column("citation_coverage", sa.Float, nullable=True),
        sa.Column("avg_retrieval_latency", sa.Float, nullable=True),
        sa.Column("avg_reranking_latency", sa.Float, nullable=True),
        sa.Column("avg_generation_latency", sa.Float, nullable=True),
        sa.Column("avg_total_latency", sa.Float, nullable=True),
        sa.Column("num_questions", sa.Integer, nullable=False, server_default="0"),
        sa.Column("passed", sa.Boolean, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("ix_eval_runs_name", "evaluation_runs", ["name"])
    op.create_index("ix_eval_runs_created_at", "evaluation_runs", ["created_at"])

    # 10. evaluation_results ----------------------------------------------- #
    op.create_table(
        "evaluation_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("evaluation_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("question", sa.Text, nullable=False),
        sa.Column("expected_answer", sa.Text, nullable=False),
        sa.Column("generated_answer", sa.Text, nullable=True),
        sa.Column("expected_sources", postgresql.JSON, nullable=True),
        sa.Column("retrieved_sources", postgresql.JSON, nullable=True),
        sa.Column("faithfulness_score", sa.Float, nullable=True),
        sa.Column("relevance_score", sa.Float, nullable=True),
        sa.Column("citation_score", sa.Float, nullable=True),
        sa.Column("retrieval_recall", sa.Float, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("ix_eval_results_run_id", "evaluation_results", ["run_id"])


# --------------------------------------------------------------------------- #
# Downgrade
# --------------------------------------------------------------------------- #

def downgrade() -> None:
    op.drop_table("evaluation_results")
    op.drop_table("evaluation_runs")
    op.drop_table("feedback")
    op.drop_table("citations")
    op.drop_table("query_results")
    op.drop_table("queries")
    op.drop_table("document_chunks")
    op.drop_table("documents")
    op.drop_table("collections")
    op.execute("DROP EXTENSION IF EXISTS vector")
