import { type NextRequest, NextResponse } from "next/server"
import pdfParse from 'pdf-parse';
import { RecursiveCharacterTextSplitter } from "@langchain/textsplitters";

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
    // insert doc processing here
  const arrayBuffer = await file.arrayBuffer(); //read file content into arraybuffer
  const buffer = Buffer.from(arrayBuffer); //convert arraybuffer to Buffer. pdfParse expect Buffer 

  try {
    const data = await pdfParse(buffer);
    const file_content = data.text
    const splitter = new RecursiveCharacterTextSplitter({
      chunkSize: 1024,
      chunkOverlap: 20
    });
    const output = await splitter.splitText(file_content);
    console.log(output[0])
    console.log("\n_________")
    return NextResponse.json({ textPreview: data.text.slice(0, 500) }); // return first 500 chars
  } catch (error) {
    console.error("Failed to parse PDF:", error);
    return NextResponse.json({ message: "Failed to read PDF" }, { status: 500 });
  }

    return NextResponse.json({
      message: `Successfully uploaded "${file.name}" (${(file.size / 1024).toFixed(1)} KB). File has been processed and is ready for use.`,
    })
  } catch (error) {
    console.error("Upload error:", error)
    return NextResponse.json({ message: "An error occurred while uploading the file" }, { status: 500 })
  }
}
