import { createClient } from '@/lib/supabase/client'
import OpenAI from 'openai'

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
})

const supabase = createClient()

// Generate embedding for a given text
async function generateEmbedding(text: string): Promise<number[]> {
  try {
    const response = await openai.embeddings.create({
      model: 'text-embedding-3-small',
      input: text,
      encoding_format: 'float',
    })
    
    return response.data[0].embedding
  } catch (error) {
    console.error('Error generating embedding:', error)
    throw new Error('Failed to generate embedding')
  }
}

// Main vector search function
export async function searchSimilarChunks(
  query: string, 
  fileName?: string, 
  topK: number = 5,
  matchThreshold: number = 0.7
) {
  try {
    // Generate query embedding
    const queryEmbedding = await generateEmbedding(query)
    
    // Try RPC first, then fallback to direct search
    try {
      const { data: chunks, error } = await supabase.rpc('match_embeddings', {
        query_embedding: queryEmbedding,
        match_threshold: matchThreshold,
        match_count: topK,
        filter_file_name: fileName || null
      })
      
      if (error) {
        console.error('Vector search RPC error:', error)
        // Fallback to direct vector search
        return await searchSimilarChunksDirect(query, fileName, topK, queryEmbedding, matchThreshold)
      }
      
      return chunks || []
    } catch (rpcError) {
      console.error('RPC not available, using direct search:', rpcError)
      // Fallback to direct vector search
      return await searchSimilarChunksDirect(query, fileName, topK, queryEmbedding)
    }
  } catch (error) {
    console.error('Vector search error:', error)
    throw new Error('Failed to perform vector search')
  }
}

// Direct vector search fallback (when RPC is not available)
async function searchSimilarChunksDirect(
  query: string, 
  fileName?: string, 
  topK: number = 5,
  queryEmbedding?: number[],
  matchThreshold: number = 0.7
) {
  try {
    // Generate embedding if not provided
    const embedding = queryEmbedding || await generateEmbedding(query)
    
    let queryBuilder = supabase
      .from('embeddings')
      .select('id, content, file_name, metadata, embedding')
    
    if (fileName) {
      queryBuilder = queryBuilder.eq('file_name', fileName)
    }
    
    const { data: allChunks, error } = await queryBuilder
    
    if (error || !allChunks) {
      console.error('Error fetching chunks:', error)
      return []
    }
    
    // Calculate cosine similarity and sort
    const chunksWithSimilarity = allChunks
      .map(chunk => {
        try {
          // Handle different embedding formats
          let chunkEmbedding: number[]
          if (Array.isArray(chunk.embedding)) {
            chunkEmbedding = chunk.embedding
          } else if (typeof chunk.embedding === 'string') {
            // If embedding is stored as a string, try to parse it
            try {
              chunkEmbedding = JSON.parse(chunk.embedding)
            } catch {
              console.error('Failed to parse embedding string:', chunk.embedding)
              return null
            }
          } else {
            console.error('Unknown embedding format:', typeof chunk.embedding)
            return null
          }
          
          // Check if vectors have the same length
          if (embedding.length !== chunkEmbedding.length) {
            console.error(`Vector length mismatch: query=${embedding.length}, chunk=${chunkEmbedding.length}`)
            return null
          }
          
          const similarity = calculateCosineSimilarity(embedding, chunkEmbedding)
          return {
            ...chunk,
            similarity
          }
        } catch (error) {
          console.error('Error processing chunk:', error)
          return null
        }
      })
      .filter(chunk => chunk !== null) // Remove null chunks
      .filter(chunk => chunk!.similarity >= matchThreshold) // Apply threshold
      .sort((a, b) => b!.similarity - a!.similarity)
      .slice(0, topK)
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
    .map(({ embedding, similarity, ...chunk }) => chunk) // Remove embedding from response
    
    return chunksWithSimilarity
  } catch (error) {
    console.error('Direct vector search error:', error)
    return []
  }
}

// Calculate cosine similarity between two vectors
function calculateCosineSimilarity(vecA: number[], vecB: number[]): number {
  if (vecA.length !== vecB.length) {
    throw new Error('Vectors must have the same length')
  }
  
  let dotProduct = 0
  let normA = 0
  let normB = 0
  
  for (let i = 0; i < vecA.length; i++) {
    dotProduct += vecA[i] * vecB[i]
    normA += vecA[i] * vecA[i]
    normB += vecB[i] * vecB[i]
  }
  
  normA = Math.sqrt(normA)
  normB = Math.sqrt(normB)
  
  if (normA === 0 || normB === 0) return 0
  
  return dotProduct / (normA * normB)
}

// Enhanced search with multiple strategies
export async function searchSimilarChunksEnhanced(
  query: string,
  options: {
    fileName?: string
    topK?: number
    matchThreshold?: number
    useHybridSearch?: boolean
    includeMetadata?: boolean
  } = {}
) {
  const {
    fileName,
    topK = 5,
    matchThreshold = 0.7,
    useHybridSearch = false
  } = options

  try {
    // Vector search
    const vectorResults = await searchSimilarChunks(query, fileName, topK, matchThreshold)
    
    if (!useHybridSearch) {
      return vectorResults
    }
    
    // Hybrid search: combine vector search with keyword search
    const keywordResults = await searchByKeywords(query, fileName, topK)
    
    // Merge and rank results
    const mergedResults = mergeSearchResults(vectorResults, keywordResults, topK)
    
    return mergedResults
  } catch (error) {
    console.error('Enhanced search error:', error)
    throw new Error('Failed to perform enhanced search')
  }
}

// Keyword-based search fallback
async function searchByKeywords(query: string, fileName?: string, topK: number = 5) {
  try {
    const keywords = query.toLowerCase().split(' ').filter(word => word.length > 2)
    
    let queryBuilder = supabase
      .from('embeddings')
      .select('id, content, file_name, metadata')
      .or(keywords.map(keyword => `content.ilike.%${keyword}%`).join(','))
      .limit(topK)
    
    if (fileName) {
      queryBuilder = queryBuilder.eq('file_name', fileName)
    }
    
    const { data: results, error } = await queryBuilder
    
    if (error) {
      console.error('Keyword search error:', error)
      return []
    }
    
    return results || []
  } catch (error) {
    console.error('Keyword search error:', error)
    return []
  }
}

// Merge and rank search results
function mergeSearchResults(
  vectorResults: Array<{ id: string; [key: string]: unknown }>,
  keywordResults: Array<{ id: string; [key: string]: unknown }>,
  topK: number
) {
  const merged = new Map()
  
  // Add vector results with high weight
  vectorResults.forEach((result, index) => {
    merged.set(result.id, {
      ...result,
      score: 1.0 - (index * 0.1), // Higher score for better vector matches
      source: 'vector'
    })
  })
  
  // Add keyword results with lower weight
  keywordResults.forEach((result, index) => {
    if (merged.has(result.id)) {
      // Boost existing result
      const existing = merged.get(result.id)
      merged.set(result.id, {
        ...existing,
        score: existing.score + 0.3,
        source: 'hybrid'
      })
    } else {
      merged.set(result.id, {
        ...result,
        score: 0.5 - (index * 0.05),
        source: 'keyword'
      })
    }
  })
  
  // Sort by score and return top K
  return Array.from(merged.values())
    .sort((a, b) => b.score - a.score)
    .slice(0, topK)
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    .map(({ score, source, ...result }) => result) // Remove scoring info from response
}

// Utility function to get search statistics
export async function getSearchStats() {
  try {
    const { count, error } = await supabase
      .from('embeddings')
      .select('*', { count: 'exact', head: true })
    
    if (error) {
      console.error('Error getting search stats:', error)
      return null
    }
    
    return {
      totalChunks: count,
      totalDocuments: await getUniqueDocumentCount()
    }
  } catch (error) {
    console.error('Error getting search stats:', error)
    return null
  }
}

// Get count of unique documents
async function getUniqueDocumentCount() {
  try {
    const { data, error } = await supabase
      .from('embeddings')
      .select('file_name')
    
    if (error) return 0
    
    const uniqueFiles = new Set(data?.map(chunk => chunk.file_name) || [])
    return uniqueFiles.size
  } catch (error) {
    console.error('Error getting unique document count:', error)
    return 0
  }
} 