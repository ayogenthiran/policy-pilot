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
    // For now, we'll just return a placeholder response
    // The actual file upload implementation will be handled by teammate
    
    // Generate a placeholder file ID (in real implementation, this would be generated after processing the file)
    const fileId = `file_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    const response: UploadResponse = {
      fileId: fileId,
      status: 'uploaded',
    };

    return NextResponse.json(response, {
      status: 200,
      headers: corsHeaders,
    });

  } catch (error) {
    console.error('Upload API error:', error);

    // Generic server error
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