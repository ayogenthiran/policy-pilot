import { type NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
  try {
    const { message } = await request.json()

    if (!message || typeof message !== "string" || message.trim() === "") {
      return NextResponse.json({ message: "Message is required" }, { status: 400 })
    }

    // Simulate processing time
    await new Promise((resolve) => setTimeout(resolve, 1000))

    // Dummy response for now
    return NextResponse.json({
      message: 'Backend not connected. This is a placeholder response to your message: "' + message.trim() + '"',
    })
  } catch (error) {
    console.error("Chat error:", error)
    return NextResponse.json({ message: "An error occurred while processing your message" }, { status: 500 })
  }
}
