"""Document service for CRUD operations"""
from sqlalchemy.orm import Session
from app.models.document import Document
from app.models.trip import Trip
from app.schemas.document import DocumentCreate, DocumentUpdate
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class DocumentService:
    """Service for document management"""

    def __init__(self, db: Session):
        self.db = db

    def get_documents_by_trip(
        self,
        trip_id: UUID,
        user_id: UUID,
        doc_type: Optional[str] = None
    ) -> tuple[List[Document], int]:
        """
        Get all documents for a trip

        Returns:
            Tuple of (documents list, total count)
        """
        # Verify trip belongs to the user
        trip = self.db.query(Trip).filter(
            Trip.id == trip_id,
            Trip.user_id == user_id
        ).first()

        if not trip:
            return [], 0

        query = self.db.query(Document).filter(Document.trip_id == trip_id)

        # Filter by type if provided
        if doc_type:
            query = query.filter(Document.type == doc_type)

        total = query.count()
        documents = query.order_by(Document.created_at.desc()).all()

        return documents, total

    def get_document_by_id(
        self,
        document_id: UUID,
        user_id: UUID
    ) -> Optional[Document]:
        """Get a specific document by ID (with user ownership check via trip)"""
        document = self.db.query(Document).filter(Document.id == document_id).first()

        if not document:
            return None

        # Verify ownership through trip
        trip = self.db.query(Trip).filter(
            Trip.id == document.trip_id,
            Trip.user_id == user_id
        ).first()

        return document if trip else None

    def create_document(
        self,
        user_id: UUID,
        document_data: DocumentCreate
    ) -> Optional[Document]:
        """Create a new document"""
        # Verify trip ownership
        trip = self.db.query(Trip).filter(
            Trip.id == document_data.trip_id,
            Trip.user_id == user_id
        ).first()

        if not trip:
            return None

        db_document = Document(
            trip_id=document_data.trip_id,
            type=document_data.type.value,
            name=document_data.name,
            file_url=document_data.file_url,
            file_type=document_data.file_type.value,
            notes=document_data.notes
        )

        self.db.add(db_document)
        self.db.commit()
        self.db.refresh(db_document)

        return db_document

    def update_document(
        self,
        document_id: UUID,
        user_id: UUID,
        document_data: DocumentUpdate
    ) -> Optional[Document]:
        """Update an existing document"""
        document = self.get_document_by_id(document_id, user_id)
        if not document:
            return None

        # Update only provided fields
        update_data = document_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "type" and value is not None:
                setattr(document, field, value.value)
            else:
                setattr(document, field, value)

        document.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(document)

        return document

    def delete_document(self, document_id: UUID, user_id: UUID) -> bool:
        """
        Delete a document

        Returns:
            True if deleted, False if not found
        """
        document = self.get_document_by_id(document_id, user_id)
        if not document:
            return False

        self.db.delete(document)
        self.db.commit()

        return True

    def get_documents_grouped_by_type(
        self,
        trip_id: UUID,
        user_id: UUID
    ) -> List[dict]:
        """
        Get documents grouped by type

        Returns:
            List of {type, documents, count}
        """
        # Verify trip belongs to the user
        trip = self.db.query(Trip).filter(
            Trip.id == trip_id,
            Trip.user_id == user_id
        ).first()

        if not trip:
            return []

        documents = self.db.query(Document).filter(
            Document.trip_id == trip_id
        ).order_by(Document.type, Document.created_at.desc()).all()

        # Group by type
        grouped = {}
        for doc in documents:
            if doc.type not in grouped:
                grouped[doc.type] = []
            grouped[doc.type].append(doc)

        return [
            {
                "type": doc_type,
                "documents": docs,
                "count": len(docs)
            }
            for doc_type, docs in grouped.items()
        ]
