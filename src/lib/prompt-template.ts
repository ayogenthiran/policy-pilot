import OpenAI from 'openai'

// Lazy initialization of OpenAI client
let openai: OpenAI | null = null

function getOpenAIClient(): OpenAI {
  if (!openai) {
    openai = new OpenAI({
      apiKey: process.env.OPENAI_API_KEY,
    })
  }
  return openai
}

export function buildPrompt(question: string, context: string): string {
  return `You are a helpful assistant that answers questions based solely on the provided document context.

INSTRUCTIONS:
- Answer the question using only the information provided in the context below
- If the context doesn't contain enough information to answer the question, say "I don't have enough information in the provided documents to answer this question"
- Be specific and cite relevant details from the context
- Keep your answer concise but complete
- Do not make assumptions or add information not present in the context

CONTEXT:
${context}

QUESTION: ${question}

ANSWER:`
}

export async function generateAnswer(question: string, context: string): Promise<string> {
  const prompt = buildPrompt(question, context)
  
  const response = await getOpenAIClient().chat.completions.create({
    model: 'gpt-4o-mini',
    messages: [{ role: 'user', content: prompt }],
    max_tokens: 500,
    temperature: 0.1, // Low temperature for consistent, factual responses
  })
  
  return response.choices[0].message.content || 'No response generated'
}

// Utility function to build custom prompts with different instructions
export function buildCustomPrompt(
  question: string, 
  context: string, 
  customInstructions?: string
): string {
  const defaultInstructions = `- Answer the question using only the information provided in the context below
- If the context doesn't contain enough information to answer the question, say "I don't have enough information in the provided documents to answer this question"
- Be specific and cite relevant details from the context
- Keep your answer concise but complete
- Do not make assumptions or add information not present in the context`

  const instructions = customInstructions || defaultInstructions

  return `You are a helpful assistant that answers questions based solely on the provided document context.

INSTRUCTIONS:
${instructions}

CONTEXT:
${context}

QUESTION: ${question}

ANSWER:`
}

// Utility function to generate answers with custom parameters
export async function generateCustomAnswer(
  question: string, 
  context: string, 
  options: {
    maxTokens?: number
    temperature?: number
    customInstructions?: string
  } = {}
): Promise<string> {
  const {
    maxTokens = 500,
    temperature = 0.1,
    customInstructions
  } = options

  const prompt = customInstructions 
    ? buildCustomPrompt(question, context, customInstructions)
    : buildPrompt(question, context)
  
  const response = await getOpenAIClient().chat.completions.create({
    model: 'gpt-4o-mini',
    messages: [{ role: 'user', content: prompt }],
    max_tokens: maxTokens,
    temperature: temperature,
  })
  
  return response.choices[0].message.content || 'No response generated'
}

// Utility function to validate prompt inputs
export function validatePromptInputs(question: string, context: string): {
  isValid: boolean
  errors: string[]
} {
  const errors: string[] = []

  if (!question || question.trim() === '') {
    errors.push('Question is required and cannot be empty')
  }

  if (!context || context.trim() === '') {
    errors.push('Context is required and cannot be empty')
  }

  if (question.length > 1000) {
    errors.push('Question is too long (max 1000 characters)')
  }

  if (context.length > 8000) {
    errors.push('Context is too long (max 8000 characters)')
  }

  return {
    isValid: errors.length === 0,
    errors
  }
} 