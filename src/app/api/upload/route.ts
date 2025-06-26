import { NextRequest, NextResponse } from 'next/server';
import { UploadResponse, ErrorResponse } from '../types';

// CORS headers
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: corsHeaders,
  });
}

export async function POST(request: NextRequest) {
  try {
    // Simulate different upload scenarios for testing
    // In real implementation, this would be actual file processing logic
    
    // Get content type to validate file upload
    const contentType = request.headers.get('content-type');
    
    // Simulate upload validation failures
    if (contentType && contentType.includes('application/json')) {
      // If JSON is sent instead of file, return validation error
      const errorResponse: ErrorResponse = {
        error: 'INVALID_FILE_TYPE',
        message: 'No file provided. Please upload a valid document file.',
      };
      return NextResponse.json(errorResponse, {
        status: 400,
        headers: corsHeaders,
      });
    }

    // Simulate random upload failures for testing (20% chance)
    const shouldSimulateFailure = Math.random() < 0.2;
    
    if (shouldSimulateFailure) {
      // Simulate different types of upload failures
      const failureTypes = [
        {
          error: 'FILE_TOO_LARGE',
          message: 'File size exceeds maximum limit of 10MB',
          status: 413
        },
        {
          error: 'UNSUPPORTED_FILE_TYPE',
          message: 'File type not supported. Please upload PDF, DOC, or TXT files only.',
          status: 400
        },
        {
          error: 'UPLOAD_FAILED',
          message: 'File upload failed due to network error. Please try again.',
          status: 500
        },
        {
          error: 'VIRUS_DETECTED',
          message: 'File upload blocked. Potential security threat detected.',
          status: 400
        }
      ];

      const randomFailure = failureTypes[Math.floor(Math.random() * failureTypes.length)];
      
      console.log('Simulated upload failure:', randomFailure.error);
      
      const errorResponse: ErrorResponse = {
        error: randomFailure.error,
        message: randomFailure.message,
      };
      
      return NextResponse.json(errorResponse, {
        status: randomFailure.status,
        headers: corsHeaders,
      });
    }

    // Simulate successful upload
    // Generate a more realistic file ID (in real implementation, this would be generated after processing the file)
    const fileId = `file_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    const response: UploadResponse = {
      fileId: fileId,
      status: 'uploaded',
    };

    console.log('Simulated successful upload:', fileId);

    return NextResponse.json(response, {
      status: 200,
      headers: corsHeaders,
    });

  } catch (error) {
    console.error('Upload API error:', error);

    // Handle specific error types
    if (error instanceof Error) {
      // File parsing or processing errors
      if (error.name === 'PayloadTooLargeError') {
        const errorResponse: ErrorResponse = {
          error: 'FILE_TOO_LARGE',
          message: 'File size exceeds maximum limit',
        };
        return NextResponse.json(errorResponse, {
          status: 413,
          headers: corsHeaders,
        });
      }
    }

    // Generic server error for unexpected issues
    const errorResponse: ErrorResponse = {
      error: 'INTERNAL_ERROR',
      message: 'An unexpected error occurred during upload',
    };
    return NextResponse.json(errorResponse, {
      status: 500,
      headers: corsHeaders,
    });
  }
} 