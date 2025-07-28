#!/usr/bin/env tsx

/**
 * Prompt Template Demo
 * 
 * This script demonstrates the prompt template functionality
 * with various scenarios and use cases.
 */

import { 
  buildPrompt, 
  generateAnswer, 
  buildCustomPrompt, 
  generateCustomAnswer,
  validatePromptInputs 
} from '../src/lib/prompt-template'

async function runDemo() {
  console.log('🚀 Prompt Template Demo\n')
  
  // Example 1: Basic prompt generation
  console.log('1️⃣ Basic Prompt Generation')
  console.log('='.repeat(50))
  
  const question = "What are the key features of the new policy?"
  const context = `
[Source: policy_document.pdf]
The new policy includes the following key features:
- Remote work flexibility up to 3 days per week
- Enhanced health benefits package
- Professional development budget of $2,000 annually
- Flexible working hours between 7 AM and 7 PM

[Source: implementation_guide.pdf]
Implementation will begin on January 1st, 2024.
All employees will receive training on the new policy.
  `
  
  const prompt = buildPrompt(question, context)
  console.log('Generated Prompt:')
  console.log(prompt)
  console.log('\n')
  
  // Example 2: Input validation
  console.log('2️⃣ Input Validation')
  console.log('='.repeat(50))
  
  const validationTests = [
    { question: "", context: "Some context" },
    { question: "Valid question", context: "" },
    { question: "A".repeat(1001), context: "Some context" },
    { question: "Valid question", context: "A".repeat(8001) },
    { question: "Valid question", context: "Valid context" }
  ]
  
  validationTests.forEach((test, index) => {
    const result = validatePromptInputs(test.question, test.context)
    console.log(`Test ${index + 1}: ${result.isValid ? '✅ Valid' : '❌ Invalid'}`)
    if (!result.isValid) {
      console.log(`   Errors: ${result.errors.join(', ')}`)
    }
  })
  console.log('\n')
  
  // Example 3: Custom prompt with different instructions
  console.log('3️⃣ Custom Prompt Instructions')
  console.log('='.repeat(50))
  
  const customInstructions = `- Provide a detailed analysis of the policy
- Include specific numbers and dates when available
- Compare with industry standards if mentioned
- Suggest potential improvements based on the content
- Format the response in bullet points`
  
  const customPrompt = buildCustomPrompt(question, context, customInstructions)
  console.log('Custom Prompt with Detailed Instructions:')
  console.log(customPrompt)
  console.log('\n')
  
  // Example 4: Handling insufficient context
  console.log('4️⃣ Insufficient Context Handling')
  console.log('='.repeat(50))
  
  const insufficientQuestion = "What is the exact budget for Q4 2024?"
  const insufficientContext = "The budget has been approved for the fiscal year."
  
  const insufficientPrompt = buildPrompt(insufficientQuestion, insufficientContext)
  console.log('Prompt for Insufficient Context:')
  console.log(insufficientPrompt)
  console.log('\n')
  
  // Example 5: Custom answer generation (if API key is available)
  console.log('5️⃣ Custom Answer Generation')
  console.log('='.repeat(50))
  
  try {
    const customAnswer = await generateCustomAnswer(question, context, {
      maxTokens: 300,
      temperature: 0.2,
      customInstructions: "- Provide a concise summary in 2-3 bullet points"
    })
    console.log('Custom Answer:')
    console.log(customAnswer)
  } catch (error) {
    console.log('❌ Error generating custom answer (likely missing API key):')
    console.log(error)
  }
  
  console.log('\n✅ Demo completed!')
}

// Run the demo if this file is executed directly
if (require.main === module) {
  runDemo().catch(console.error)
}

export { runDemo } 