// Example usage and testing of the prompt template
import { buildPrompt, generateAnswer } from './prompt-template'

// Example usage
export async function testPromptTemplate() {
  const question = "What are the main benefits of the new policy?"
  const context = `
[Source: policy_document.pdf]
The new policy introduces several key benefits:
1. Improved efficiency through streamlined processes
2. Cost reduction of up to 25%
3. Enhanced employee satisfaction
4. Better compliance with industry standards

[Source: implementation_guide.pdf]
Implementation timeline: 3 months
Training requirements: 2-day workshop for all staff
Expected ROI: 150% within first year
  `

  // Test the prompt building
  const prompt = buildPrompt(question, context)
  console.log('Generated Prompt:')
  console.log(prompt)
  console.log('\n' + '='.repeat(50) + '\n')

  // Test the answer generation (requires OpenAI API key)
  try {
    const answer = await generateAnswer(question, context)
    console.log('Generated Answer:')
    console.log(answer)
  } catch (error) {
    console.log('Error generating answer (likely missing API key):', error)
  }
}

// Example of how the prompt template handles insufficient context
export function testInsufficientContext() {
  const question = "What is the exact budget allocation for Q4?"
  const context = "The budget has been approved for the fiscal year."
  
  const prompt = buildPrompt(question, context)
  console.log('Prompt with insufficient context:')
  console.log(prompt)
}

// Example of how the prompt template handles specific questions
export function testSpecificQuestion() {
  const question = "What are the three main points from the policy document?"
  const context = `
[Source: policy_document.pdf]
1. All employees must complete safety training annually
2. Incident reports must be filed within 24 hours
3. Regular audits will be conducted quarterly
  `
  
  const prompt = buildPrompt(question, context)
  console.log('Prompt for specific question:')
  console.log(prompt)
} 