import { NextResponse } from "next/server";
import { getYouAPIClient } from "@/lib/you-api-client";
import { getUsageTracker, API_COSTS } from "@/lib/usage-tracker";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { insights, competitors } = body;

    const startTime = Date.now();
    const usageTracker = getUsageTracker();
    const youApi = getYouAPIClient();

    // Generate actions using You.com Custom Agents API
    const actionQuery = `
Based on the following competitive intelligence insights, generate 3-5 specific, actionable tasks for a product team:

Insights: ${insights || "Recent competitive activity detected"}
Competitors: ${competitors?.join(", ") || "Various competitors"}

For each action, provide:
1. Clear, specific title
2. Detailed description of what needs to be done
3. Priority level (Critical/High/Medium/Low)
4. Suggested assignee team (Product Team/Strategy Team/Marketing Team/Research Team/Sales Team)
5. Recommended timeline/due date
6. Relevant tags

Format as JSON array:
[
  {
    "title": "Action title",
    "description": "Detailed description",
    "priority": "High",
    "assignee": "Product Team", 
    "timeline": "1-2 weeks",
    "tags": ["tag1", "tag2"]
  }
]

Focus on actionable, specific tasks that directly address competitive threats or opportunities.
`;

    const chatResponse = await youApi.chat(actionQuery, {
      chat_mode: "custom",
      include_sources: false,
    });

    const responseTime = Date.now() - startTime;
    usageTracker.trackCall({
      api_name: "chat",
      endpoint: "/v1/chat",
      method: "POST",
      response_time_ms: responseTime,
      status_code: 200,
      success: true,
      cost_estimate: API_COSTS.chat,
    });

    // Parse the AI response
    let generatedActions;
    try {
      const jsonMatch = chatResponse.answer.match(/\[[\s\S]*\]/);
      if (jsonMatch) {
        generatedActions = JSON.parse(jsonMatch[0]);
      } else {
        throw new Error("No JSON array found in response");
      }
    } catch (parseError) {
      console.warn(
        "Failed to parse AI response, using fallback actions:",
        parseError
      );

      // Fallback actions based on common competitive intelligence needs
      generatedActions = [
        {
          title: "Analyze competitor feature updates",
          description:
            "Review recent product announcements and assess feature gaps in our offering",
          priority: "High",
          assignee: "Product Team",
          timeline: "1-2 weeks",
          tags: ["competitive-analysis", "product-strategy"],
        },
        {
          title: "Update competitive positioning materials",
          description:
            "Refresh sales materials and messaging based on latest competitive intelligence",
          priority: "Medium",
          assignee: "Marketing Team",
          timeline: "2-3 weeks",
          tags: ["marketing", "positioning"],
        },
        {
          title: "Monitor competitor pricing changes",
          description:
            "Track pricing updates and assess impact on our market position",
          priority: "Medium",
          assignee: "Strategy Team",
          timeline: "Ongoing",
          tags: ["pricing", "market-analysis"],
        },
      ];
    }

    // Convert to full action objects and save
    const actions = generatedActions.map((action: any, index: number) => ({
      id: Date.now() + index,
      title: action.title,
      description: action.description,
      priority: action.priority || "Medium",
      status: "Pending",
      assignee: action.assignee || "Product Team",
      dueDate: calculateDueDate(action.timeline),
      source: "AI Generated from Competitive Insights",
      tags: action.tags || [],
      created_at: new Date().toISOString(),
    }));

    // Add to actions storage (in production, save to database)
    // For now, we'll return them for the frontend to handle

    return NextResponse.json(
      {
        actions,
        generated_count: actions.length,
        processing_time_ms: Date.now() - startTime,
      },
      { status: 201 }
    );
  } catch (error) {
    console.error("Failed to generate actions:", error);

    // Track failed API call
    const usageTracker = getUsageTracker();
    usageTracker.trackCall({
      api_name: "chat",
      endpoint: "/v1/chat",
      method: "POST",
      response_time_ms: 0,
      status_code: 500,
      success: false,
      cost_estimate: 0,
    });

    return NextResponse.json(
      { error: "Failed to generate actions from insights" },
      { status: 500 }
    );
  }
}

function calculateDueDate(timeline: string): string {
  const now = new Date();
  let daysToAdd = 7; // Default 1 week

  if (timeline.includes("immediate") || timeline.includes("urgent")) {
    daysToAdd = 1;
  } else if (timeline.includes("1-2 weeks") || timeline.includes("week")) {
    daysToAdd = 10;
  } else if (timeline.includes("2-3 weeks")) {
    daysToAdd = 17;
  } else if (timeline.includes("month")) {
    daysToAdd = 30;
  } else if (timeline.includes("ongoing")) {
    daysToAdd = 90;
  }

  const dueDate = new Date(now.getTime() + daysToAdd * 24 * 60 * 60 * 1000);
  return dueDate.toISOString().split("T")[0];
}
