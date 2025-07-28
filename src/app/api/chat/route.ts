import { type NextRequest, NextResponse } from "next/server"
import { searchSimilarChunksEnhanced } from '@/lib/vector-search'
import { generateAnswer, validatePromptInputs } from '@/lib/prompt-template'
import { ChatRequest, ChatResponse } from '../types'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    console.log('Received request body:', body)
    
    const { message, question, fileName, useHybridSearch = false, matchThreshold = 0.1 }: ChatRequest = body

    // Support both 'message' and 'question' for backward compatibility
    const userQuestion = message || question

    // Basic validation for question
    if (!userQuestion || typeof userQuestion !== "string" || userQuestion.trim() === "") {
      return NextResponse.json({ 
        message: "Question is required and cannot be empty" 
      }, { status: 400 })
    }

    // Validate question length
    if (userQuestion.length > 1000) {
      return NextResponse.json({ 
        message: "Question is too long (max 1000 characters)" 
      }, { status: 400 })
    }

    console.log(`Processing question: "${userQuestion}"`)

    // Step 1: Search for relevant document chunks
    const searchResults = await searchSimilarChunksEnhanced(userQuestion.trim(), {
      fileName,
      topK: 5,
      matchThreshold, // Use the threshold from request
      useHybridSearch,
      includeMetadata: true
    })

    console.log(`Found ${searchResults.length} relevant chunks`)

    // Step 2: Prepare context from search results
    let context = ""
    let sources: string[] = []

    if (searchResults.length > 0) {
      // Combine relevant chunks into context
      context = searchResults
        .map((result: any, index: number) => {
          const source = result.file_name || `Document ${index + 1}`
          if (!sources.includes(source)) {
            sources.push(source)
          }
          return `[Source: ${source}]\n${result.content}\n`
        })
        .join('\n---\n')
    } else {
      context = "No relevant documents found in the knowledge base."
    }

    // Validate the final context
    const contextValidation = validatePromptInputs(userQuestion.trim(), context)
    if (!contextValidation.isValid) {
      return NextResponse.json({ 
        message: "Context validation failed", 
        errors: contextValidation.errors 
      }, { status: 400 })
    }

    // Step 3: Generate AI response using the new prompt template
    const answer = await generateAnswer(userQuestion.trim(), context)

    // Step 4: Return the response
    const response: ChatResponse = {
      answer: answer,
      sources: sources.length > 0 ? sources : undefined
    }

    console.log(`Generated response with ${sources.length} sources`)

    return NextResponse.json(response)

  } catch (error) {
    console.error("Chat API error:", error)
    
    // Handle specific OpenAI errors
    if (error instanceof Error) {
      if (error.message.includes('API key')) {
        return NextResponse.json({ 
          message: "OpenAI API key not configured. Please check your environment variables." 
        }, { status: 500 })
      }
      if (error.message.includes('rate limit')) {
        return NextResponse.json({ 
          message: "Rate limit exceeded. Please try again in a moment." 
        }, { status: 429 })
      }
    }

    return NextResponse.json({ 
      message: "An error occurred while processing your question. Please try again." 
    }, { status: 500 })
  }
}