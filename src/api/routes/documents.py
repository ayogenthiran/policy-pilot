"""
Document management API routes for Policy Pilot RAG backend.
Handles document upload, processing, and management.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import JSONResponse

from src.core.logging import get_logger
from src.services.rag_service import RAGService
from src.services.file_service import FileService
from src.models.schemas import (
    DocumentUploadResponse,
    DocumentListResponse,
    DocumentDetailResponse,
    DocumentDeleteResponse,
    PaginationParams,
    FilterParams
)
from src.models.document import DocumentStatus
from src.utils.exceptions import FileUploadError, ValidationError, DocumentProcessingError
from src.utils.security import security_validator
from src.utils.metrics import structured_logger, metrics_collector

logger = get_logger(__name__)

# Create router
router = APIRouter(prefix="/api", tags=["documents"])


def get_rag_service() -> RAGService:
    """Dependency to get RAG service instance."""
    return RAGService()


def get_file_service() -> FileService:
    """Dependency to get file service instance."""
    return FileService()


@router.post(
    "/upload-document",
    response_model=DocumentUploadResponse,
    summary="Upload and process a document",
    description="Upload a document file and process it through the RAG pipeline"
)
async def upload_document(
    file: UploadFile = File(..., description="Document file to upload"),
    rag_service: RAGService = Depends(get_rag_service),
    file_service: FileService = Depends(get_file_service)
) -> DocumentUploadResponse:
    """
    Upload and process a document through the RAG pipeline.
    
    Args:
        file: Uploaded file
        rag_service: RAG service dependency
        file_service: File service dependency
        
    Returns:
        Document upload response with processing results
    """
    try:
        # Validate file
        file_content = await file.read()
        file_size = len(file_content)
        
        # Security validation
        security_validation = security_validator.validate_file_upload(
            filename=file.filename,
            file_size=file_size,
            content_type=file.content_type
        )
        
        if not security_validation['valid']:
            raise ValidationError(f"Security validation failed: {security_validation}")
        
        # Validate file using file service
        validation_result = file_service.validate_file(
            filename=file.filename,
            file_size=file_size,
            content_type=file.content_type
        )
        
        if not validation_result['valid']:
            raise ValidationError(f"File validation failed: {validation_result}")
        
        # Save uploaded file
        file_info = file_service.save_uploaded_file(
            file_content=file_content,
            filename=file.filename
        )
        
        # Process document through RAG pipeline
        import time
        start_time = time.time()
        
        processed_doc = rag_service.process_document(
            file_path=file_info['file_path'],
            filename=file.filename,
            document_id=file_info['document_id']
        )
        
        processing_time = time.time() - start_time
        
        # Record metrics
        metrics_collector.record_metric(
            operation="document_processing",
            duration=processing_time,
            success=processed_doc.status == DocumentStatus.COMPLETED,
            metadata={
                "filename": file.filename,
                "file_size": file_size,
                "chunks_created": processed_doc.chunks_count,
                "document_id": processed_doc.document_id
            }
        )
        
        # Log structured processing
        structured_logger.log_document_processing(
            document_id=processed_doc.document_id,
            filename=file.filename,
            chunks_count=processed_doc.chunks_count,
            duration=processing_time,
            success=processed_doc.status == DocumentStatus.COMPLETED,
            error=processed_doc.error_message if processed_doc.status != DocumentStatus.COMPLETED else None
        )
        
        # Create response
        if processed_doc.status == DocumentStatus.COMPLETED:
            response = DocumentUploadResponse(
                success=True,
                message="Document uploaded and processed successfully",
                document_id=processed_doc.document_id,
                status=processed_doc.status,
                chunks_created=processed_doc.chunks_count,
                processing_time=processed_doc.processing_time_seconds,
                file_size=file_size,
                filename=file.filename
            )
        else:
            response = DocumentUploadResponse(
                success=False,
                message="Document upload failed",
                document_id=processed_doc.document_id,
                status=processed_doc.status,
                chunks_created=0,
                error=processed_doc.error_message,
                file_size=file_size,
                filename=file.filename
            )
        
        logger.info(f"Document upload completed: {file.filename} - {processed_doc.status}")
        return response
        
    except ValidationError as e:
        logger.error(f"File validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except FileUploadError as e:
        logger.error(f"File upload error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except DocumentProcessingError as e:
        logger.error(f"Document processing error: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during document upload: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/documents",
    response_model=DocumentListResponse,
    summary="List documents",
    description="Get a paginated list of processed documents"
)
async def list_documents(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    status: Optional[DocumentStatus] = Query(None, description="Filter by document status"),
    file_type: Optional[str] = Query(None, description="Filter by file type"),
    rag_service: RAGService = Depends(get_rag_service)
) -> DocumentListResponse:
    """
    Get a paginated list of documents.
    
    Args:
        page: Page number
        page_size: Items per page
        status: Filter by document status
        file_type: Filter by file type
        rag_service: RAG service dependency
        
    Returns:
        Paginated list of documents
    """
    try:
        # Get document statistics
        stats = rag_service.get_document_statistics()
        total_documents = stats.get('documents', {}).get('total_documents', 0)
        
        # Calculate pagination
        total_pages = (total_documents + page_size - 1) // page_size
        has_next = page < total_pages
        has_previous = page > 1
        
        # For now, return basic response (in a real implementation, you'd query the database)
        documents = []  # This would be populated from the database
        
        response = DocumentListResponse(
            success=True,
            message=f"Retrieved {len(documents)} documents",
            documents=documents,
            total_count=total_documents,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=has_next,
            has_previous=has_previous
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to list documents")


@router.get(
    "/documents/{document_id}",
    response_model=DocumentDetailResponse,
    summary="Get document details",
    description="Get detailed information about a specific document"
)
async def get_document(
    document_id: str,
    rag_service: RAGService = Depends(get_rag_service)
) -> DocumentDetailResponse:
    """
    Get detailed information about a document.
    
    Args:
        document_id: Document identifier
        rag_service: RAG service dependency
        
    Returns:
        Document details
    """
    try:
        # This would typically query the database for document details
        # For now, return a placeholder response
        response = DocumentDetailResponse(
            success=True,
            message="Document details retrieved",
            document=None,  # This would be populated from the database
            chunks=[]
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting document {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get document details")


@router.delete(
    "/documents/{document_id}",
    response_model=DocumentDeleteResponse,
    summary="Delete document",
    description="Delete a document and all its chunks from the system"
)
async def delete_document(
    document_id: str,
    rag_service: RAGService = Depends(get_rag_service)
) -> DocumentDeleteResponse:
    """
    Delete a document and all its chunks.
    
    Args:
        document_id: Document identifier
        rag_service: RAG service dependency
        
    Returns:
        Deletion result
    """
    try:
        # Delete document using RAG service
        result = rag_service.delete_document(document_id)
        
        if result['success']:
            response = DocumentDeleteResponse(
                success=True,
                message="Document deleted successfully",
                document_id=document_id,
                chunks_deleted=0  # This would be populated from the result
            )
        else:
            response = DocumentDeleteResponse(
                success=False,
                message=result.get('message', 'Failed to delete document'),
                document_id=document_id,
                chunks_deleted=0
            )
        
        logger.info(f"Document deletion: {document_id} - {result['success']}")
        return response
        
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete document")


@router.get(
    "/documents/{document_id}/chunks",
    summary="Get document chunks",
    description="Get all chunks for a specific document"
)
async def get_document_chunks(
    document_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    rag_service: RAGService = Depends(get_rag_service)
) -> JSONResponse:
    """
    Get chunks for a specific document.
    
    Args:
        document_id: Document identifier
        page: Page number
        page_size: Items per page
        rag_service: RAG service dependency
        
    Returns:
        Document chunks
    """
    try:
        # This would typically query the database for document chunks
        # For now, return a placeholder response
        chunks = []  # This would be populated from the database
        
        response = {
            "success": True,
            "message": f"Retrieved {len(chunks)} chunks for document {document_id}",
            "document_id": document_id,
            "chunks": chunks,
            "page": page,
            "page_size": page_size,
            "total_chunks": len(chunks)
        }
        
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(f"Error getting chunks for document {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get document chunks")


@router.get(
    "/documents/stats",
    summary="Get document statistics",
    description="Get comprehensive document statistics"
)
async def get_document_stats(
    rag_service: RAGService = Depends(get_rag_service)
) -> JSONResponse:
    """
    Get document statistics.
    
    Args:
        rag_service: RAG service dependency
        
    Returns:
        Document statistics
    """
    try:
        stats = rag_service.get_document_statistics()
        
        response = {
            "success": True,
            "message": "Document statistics retrieved",
            "statistics": stats
        }
        
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(f"Error getting document statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get document statistics")
