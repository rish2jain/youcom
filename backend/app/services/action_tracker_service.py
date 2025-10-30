"""
Service for managing action tracking and lightweight task management.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func, update

from ..models.action_tracker import (
    ActionItem, ActionReminder, ActionBoard, ActionBoardItem, ActionTemplate,
    ActionStatus, ActionPriority
)
from ..models.impact_card import ImpactCard
from ..schemas.action_tracker import (
    ActionItemCreate, ActionItemUpdate, ActionReminderCreate,
    ActionBoardCreate, ActionBoardItemCreate, ActionTemplateCreate,
    ActionSummary, ActionBoardView, ActionInsights,
    BUILTIN_ACTION_TEMPLATES
)

logger = logging.getLogger(__name__)

class ActionTrackerService:
    """Service for managing action tracking and task management."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def initialize_builtin_templates(self) -> List[ActionTemplate]:
        """Initialize built-in action templates if they don't exist."""
        created_templates = []
        
        for template_key, template_data in BUILTIN_ACTION_TEMPLATES.items():
            existing = self.db.query(ActionTemplate).filter(
                ActionTemplate.name == template_data["name"]
            ).first()
            
            if not existing:
                template_create = ActionTemplateCreate(**template_data)
                template = ActionTemplate(**template_create.dict())
                self.db.add(template)
                created_templates.append(template)
        
        if created_templates:
            self.db.commit()
            for template in created_templates:
                self.db.refresh(template)
            logger.info(f"Initialized {len(created_templates)} built-in action templates")
        
        return created_templates
    
    # Action Item Management
    
    async def create_action_item(self, action_data: ActionItemCreate) -> ActionItem:
        """Create a new action item."""
        
        # Verify impact card exists
        impact_card = self.db.query(ImpactCard).filter(
            ImpactCard.id == action_data.impact_card_id
        ).first()
        
        if not impact_card:
            raise ValueError(f"Impact card {action_data.impact_card_id} not found")
        
        action = ActionItem(**action_data.dict())
        action.user_modified = True  # Mark as user-created
        action.ai_generated = False
        
        self.db.add(action)
        self.db.commit()
        self.db.refresh(action)
        
        logger.info(f"Created action item '{action.title}' for impact card {action_data.impact_card_id}")
        return action
    
    async def update_action_item(
        self, 
        action_id: int, 
        update_data: ActionItemUpdate
    ) -> Optional[ActionItem]:
        """Update an existing action item."""
        
        action = self.db.query(ActionItem).filter(ActionItem.id == action_id).first()
        if not action:
            return None
        
        # Track status changes
        old_status = action.status
        
        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(action, field, value)
        
        action.user_modified = True
        action.updated_at = datetime.now(timezone.utc)
        
        # Handle status changes
        if update_data.status and update_data.status != old_status:
            await self._handle_status_change(action, old_status, update_data.status)
        
        self.db.commit()
        self.db.refresh(action)
        
        logger.info(f"Updated action item {action_id}: {action.title}")
        return action
    
    async def get_action_items(
        self, 
        impact_card_id: Optional[int] = None,
        status: Optional[ActionStatus] = None,
        assigned_to: Optional[str] = None,
        overdue_only: bool = False
    ) -> List[ActionItem]:
        """Get action items with optional filtering."""
        
        query = self.db.query(ActionItem)
        
        if impact_card_id:
            query = query.filter(ActionItem.impact_card_id == impact_card_id)
        
        if status:
            query = query.filter(ActionItem.status == status)
        
        if assigned_to:
            query = query.filter(ActionItem.assigned_to == assigned_to)
        
        if overdue_only:
            query = query.filter(
                and_(
                    ActionItem.due_date < datetime.now(timezone.utc),
                    ActionItem.status.notin_([ActionStatus.DONE, ActionStatus.CANCELLED])
                )
            )
        
        return query.order_by(
            ActionItem.priority.desc(),
            ActionItem.due_date.asc(),
            ActionItem.created_at.desc()
        ).all()
    
    async def generate_actions_from_impact_card(
        self, 
        impact_card_id: int,
        template_name: Optional[str] = None
    ) -> List[ActionItem]:
        """Generate action items from an impact card using AI or templates."""
        
        impact_card = self.db.query(ImpactCard).filter(
            ImpactCard.id == impact_card_id
        ).first()
        
        if not impact_card:
            raise ValueError(f"Impact card {impact_card_id} not found")
        
        # Use template if specified
        if template_name:
            template = self.db.query(ActionTemplate).filter(
                ActionTemplate.name == template_name
            ).first()
            
            if template:
                return await self._generate_from_template(impact_card, template)
        
        # Generate AI-based actions
        return await self._generate_ai_actions(impact_card)
    
    async def get_action_summary(self, impact_card_id: int) -> ActionSummary:
        """Get summary statistics for actions on an impact card."""
        
        actions = await self.get_action_items(impact_card_id=impact_card_id)
        
        # Count by status
        by_status = {}
        for status in ActionStatus:
            by_status[status] = len([a for a in actions if a.status == status])
        
        # Count by priority
        by_priority = {}
        for priority in ActionPriority:
            by_priority[priority] = len([a for a in actions if a.priority == priority])
        
        # Overdue count
        overdue_count = len([a for a in actions if a.is_overdue])
        
        # Completed this week
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        completed_this_week = len([
            a for a in actions 
            if a.status == ActionStatus.DONE and a.completed_at and a.completed_at > week_ago
        ])
        
        # Time estimates
        estimated_total = sum(a.estimated_hours or 0 for a in actions)
        actual_total = sum(a.actual_hours or 0 for a in actions)
        
        return ActionSummary(
            total_actions=len(actions),
            by_status=by_status,
            by_priority=by_priority,
            overdue_count=overdue_count,
            completed_this_week=completed_this_week,
            estimated_total_hours=estimated_total,
            actual_total_hours=actual_total
        )
    
    # Action Board Management
    
    async def create_action_board(
        self, 
        board_data: ActionBoardCreate
    ) -> ActionBoard:
        """Create a new action board."""
        
        # Set default columns if not provided
        if not board_data.columns:
            board_data.columns = [
                {"id": "planned", "name": "Planned", "color": "#gray"},
                {"id": "in_progress", "name": "In Progress", "color": "#blue"},
                {"id": "done", "name": "Done", "color": "#green"}
            ]
        
        board = ActionBoard(**board_data.dict())
        self.db.add(board)
        self.db.commit()
        self.db.refresh(board)
        
        logger.info(f"Created action board '{board.name}' for user {board_data.user_id}")
        return board
    
    async def add_action_to_board(
        self, 
        board_id: int, 
        action_item_id: int,
        column_id: str = "planned"
    ) -> ActionBoardItem:
        """Add an action item to a board."""
        
        # Verify board and action exist
        board = self.db.query(ActionBoard).filter(ActionBoard.id == board_id).first()
        action = self.db.query(ActionItem).filter(ActionItem.id == action_item_id).first()
        
        if not board:
            raise ValueError(f"Action board {board_id} not found")
        if not action:
            raise ValueError(f"Action item {action_item_id} not found")
        
        # Check if already on board
        existing = self.db.query(ActionBoardItem).filter(
            and_(
                ActionBoardItem.board_id == board_id,
                ActionBoardItem.action_item_id == action_item_id
            )
        ).first()
        
        if existing:
            return existing
        
        # Get position for new item
        max_position = self.db.query(func.max(ActionBoardItem.position)).filter(
            and_(
                ActionBoardItem.board_id == board_id,
                ActionBoardItem.column_id == column_id
            )
        ).scalar() or 0
        
        board_item_data = ActionBoardItemCreate(
            board_id=board_id,
            action_item_id=action_item_id,
            column_id=column_id,
            position=max_position + 1
        )
        
        board_item = ActionBoardItem(**board_item_data.dict())
        self.db.add(board_item)
        self.db.commit()
        self.db.refresh(board_item)
        
        return board_item
    
    async def move_action_on_board(
        self, 
        board_item_id: int,
        new_column_id: str,
        new_position: Optional[int] = None
    ) -> ActionBoardItem:
        """Move an action item to a different column or position."""
        
        board_item = self.db.query(ActionBoardItem).filter(
            ActionBoardItem.id == board_item_id
        ).first()
        
        if not board_item:
            raise ValueError(f"Board item {board_item_id} not found")
        
        old_column = board_item.column_id
        
        # Update column
        board_item.column_id = new_column_id
        board_item.moved_at = datetime.now(timezone.utc)
        
        # Update position if specified
        if new_position is not None:
            board_item.position = new_position
        else:
            # Move to end of new column
            max_position = self.db.query(func.max(ActionBoardItem.position)).filter(
                and_(
                    ActionBoardItem.board_id == board_item.board_id,
                    ActionBoardItem.column_id == new_column_id
                )
            ).scalar() or 0
            board_item.position = max_position + 1
        
        # Update action status based on column
        await self._sync_action_status_with_column(board_item, new_column_id)
        
        self.db.commit()
        self.db.refresh(board_item)
        
        logger.info(f"Moved board item {board_item_id} from {old_column} to {new_column_id}")
        return board_item
    
    async def get_board_view(self, board_id: int) -> Optional[ActionBoardView]:
        """Get complete board view with items organized by column."""
        
        board = self.db.query(ActionBoard).filter(ActionBoard.id == board_id).first()
        if not board:
            return None
        
        # Get all board items with their actions
        board_items = self.db.query(ActionBoardItem).filter(
            ActionBoardItem.board_id == board_id
        ).order_by(ActionBoardItem.column_id, ActionBoardItem.position).all()
        
        # Organize by column
        items_by_column = {}
        for column in board.columns:
            column_id = column["id"]
            items_by_column[column_id] = [
                item for item in board_items if item.column_id == column_id
            ]
        
        # Get summary for all actions on this board
        all_action_ids = [item.action_item_id for item in board_items]
        if all_action_ids:
            # This is a simplified summary - in practice you'd aggregate across all impact cards
            summary = ActionSummary(
                total_actions=len(all_action_ids),
                by_status={status: 0 for status in ActionStatus},
                by_priority={priority: 0 for priority in ActionPriority},
                overdue_count=0,
                completed_this_week=0,
                estimated_total_hours=0,
                actual_total_hours=0
            )
        else:
            summary = ActionSummary(
                total_actions=0,
                by_status={status: 0 for status in ActionStatus},
                by_priority={priority: 0 for priority in ActionPriority},
                overdue_count=0,
                completed_this_week=0,
                estimated_total_hours=0,
                actual_total_hours=0
            )
        
        return ActionBoardView(
            board=board,
            items_by_column=items_by_column,
            summary=summary
        )
    
    # Reminder Management
    
    async def create_reminder(self, reminder_data: ActionReminderCreate) -> ActionReminder:
        """Create a reminder for an action item."""
        
        reminder = ActionReminder(**reminder_data.dict())
        self.db.add(reminder)
        self.db.commit()
        self.db.refresh(reminder)
        
        logger.info(f"Created {reminder_data.reminder_type} reminder for action {reminder_data.action_item_id}")
        return reminder
    
    async def get_due_reminders(self) -> List[ActionReminder]:
        """Get reminders that are due to be sent."""
        
        now = datetime.now(timezone.utc)
        return self.db.query(ActionReminder).filter(
            and_(
                ActionReminder.reminder_time <= now,
                ActionReminder.is_sent == False
            )
        ).all()
    
    # Analytics and Insights
    
    async def get_action_insights(self, user_id: Optional[int] = None) -> ActionInsights:
        """Get insights and analytics for actions."""
        
        # This is a simplified implementation
        # In practice, you'd analyze historical data for the user or system-wide
        
        return ActionInsights(
            completion_rate=0.75,
            average_completion_time_days=3.5,
            most_common_categories=[
                {"category": "research", "count": 45},
                {"category": "strategy", "count": 32},
                {"category": "communication", "count": 28}
            ],
            productivity_trends=[
                {"period": "this_week", "completed": 12, "created": 15},
                {"period": "last_week", "completed": 18, "created": 14}
            ],
            recommendations=[
                "Consider breaking down large tasks into smaller actions",
                "Set more realistic due dates to improve completion rates",
                "Use templates for common action patterns"
            ]
        )
    
    # Private helper methods
    
    async def _handle_status_change(
        self, 
        action: ActionItem, 
        old_status: ActionStatus, 
        new_status: ActionStatus
    ):
        """Handle status change logic."""
        
        # Update completion timestamp
        if new_status == ActionStatus.DONE and old_status != ActionStatus.DONE:
            action.completed_at = datetime.now(timezone.utc)
            action.progress_percentage = 100
        elif new_status != ActionStatus.DONE and old_status == ActionStatus.DONE:
            action.completed_at = None
        
        # Track status history
        if not action.status_updates:
            action.status_updates = []
        
        action.status_updates.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "old_status": old_status.value,
            "new_status": new_status.value,
            "user_modified": True
        })
    
    async def _sync_action_status_with_column(
        self, 
        board_item: ActionBoardItem, 
        column_id: str
    ):
        """Sync action status with board column."""
        
        # Map common column IDs to statuses
        column_status_map = {
            "planned": ActionStatus.PLANNED,
            "todo": ActionStatus.PLANNED,
            "in_progress": ActionStatus.IN_PROGRESS,
            "doing": ActionStatus.IN_PROGRESS,
            "done": ActionStatus.DONE,
            "completed": ActionStatus.DONE,
            "cancelled": ActionStatus.CANCELLED
        }
        
        new_status = column_status_map.get(column_id.lower())
        if new_status and board_item.action_item.status != new_status:
            old_status = board_item.action_item.status
            board_item.action_item.status = new_status
            await self._handle_status_change(board_item.action_item, old_status, new_status)
    
    async def _generate_from_template(
        self, 
        impact_card: ImpactCard, 
        template: ActionTemplate
    ) -> List[ActionItem]:
        """Generate actions from a template."""
        
        actions = []
        
        for action_template in template.template_actions:
            action_data = ActionItemCreate(
                impact_card_id=impact_card.id,
                title=action_template["title"],
                description=action_template.get("description"),
                category=action_template.get("category"),
                priority=ActionPriority(action_template.get("priority", "medium")),
                estimated_hours=action_template.get("estimated_hours"),
                success_criteria=action_template.get("success_criteria"),
                source_insight=f"Generated from template: {template.name}",
                ai_generated=True
            )
            
            action = ActionItem(**action_data.dict())
            self.db.add(action)
            actions.append(action)
        
        # Update template usage atomically
        if template is not None:
            self.db.execute(
                update(ActionTemplate)
                .where(ActionTemplate.id == template.id)
                .values(usage_count=ActionTemplate.usage_count + 1)
            )
        
        self.db.commit()
        for action in actions:
            self.db.refresh(action)
        
        logger.info(f"Generated {len(actions)} actions from template '{template.name}'")
        return actions
    
    async def _generate_ai_actions(self, impact_card: ImpactCard) -> List[ActionItem]:
        """Generate AI-based actions from impact card insights."""
        
        # This is a simplified implementation
        # In practice, this would use AI to analyze the impact card and generate relevant actions
        
        base_actions = [
            {
                "title": f"Analyze impact of {impact_card.company_name} developments",
                "description": "Deep dive analysis of competitive implications",
                "category": "research",
                "priority": ActionPriority.HIGH,
                "estimated_hours": 4
            },
            {
                "title": f"Brief team on {impact_card.company_name} insights",
                "description": "Share findings with relevant stakeholders",
                "category": "communication",
                "priority": ActionPriority.MEDIUM,
                "estimated_hours": 1
            }
        ]
        
        # Add risk-specific actions based on risk score
        if impact_card.risk_score > 70:
            base_actions.append({
                "title": "Develop strategic response plan",
                "description": "Create action plan to address high-risk competitive threat",
                "category": "strategy",
                "priority": ActionPriority.URGENT,
                "estimated_hours": 8
            })
        
        actions = []
        for action_data in base_actions:
            action_create = ActionItemCreate(
                impact_card_id=impact_card.id,
                **action_data,
                source_insight="AI-generated based on impact card analysis",
                ai_generated=True
            )
            
            action = ActionItem(**action_create.dict())
            self.db.add(action)
            actions.append(action)
        
        self.db.commit()
        for action in actions:
            self.db.refresh(action)
        
        logger.info(f"Generated {len(actions)} AI-based actions for impact card {impact_card.id}")
        return actions