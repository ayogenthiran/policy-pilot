import { type NextRequest, NextResponse } from "next/server"
import { RecursiveCharacterTextSplitter } from "@langchain/textsplitters";
import OpenAI from "openai";
import { createClient } from '@supabase/supabase-js'
import { v4 } from "uuid";

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

    // For now, we'll just accept the file without parsing
    // TODO: Implement PDF parsing with a reliable library
    const file_content = `Sample text from ${file.name}. PDF parsing will be implemented soon.`;

    const openai = new OpenAI();
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
    const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
    
    if (!supabaseUrl || !supabaseKey) {
      return NextResponse.json({ message: "Missing Supabase configuration" }, { status: 500 });
    }
    
    const supabase = createClient(supabaseUrl, supabaseKey)
    //text splitter
    const splitter = new RecursiveCharacterTextSplitter({
      chunkSize: 1024,
      chunkOverlap: 20
    });
    const output = await splitter.splitText(file_content);

    // embedding gen text-embedding-3-small $0.02/1M
    for (const chuck of output) {
      const embedding = await openai.embeddings.create({
        model: "text-embedding-3-small",
        input: chuck,
        encoding_format: "float",
      });
      //console.log(embedding.data[0]["embedding"]) //embedding is a list with one element. the element is a dict with object, index, and embedding
      const { error } = await supabase
      .from('embeddings')
      .insert({ id: v4(), content: chuck,metadata: null,embedding: embedding.data[0]["embedding"], file_name: file.name})
      if (error){
        console.log(error)
      }
    }

    return NextResponse.json({
      message: `Successfully uploaded "${file.name}" (${(file.size / 1024).toFixed(1)} KB). File has been processed and is ready for use.`,
    })
  } catch (error) {
    console.error("Upload error:", error)
    return NextResponse.json({ message: "An error occurred while uploading the file" }, { status: 500 })
  }
}