import { NextRequest, NextResponse } from 'next/server'
import { writeFile } from 'fs/promises'
import path from 'path'

export async function POST(request: NextRequest) {
  try {
    // Get form data
    const formData = await request.formData()
    const file = formData.get('pdf') as File

    // Check if file exists
    if (!file) {
      return NextResponse.json(
        { error: 'No file uploaded' },
        { status: 400 }
      )
    }

    // Validate file type
    if (file.type !== 'application/pdf') {
      return NextResponse.json(
        { error: 'This isn\'t a PDF file. Please upload a PDF file only.' },
        { status: 400 }
      )
    }

    // Validate file size (10MB limit)
    if (file.size > 10 * 1024 * 1024) {
      return NextResponse.json(
        { error: 'File size too large. Please upload a file smaller than 10MB.' },
        { status: 400 }
      )
    }

//     // Convert file to buffer
//     const bytes = await file.arrayBuffer()
//     const buffer = Buffer.from(bytes)

//     // Generate unique filename
//     const timestamp = Date.now()
//     const originalName = file.name.replace(/[^a-zA-Z0-9.-]/g, '_') // Sanitize filename
//     const fileName = `${timestamp}_${originalName}`

//     // Define path to public folder
//     const filePath = path.join(process.cwd(), 'public', 'uploads', fileName)

//     // Save file to public folder
//     await writeFile(filePath, buffer)

//     // Return success response with placeholder DB message
//     return NextResponse.json({
//       success: true,
//       message: `Db connection not established. ${fileName} stored in public folder`,
//       data: {
//         fileName: fileName,
//         originalName: file.name,
//         size: file.size,
//         uploadedAt: new Date().toISOString(),
//         path: `/uploads/${fileName}`
//       }
//     })

//   } catch (error) {
//     console.error('Upload error:', error)
    
    // Handle connection/server errors
    return NextResponse.json(
      { error: 'Connection issue with frontend. Please try again.' },
      { status: 500 }
    )
  }
}