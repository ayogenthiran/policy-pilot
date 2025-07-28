import { NextRequest, NextResponse } from 'next/server'
import { searchSimilarChunksEnhanced, getSearchStats } from '@/lib/vector-search'
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { query, fileName, topK = 5, matchThreshold = 0.7, useHybridSearch = false } = body

    if (!query) {
      return NextResponse.json({ error: 'Query is required' }, { status: 400 })
    }

    // First, let's check what's in the database for debugging
    const { data: allEmbeddings, error: dbError } = await supabase
      .from('embeddings')
      .select('id, content, file_name, embedding')
      .limit(5)

    console.log('Database check:', {
      totalEmbeddings: allEmbeddings?.length || 0,
      sampleEmbedding: allEmbeddings?.[0] ? {
        id: allEmbeddings[0].id,
        content: allEmbeddings[0].content?.substring(0, 100) + '...',
        file_name: allEmbeddings[0].file_name,
        embeddingType: typeof allEmbeddings[0].embedding,
        embeddingLength: Array.isArray(allEmbeddings[0].embedding) ? allEmbeddings[0].embedding.length : 'N/A'
      } : null
    })

    // Perform the search
    const results = await searchSimilarChunksEnhanced(query, {
      fileName,
      topK,
      matchThreshold,
      useHybridSearch
    })

    // Get search statistics
    const stats = await getSearchStats()

    return NextResponse.json({
      results,
      stats,
      searchOptions: {
        query,
        results: topK,
        threshold: matchThreshold,
        hybridSearch: useHybridSearch
      }
    })
  } catch (error) {
    console.error('Search API error:', error)
    return NextResponse.json(
      { error: 'Failed to perform search' },
      { status: 500 }
    )
  }
}

export async function GET(request: NextRequest) {
  try {
    // Get search statistics
    const stats = await getSearchStats()
    
    return NextResponse.json({
      success: true,
      stats
    })
  } catch (error) {
    console.error("Search stats API error:", error)
    return NextResponse.json({ 
      error: "An error occurred while fetching search statistics"
    }, { status: 500 })
  }
} 