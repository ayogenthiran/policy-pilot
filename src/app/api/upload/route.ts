import { type NextRequest, NextResponse } from "next/server"
import { RecursiveCharacterTextSplitter } from "@langchain/textsplitters";
import OpenAI from "openai";
import { createClient } from '@supabase/supabase-js'
import { v4 } from "uuid";
import pdf from 'pdf-parse';

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const file = formData.get("file") as File
    if (!file) {
      return NextResponse.json({ message: "No file uploaded" }, { status: 400 })
    }

    // Validate file type
    if (file.type !== "application/pdf") {
      return NextResponse.json({ message: "Only PDF files are supported" }, { status: 400 })
    }

    // Validate file size (optional - limit to 10MB)
    const maxSize = 10 * 1024 * 1024 // 10MB
    if (file.size > maxSize) {
      return NextResponse.json({ message: "File size must be less than 10MB" }, { status: 400 })
    }

    // Parse PDF content
    let file_content: string;
    try {
      console.log(`Starting PDF parsing for file: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`);
      
      const arrayBuffer = await file.arrayBuffer();
      const buffer = Buffer.from(arrayBuffer);
      const pdfData = await pdf(buffer);
      file_content = pdfData.text;
      
      // Validate that we extracted some text
      if (!file_content || file_content.trim().length === 0) {
        console.warn(`No text extracted from PDF: ${file.name}`);
        return NextResponse.json({ 
          message: "Could not extract text from PDF. The file might be empty, corrupted, or contain only images." 
        }, { status: 400 });
      }
      
      // Log parsing statistics
      console.log(`✅ Successfully extracted ${file_content.length} characters from PDF: ${file.name}`);
      console.log(`📄 PDF Info: ${pdfData.numpages} pages, ${pdfData.info?.Title || 'No title'}`);
      
    } catch (pdfError) {
      console.error("❌ PDF parsing error:", pdfError);
      return NextResponse.json({ 
        message: "Failed to parse PDF file. Please ensure the file is not corrupted and contains extractable text." 
      }, { status: 400 });
    }

    const openai = new OpenAI();
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
    const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
    
    if (!supabaseUrl || !supabaseKey) {
      return NextResponse.json({ message: "Missing Supabase configuration" }, { status: 500 });
    }
    
    const supabase = createClient(supabaseUrl, supabaseKey)
    //text splitter
    // Create text chunks for vector search
    const splitter = new RecursiveCharacterTextSplitter({
      chunkSize: 1024,
      chunkOverlap: 20
    });
    const output = await splitter.splitText(file_content);
    
    console.log(`📝 Created ${output.length} text chunks from ${file.name}`);
    
    if (output.length === 0) {
      return NextResponse.json({ 
        message: "Failed to create text chunks from the PDF content." 
      }, { status: 500 });
    }

    // Generate embeddings for each chunk
    console.log(`🔍 Generating embeddings for ${output.length} chunks...`);
    let successfulEmbeddings = 0;
    
    for (let i = 0; i < output.length; i++) {
      const chunk = output[i];
      try {
        const embedding = await openai.embeddings.create({
          model: "text-embedding-3-small",
          input: chunk,
          encoding_format: "float",
        });
        
        const { error } = await supabase
          .from('embeddings')
          .insert({ 
            id: v4(), 
            content: chunk,
            metadata: null,
            embedding: embedding.data[0]["embedding"], 
            file_name: file.name
          });
          
        if (error) {
          console.error(`❌ Failed to store embedding ${i + 1}:`, error);
        } else {
          successfulEmbeddings++;
        }
        
        // Log progress every 5 chunks
        if ((i + 1) % 5 === 0 || i === output.length - 1) {
          console.log(`📊 Progress: ${i + 1}/${output.length} chunks processed`);
        }
      } catch (embeddingError) {
        console.error(`❌ Failed to generate embedding for chunk ${i + 1}:`, embeddingError);
      }
    }
    
    console.log(`✅ Successfully processed ${successfulEmbeddings}/${output.length} chunks for ${file.name}`);

    return NextResponse.json({
      message: `Successfully uploaded "${file.name}" (${(file.size / 1024).toFixed(1)} KB). Extracted ${file_content.length} characters, created ${output.length} chunks, and processed ${successfulEmbeddings} embeddings. File is ready for use.`,
    })
  } catch (error) {
    console.error("Upload error:", error)
    return NextResponse.json({ message: "An error occurred while uploading the file" }, { status: 500 })
  }
}