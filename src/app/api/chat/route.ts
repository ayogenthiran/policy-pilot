import { NextRequest, NextResponse } from 'next/server';
import { ChatRequest, ChatResponse, ErrorResponse } from '../types';

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
    // Parse request body
    const body: ChatRequest = await request.json();

    // Input validation
    if (!body.question) {
      const errorResponse: ErrorResponse = {
        error: 'VALIDATION_ERROR',
        message: 'Question is required',
      };
      return NextResponse.json(errorResponse, {
        status: 400,
        headers: corsHeaders,
      });
    }

    if (typeof body.question !== 'string') {
      const errorResponse: ErrorResponse = {
        error: 'VALIDATION_ERROR',
        message: 'Question must be a string',
      };
      return NextResponse.json(errorResponse, {
        status: 400,
        headers: corsHeaders,
      });
    }

    if (body.question.trim().length === 0) {
      const errorResponse: ErrorResponse = {
        error: 'VALIDATION_ERROR',
        message: 'Question cannot be empty',
      };
      return NextResponse.json(errorResponse, {
        status: 400,
        headers: corsHeaders,
      });
    }

    // Optional fileId validation
    if (body.fileId && typeof body.fileId !== 'string') {
      const errorResponse: ErrorResponse = {
        error: 'VALIDATION_ERROR',
        message: 'FileId must be a string',
      };
      return NextResponse.json(errorResponse, {
        status: 400,
        headers: corsHeaders,
      });
    }

    // Placeholder response
    const response: ChatResponse = {
      answer: `This is a placeholder response for: ${body.question}`,
      sources: body.fileId ? [`Document ${body.fileId}`] : undefined,
    };

    return NextResponse.json(response, {
      status: 200,
      headers: corsHeaders,
    });

  } catch (error) {
    console.error('Chat API error:', error);

    // Handle JSON parsing errors
    if (error instanceof SyntaxError) {
      const errorResponse: ErrorResponse = {
        error: 'INVALID_JSON',
        message: 'Invalid JSON in request body',
      };
      return NextResponse.json(errorResponse, {
        status: 400,
        headers: corsHeaders,
      });
    }

    // Generic server error
    const errorResponse: ErrorResponse = {
      error: 'INTERNAL_ERROR',
      message: 'An unexpected error occurred',
    };
    return NextResponse.json(errorResponse, {
      status: 500,
      headers: corsHeaders,
    });
  }
} 