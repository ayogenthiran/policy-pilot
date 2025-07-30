# Prompt Template Design

This document describes the prompt template design implemented in the Policy Pilot application for generating AI responses based on document context.

## Overview

The prompt template is designed to ensure that AI responses are:
- Based solely on provided document context
- Factual and consistent
- Concise but complete
- Properly cited with sources

## Implementation

### Core Functions

#### `buildPrompt(question: string, context: string): string`

Builds a structured prompt that instructs the AI to:
- Answer questions using only the provided context
- Acknowledge when insufficient information is available
- Be specific and cite relevant details
- Avoid assumptions or external knowledge

#### `generateAnswer(question: string, context: string): Promise<string>`

Generates an AI response using the built prompt with:
- Model: `gpt-4o-mini`
- Max tokens: 500
- Temperature: 0.1 (low for consistent, factual responses)

## Prompt Structure

The generated prompt follows this structure:

```
You are a helpful assistant that answers questions based solely on the provided document context.

INSTRUCTIONS:
- Answer the question using only the information provided in the context below
- If the context doesn't contain enough information to answer the question, say "I don't have enough information in the provided documents to answer this question"
- Be specific and cite relevant details from the context
- Keep your answer concise but complete
- Do not make assumptions or add information not present in the context

CONTEXT:
[Source: document1.pdf]
Content from document 1...

[Source: document2.pdf]
Content from document 2...

QUESTION: What is the user's question?

ANSWER:
```

## Key Features

### 1. Context-Only Responses
The AI is explicitly instructed to use only the provided context, preventing hallucination and ensuring accuracy.

### 2. Insufficient Information Handling
When the context doesn't contain enough information, the AI will explicitly state this rather than making assumptions.

### 3. Source Citation
The prompt structure includes source information, allowing the AI to cite specific documents in its responses.

### 4. Consistent Output
Low temperature (0.1) ensures consistent, factual responses across multiple queries.

## Usage in Policy Pilot

The prompt template is integrated into the chat API route (`/api/chat`) and is used to:

1. **Search for relevant documents** using vector search
2. **Build context** from search results
3. **Generate responses** using the structured prompt
4. **Return answers** with source citations

## Example Usage

```typescript
import { generateAnswer } from '@/lib/prompt-template'

const question = "What are the main benefits of the new policy?"
const context = `
[Source: policy_document.pdf]
The new policy introduces several key benefits:
1. Improved efficiency through streamlined processes
2. Cost reduction of up to 25%
3. Enhanced employee satisfaction
`

const answer = await generateAnswer(question, context)
```

## Testing

The `examples/prompt-template-demo.ts` file contains examples demonstrating:
- Basic prompt generation
- Handling insufficient context
- Specific question answering
- Error handling

## Benefits

1. **Consistency**: Standardized prompt structure ensures consistent AI behavior
2. **Accuracy**: Context-only responses reduce hallucination
3. **Transparency**: Clear instructions about information limitations
4. **Maintainability**: Centralized prompt logic for easy updates
5. **Reliability**: Low temperature ensures factual, consistent responses 