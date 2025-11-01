"""
API endpoints for enhancement features: timeline, evidence badges, playbooks, and action tracking.
"""
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ..database import get_db
from ..models.impact_card import ImpactCard
from ..services.insight_timeline_service import InsightTimelineService
from ..services.evidence_badge_service import EvidenceBadgeService
from ..services.personal_playbook_service import PersonalPlaybookService
from ..services.action_tracker_service import ActionTrackerService
from ..schemas.insight_timeline import InsightDeltaResponse, InsightTimeline
from ..schemas.evidence_badge import EvidenceBadgeResponse, ConfidenceMetrics
from ..schemas.personal_playbook import (
    PersonaPreset, UserPlaybook, PlaybookRecommendation, 
    PlaybookExecutionPlan, PlaybookResults
)
from ..schemas.action_tracker import (
    ActionItem, ActionItemCreate, ActionItemUpdate, ActionSummary,
    ActionBoard, ActionBoardView, ActionInsights, ActionBoardCreate
)

# Request/Response schemas for evidence badge creation
class EvidenceBadgeCreateRequest(BaseModel):
    entity_type: str = Field(..., description="Type: impact_card, insight, recommendation")
    entity_id: int
    sources: List[Dict[str, Any]]
    confidence_override: Optional[float] = Field(None, ge=0.0, le=100.0)

class EvidenceBadgeCreateResponse(BaseModel):
    id: int
    confidence: float

# Demo setup response schema
class DemoSetupResponse(BaseModel):
    message: str
    personas_count: int
    demo_playbook_id: Optional[int] = None
    demo_board_id: int

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/enhancements", tags=["enhancements"])

# Insight Timeline & Delta Highlights

@router.get("/timeline/{company_name}/latest", response_model=Optional[InsightTimeline])
async def get_latest_timeline(
    company_name: str,
    db: Session = Depends(get_db)
):
    """Get the latest timeline entry for a company."""
    service = InsightTimelineService(db)
    return await service.get_latest_timeline(company_name)

@router.get("/timeline/{company_name}/history", response_model=List[InsightTimeline])
async def get_timeline_history(
    company_name: str,
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get timeline history for a company."""
    service = InsightTimelineService(db)
    return await service.get_timeline_history(company_name, limit)

@router.post("/timeline/{company_name}/analyze-delta", response_model=InsightDeltaResponse)
async def analyze_delta_since_last_run(
    company_name: str,
    impact_card_id: int,
    db: Session = Depends(get_db)
):
    """Analyze changes since the last analysis run."""
    service = InsightTimelineService(db)
    return await service.analyze_delta_since_last_run(company_name, impact_card_id)

# Evidence Badges & Confidence

@router.get("/evidence/{entity_type}/{entity_id}", response_model=Optional[EvidenceBadgeResponse])
async def get_evidence_badge(
    entity_type: str,
    entity_id: int,
    db: Session = Depends(get_db)
):
    """Get evidence badge with expanded details."""
    service = EvidenceBadgeService(db)
    return await service.get_expanded_evidence(entity_type, entity_id)

@router.get("/evidence/{entity_type}/{entity_id}/metrics", response_model=Optional[ConfidenceMetrics])
async def get_confidence_metrics(
    entity_type: str,
    entity_id: int,
    db: Session = Depends(get_db)
):
    """Get simplified confidence metrics for display."""
    service = EvidenceBadgeService(db)
    return await service.get_confidence_metrics(entity_type, entity_id)

@router.post("/evidence/create", response_model=EvidenceBadgeCreateResponse)
async def create_evidence_badge(
    request: EvidenceBadgeCreateRequest,
    db: Session = Depends(get_db)
):
    """Create an evidence badge for an entity."""
    service = EvidenceBadgeService(db)
    badge = await service.create_evidence_badge(
        request.entity_type, request.entity_id, request.sources, request.confidence_override
    )
    return EvidenceBadgeCreateResponse(id=badge.id, confidence=badge.confidence_percentage)

# Personal Playbooks

@router.get("/playbooks/personas", response_model=List[PersonaPreset])
async def get_persona_presets(
    category: Optional[str] = Query(None, description="Filter by category: individual, enterprise, research"),
    active_only: bool = Query(True, description="Only return active presets"),
    db: Session = Depends(get_db)
):
    """Get available persona presets."""
    service = PersonalPlaybookService(db)
    return await service.get_persona_presets(category, active_only)

@router.post("/playbooks/create", response_model=UserPlaybook)
async def create_user_playbook(
    user_id: int,
    persona_preset_id: int,
    custom_name: Optional[str] = None,
    custom_config: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db)
):
    """Create a user's personalized playbook."""
    service = PersonalPlaybookService(db)
    return await service.create_user_playbook(
        user_id, persona_preset_id, custom_name, custom_config
    )

@router.get("/playbooks/user/{user_id}", response_model=List[UserPlaybook])
async def get_user_playbooks(
    user_id: int,
    favorites_only: bool = Query(False, description="Only return favorite playbooks"),
    db: Session = Depends(get_db)
):
    """Get user's playbooks."""
    service = PersonalPlaybookService(db)
    return await service.get_user_playbooks(user_id, favorites_only)

@router.post("/playbooks/recommend", response_model=List[PlaybookRecommendation])
async def recommend_playbooks(
    user_id: int,
    context: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Recommend playbooks based on user context."""
    service = PersonalPlaybookService(db)
    return await service.recommend_playbooks(user_id, context)

@router.get("/playbooks/{playbook_id}/plan", response_model=PlaybookExecutionPlan)
async def create_execution_plan(
    playbook_id: int,
    target_company: Optional[str] = Query(None, description="Target company for research"),
    db: Session = Depends(get_db)
):
    """Create an execution plan for a playbook."""
    service = PersonalPlaybookService(db)
    return await service.create_execution_plan(playbook_id, target_company)

@router.post("/playbooks/{playbook_id}/execute")
async def execute_playbook(
    playbook_id: int,
    target_company: Optional[str] = None,
    execution_type: str = "research",
    db: Session = Depends(get_db)
):
    """Execute a playbook workflow."""
    service = PersonalPlaybookService(db)
    execution = await service.execute_playbook(playbook_id, target_company, execution_type)
    return {"execution_id": execution.id, "status": execution.completion_status}

@router.get("/playbooks/execution/{execution_id}/results", response_model=Optional[PlaybookResults])
async def get_execution_results(
    execution_id: int,
    db: Session = Depends(get_db)
):
    """Get results from a playbook execution."""
    service = PersonalPlaybookService(db)
    return await service.get_execution_results(execution_id)

# Action Tracking

@router.post("/actions/create", response_model=ActionItem)
async def create_action_item(
    action_data: ActionItemCreate,
    db: Session = Depends(get_db)
):
    """Create a new action item."""
    service = ActionTrackerService(db)
    return await service.create_action_item(action_data)

@router.put("/actions/{action_id}", response_model=Optional[ActionItem])
async def update_action_item(
    action_id: int,
    update_data: ActionItemUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing action item."""
    service = ActionTrackerService(db)
    action = await service.update_action_item(action_id, update_data)
    if not action:
        raise HTTPException(status_code=404, detail="Action item not found")
    return action

@router.get("/actions", response_model=List[ActionItem])
async def get_action_items(
    impact_card_id: Optional[int] = Query(None, description="Filter by impact card"),
    status: Optional[str] = Query(None, description="Filter by status"),
    assigned_to: Optional[str] = Query(None, description="Filter by assignee"),
    overdue_only: bool = Query(False, description="Only return overdue items"),
    db: Session = Depends(get_db)
):
    """Get action items with optional filtering."""
    from ..models.action_tracker import ActionStatus
    
    status_enum = None
    if status:
        try:
            status_enum = ActionStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    service = ActionTrackerService(db)
    return await service.get_action_items(impact_card_id, status_enum, assigned_to, overdue_only)

@router.post("/actions/generate/{impact_card_id}", response_model=List[ActionItem])
async def generate_actions_from_impact_card(
    impact_card_id: int,
    template_name: Optional[str] = Query(None, description="Template to use for generation"),
    db: Session = Depends(get_db)
):
    """Generate action items from an impact card."""
    service = ActionTrackerService(db)
    return await service.generate_actions_from_impact_card(impact_card_id, template_name)

@router.get("/actions/summary/{impact_card_id}", response_model=ActionSummary)
async def get_action_summary(
    impact_card_id: int,
    db: Session = Depends(get_db)
):
    """Get summary statistics for actions on an impact card."""
    service = ActionTrackerService(db)
    return await service.get_action_summary(impact_card_id)

# Action Boards

@router.post("/boards/create", response_model=ActionBoard)
async def create_action_board(
    board_data: ActionBoardCreate,
    db: Session = Depends(get_db)
):
    """Create a new action board."""
    service = ActionTrackerService(db)
    return await service.create_action_board(board_data)

@router.post("/boards/{board_id}/add-action")
async def add_action_to_board(
    board_id: int,
    action_item_id: int,
    column_id: str = "planned",
    db: Session = Depends(get_db)
):
    """Add an action item to a board."""
    service = ActionTrackerService(db)
    board_item = await service.add_action_to_board(board_id, action_item_id, column_id)
    return {"board_item_id": board_item.id, "column_id": board_item.column_id}

@router.put("/boards/items/{board_item_id}/move")
async def move_action_on_board(
    board_item_id: int,
    new_column_id: str,
    new_position: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Move an action item to a different column or position."""
    service = ActionTrackerService(db)
    board_item = await service.move_action_on_board(board_item_id, new_column_id, new_position)
    return {"board_item_id": board_item.id, "column_id": board_item.column_id, "position": board_item.position}

@router.get("/boards/{board_id}/view", response_model=Optional[ActionBoardView])
async def get_board_view(
    board_id: int,
    db: Session = Depends(get_db)
):
    """Get complete board view with items organized by column."""
    service = ActionTrackerService(db)
    board_view = await service.get_board_view(board_id)
    if not board_view:
        raise HTTPException(status_code=404, detail="Board not found")
    return board_view

# Analytics and Insights

@router.get("/insights/actions", response_model=ActionInsights)
async def get_action_insights(
    user_id: Optional[int] = Query(None, description="Filter by user"),
    db: Session = Depends(get_db)
):
    """Get insights and analytics for actions."""
    service = ActionTrackerService(db)
    return await service.get_action_insights(user_id)

# Demo and Testing Endpoints

@router.post("/demo/setup", response_model=DemoSetupResponse)
async def setup_demo_data(
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """Set up demo data for all enhancement features."""
    
    # Initialize services
    timeline_service = InsightTimelineService(db)
    evidence_service = EvidenceBadgeService(db)
    playbook_service = PersonalPlaybookService(db)
    action_service = ActionTrackerService(db)
    
    # Create demo playbook
    personas = await playbook_service.get_persona_presets(category="individual")
    demo_playbook = None
    if personas:
        demo_playbook = await playbook_service.create_user_playbook(
            user_id=user_id,
            persona_preset_id=personas[0].id,
            custom_name="My Demo Playbook"
        )
    
    # Create demo action board
    board_data = ActionBoardCreate(
        name="Demo Action Board",
        user_id=user_id,
        description="Demo board for testing action tracking",
        board_type="personal",
        columns=[]
    )
    demo_board = await action_service.create_action_board(board_data)
    
    return DemoSetupResponse(
        message="Demo data setup complete",
        personas_count=len(personas) if personas else 0,
        demo_playbook_id=demo_playbook.id if demo_playbook else None,
        demo_board_id=demo_board.id
    )

@router.get("/demo/status")
async def get_demo_status(db: Session = Depends(get_db)):
    """Get status of demo data and enhancement features."""
    
    # Check if built-in data exists
    playbook_service = PersonalPlaybookService(db)
    action_service = ActionTrackerService(db)
    
    personas = await playbook_service.get_persona_presets()
    
    # Count existing data
    from ..models.insight_timeline import InsightTimeline
    from ..models.evidence_badge import EvidenceBadge
    from ..models.personal_playbook import UserPlaybook
    from ..models.action_tracker import ActionItem
    
    timeline_count = db.query(InsightTimeline).count()
    evidence_count = db.query(EvidenceBadge).count()
    playbook_count = db.query(UserPlaybook).count()
    action_count = db.query(ActionItem).count()
    
    return {
        "enhancement_features": {
            "insight_timeline": {
                "available": True,
                "entries_count": timeline_count
            },
            "evidence_badges": {
                "available": True,
                "badges_count": evidence_count
            },
            "personal_playbooks": {
                "available": True,
                "personas_count": len(personas),
                "user_playbooks_count": playbook_count
            },
            "action_tracking": {
                "available": True,
                "actions_count": action_count
            }
        },
        "demo_ready": True,
        "last_updated": datetime.utcnow().isoformat()
    }