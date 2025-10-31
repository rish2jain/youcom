import { NextResponse } from "next/server";

// In-memory storage for demo (replace with database in production)
let userActions: any[] = [];

export async function GET() {
  try {
    return NextResponse.json(userActions);
  } catch (error) {
    console.error("Failed to fetch actions:", error);
    return NextResponse.json(
      { error: "Failed to fetch actions" },
      { status: 500 }
    );
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json();

    const newAction = {
      id: Date.now(),
      title: body.title,
      description: body.description,
      priority: body.priority || "Medium",
      status: body.status || "Pending",
      assignee: body.assignee || "Unassigned",
      dueDate:
        body.dueDate ||
        new Date(Date.now() + 7 * 24 * 60 * 60 * 1000)
          .toISOString()
          .split("T")[0],
      source: body.source || "Manual Entry",
      tags: body.tags || [],
      created_at: new Date().toISOString(),
    };

    userActions.push(newAction);

    return NextResponse.json(newAction, { status: 201 });
  } catch (error) {
    console.error("Failed to create action:", error);
    return NextResponse.json(
      { error: "Failed to create action" },
      { status: 500 }
    );
  }
}
