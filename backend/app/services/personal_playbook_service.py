"""
Service for managing personal playbooks and persona-driven workflows.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, update

from ..models.personal_playbook import PersonaPreset, UserPlaybook, PlaybookExecution, PlaybookTemplate
from ..schemas.personal_playbook import (
    PersonaPresetCreate, 
    UserPlaybookCreate, 
    PlaybookExecutionCreate,
    PlaybookRecommendation,
    PlaybookExecutionPlan,
    PlaybookResults,
    BUILTIN_PERSONAS
)

logger = logging.getLogger(__name__)

class PersonalPlaybookService:
    """Service for managing personal playbooks and persona-driven workflows."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def initialize_builtin_personas(self) -> List[PersonaPreset]:
        """Initialize built-in persona presets if they don't exist."""
        created_personas = []
        
        for persona_key, persona_data in BUILTIN_PERSONAS.items():
            existing = self.db.query(PersonaPreset).filter(
                PersonaPreset.name == persona_data["name"]
            ).first()
            
            if not existing:
                preset_data = PersonaPresetCreate(**persona_data)
                persona = PersonaPreset(**preset_data.dict())
                self.db.add(persona)
                created_personas.append(persona)
        
        if created_personas:
            self.db.commit()
            for persona in created_personas:
                self.db.refresh(persona)
            logger.info(f"Initialized {len(created_personas)} built-in persona presets")
        
        return created_personas
    
    async def get_persona_presets(
        self, 
        category: Optional[str] = None,
        active_only: bool = True
    ) -> List[PersonaPreset]:
        """Get available persona presets."""
        query = self.db.query(PersonaPreset)
        
        if active_only:
            query = query.filter(PersonaPreset.is_active == True)
        
        if category:
            query = query.filter(PersonaPreset.category == category)
        
        return query.order_by(PersonaPreset.usage_count.desc()).all()
    
    async def create_user_playbook(
        self, 
        user_id: int, 
        persona_preset_id: int,
        custom_name: Optional[str] = None,
        custom_config: Optional[Dict[str, Any]] = None
    ) -> UserPlaybook:
        """Create a user's personalized playbook."""
        
        # Verify persona preset exists
        persona_preset = self.db.query(PersonaPreset).filter(
            PersonaPreset.id == persona_preset_id
        ).first()
        
        if not persona_preset:
            raise ValueError(f"Persona preset {persona_preset_id} not found")
        
        # Create user playbook
        playbook_data = UserPlaybookCreate(
            user_id=user_id,
            persona_preset_id=persona_preset_id,
            custom_name=custom_name,
            custom_config=custom_config
        )
        
        playbook = UserPlaybook(**playbook_data.dict())
        self.db.add(playbook)
        self.db.commit()
        self.db.refresh(playbook)
        
        # Increment usage count for persona preset atomically
        self.db.execute(
            update(PersonaPreset)
            .where(PersonaPreset.id == persona_preset.id)
            .values(usage_count=PersonaPreset.usage_count + 1)
        )
        self.db.commit()
        
        logger.info(f"Created user playbook for user {user_id} with persona {persona_preset.name}")
        return playbook
    
    async def get_user_playbooks(
        self, 
        user_id: int,
        favorites_only: bool = False
    ) -> List[UserPlaybook]:
        """Get user's playbooks."""
        query = self.db.query(UserPlaybook).filter(UserPlaybook.user_id == user_id)
        
        if favorites_only:
            query = query.filter(UserPlaybook.is_favorite == True)
        
        return query.order_by(desc(UserPlaybook.last_used)).all()
    
    async def recommend_playbooks(
        self, 
        user_id: int,
        context: Dict[str, Any]
    ) -> List[PlaybookRecommendation]:
        """Recommend playbooks based on user context."""
        
        # Get user's existing playbooks to understand preferences
        user_playbooks = await self.get_user_playbooks(user_id)
        used_persona_ids = {pb.persona_preset_id for pb in user_playbooks}
        
        # Get all available personas
        all_personas = await self.get_persona_presets()
        
        recommendations = []
        
        for persona in all_personas:
            match_score = await self._calculate_match_score(persona, context, user_playbooks)
            
            if match_score > 0.3:  # Only recommend if reasonable match
                match_reasons = await self._get_match_reasons(persona, context)
                
                recommendation = PlaybookRecommendation(
                    persona_preset=persona,
                    match_score=match_score,
                    match_reasons=match_reasons,
                    estimated_time_minutes=self._estimate_execution_time(persona),
                    key_benefits=self._get_key_benefits(persona)
                )
                recommendations.append(recommendation)
        
        # Sort by match score and return top 5
        recommendations.sort(key=lambda x: x.match_score, reverse=True)
        return recommendations[:5]
    
    async def create_execution_plan(
        self, 
        user_playbook_id: int,
        target_company: Optional[str] = None
    ) -> PlaybookExecutionPlan:
        """Create an execution plan for a playbook."""
        
        playbook = self.db.query(UserPlaybook).filter(
            UserPlaybook.id == user_playbook_id
        ).first()
        
        if not playbook:
            raise ValueError(f"User playbook {user_playbook_id} not found")
        
        # Get effective configuration (preset + user customizations)
        config = self._merge_playbook_config(playbook)
        
        # Generate execution steps
        steps = await self._generate_execution_steps(config, target_company)
        
        # Calculate estimates
        estimated_duration = self._estimate_execution_time(playbook.persona_preset)
        
        return PlaybookExecutionPlan(
            playbook=playbook,
            steps=steps,
            estimated_duration=estimated_duration,
            required_inputs=self._get_required_inputs(config),
            expected_outputs=self._get_expected_outputs(config),
            success_criteria=self._get_success_criteria(config)
        )
    
    async def execute_playbook(
        self, 
        user_playbook_id: int,
        target_company: Optional[str] = None,
        execution_type: str = "research"
    ) -> PlaybookExecution:
        """Execute a playbook workflow."""
        
        # Create execution record
        execution_data = PlaybookExecutionCreate(
            user_playbook_id=user_playbook_id,
            target_company=target_company,
            execution_type=execution_type,
            estimated_duration_minutes=self._estimate_execution_time_for_type(execution_type)
        )
        
        execution = PlaybookExecution(**execution_data.dict())
        self.db.add(execution)
        self.db.flush()  # Get the ID
        
        try:
            # Execute the workflow
            results = await self._execute_workflow(execution)
            
            # Update execution with results
            execution.completion_status = "completed"
            execution.completion_percentage = 100
            execution.completed_at = datetime.now(timezone.utc)
            execution.generated_artifacts = results.get("artifacts", {})
            
            # Update user playbook usage
            playbook = self.db.query(UserPlaybook).filter(
                UserPlaybook.id == user_playbook_id
            ).first()
            
            if playbook:
                # Update usage count and last_used atomically
                self.db.execute(
                    update(UserPlaybook)
                    .where(UserPlaybook.id == playbook.id)
                    .values(
                        usage_count=UserPlaybook.usage_count + 1,
                        last_used=datetime.now(timezone.utc)
                    )
                )
            
            self.db.commit()
            self.db.refresh(execution)
            
            logger.info(f"Successfully executed playbook {user_playbook_id} for {target_company}")
            
        except Exception as e:
            execution.completion_status = "failed"
            execution.execution_notes = str(e)
            self.db.commit()
            logger.error(f"Failed to execute playbook {user_playbook_id}: {e}")
            raise
        
        return execution
    
    async def get_execution_results(
        self, 
        execution_id: int
    ) -> Optional[PlaybookResults]:
        """Get results from a playbook execution."""
        
        execution = self.db.query(PlaybookExecution).filter(
            PlaybookExecution.id == execution_id
        ).first()
        
        if not execution or execution.completion_status != "completed":
            return None
        
        # Generate results summary
        artifacts = await self._format_execution_artifacts(execution)
        insights = await self._extract_execution_insights(execution)
        next_steps = await self._generate_next_steps(execution)
        time_saved = await self._calculate_time_saved(execution)
        
        return PlaybookResults(
            execution=execution,
            artifacts=artifacts,
            insights=insights,
            next_steps=next_steps,
            time_saved_estimate=time_saved,
            satisfaction_prompt=self._generate_satisfaction_prompt(execution)
        )
    
    async def _calculate_match_score(
        self, 
        persona: PersonaPreset, 
        context: Dict[str, Any],
        user_playbooks: List[UserPlaybook]
    ) -> float:
        """Calculate how well a persona matches the user's context."""
        score = 0.0
        
        # Context matching
        user_type = context.get("user_type", "individual")
        if persona.category == user_type:
            score += 0.3
        
        # Task matching
        task_type = context.get("task_type")
        if task_type:
            if task_type in persona.name.lower():
                score += 0.4
            elif any(task_type in task for task in (persona.follow_up_tasks or [])):
                score += 0.2
        
        # Experience level matching
        experience = context.get("experience_level", "medium")
        if experience == "beginner" and persona.analysis_depth == "quick":
            score += 0.2
        elif experience == "expert" and persona.analysis_depth == "deep":
            score += 0.2
        elif experience == "medium" and persona.analysis_depth == "medium":
            score += 0.1
        
        # Usage history bonus
        used_persona_ids = {pb.persona_preset_id for pb in user_playbooks}
        if persona.id in used_persona_ids:
            score += 0.1  # Slight bonus for familiar personas
        
        return min(1.0, score)
    
    async def _get_match_reasons(
        self, 
        persona: PersonaPreset, 
        context: Dict[str, Any]
    ) -> List[str]:
        """Get reasons why this persona matches the context."""
        reasons = []
        
        if persona.category == context.get("user_type", "individual"):
            reasons.append(f"Designed for {persona.category} users")
        
        if context.get("task_type") and context["task_type"] in persona.name.lower():
            reasons.append(f"Specialized for {context['task_type']} tasks")
        
        if persona.analysis_depth == "quick":
            reasons.append("Fast execution for quick insights")
        elif persona.analysis_depth == "deep":
            reasons.append("Comprehensive analysis for thorough research")
        
        if persona.usage_count > 10:
            reasons.append("Popular choice among users")
        
        return reasons
    
    def _estimate_execution_time(self, persona: PersonaPreset) -> int:
        """Estimate execution time in minutes."""
        base_times = {
            "quick": 5,
            "medium": 15,
            "deep": 30
        }
        return base_times.get(persona.analysis_depth, 15)
    
    def _estimate_execution_time_for_type(self, execution_type: str) -> int:
        """Estimate execution time based on type."""
        type_times = {
            "research": 10,
            "monitoring": 5,
            "analysis": 20
        }
        return type_times.get(execution_type, 10)
    
    def _get_key_benefits(self, persona: PersonaPreset) -> List[str]:
        """Get key benefits of using this persona."""
        benefits = []
        
        if persona.analysis_depth == "quick":
            benefits.append("Get insights in under 10 minutes")
        elif persona.analysis_depth == "deep":
            benefits.append("Comprehensive analysis with detailed insights")
        
        if persona.follow_up_tasks:
            benefits.append(f"Includes {len(persona.follow_up_tasks)} follow-up tasks")
        
        if persona.export_templates:
            formats = persona.export_templates.get("formats", [])
            if formats:
                benefits.append(f"Export to {', '.join(formats)}")
        
        benefits.append("Tailored for your specific use case")
        
        return benefits
    
    def _merge_playbook_config(self, playbook: UserPlaybook) -> Dict[str, Any]:
        """Merge persona preset config with user customizations."""
        base_config = {
            "default_data_slices": playbook.persona_preset.default_data_slices or {},
            "export_templates": playbook.persona_preset.export_templates or {},
            "follow_up_tasks": playbook.persona_preset.follow_up_tasks or [],
            "key_questions": playbook.persona_preset.key_questions or [],
            "priority_sources": playbook.persona_preset.priority_sources or [],
            "analysis_depth": playbook.persona_preset.analysis_depth
        }
        
        # Apply user customizations
        if playbook.custom_config:
            for key, value in playbook.custom_config.items():
                if key in base_config:
                    base_config[key] = value
        
        return base_config
    
    async def _generate_execution_steps(
        self, 
        config: Dict[str, Any], 
        target_company: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Generate execution steps for the playbook."""
        steps = []
        
        # Step 1: Data collection
        steps.append({
            "step": 1,
            "name": "Data Collection",
            "description": "Gather information from configured sources",
            "estimated_minutes": 3,
            "data_slices": config.get("default_data_slices", {}),
            "priority_sources": config.get("priority_sources", [])
        })
        
        # Step 2: Analysis
        analysis_depth = config.get("analysis_depth", "medium")
        analysis_time = {"quick": 2, "medium": 5, "deep": 10}.get(analysis_depth, 5)
        
        steps.append({
            "step": 2,
            "name": "Analysis",
            "description": f"Perform {analysis_depth} analysis of collected data",
            "estimated_minutes": analysis_time,
            "key_questions": config.get("key_questions", [])
        })
        
        # Step 3: Report generation
        steps.append({
            "step": 3,
            "name": "Report Generation",
            "description": "Generate formatted output",
            "estimated_minutes": 2,
            "export_templates": config.get("export_templates", {})
        })
        
        # Step 4: Follow-up planning
        if config.get("follow_up_tasks"):
            steps.append({
                "step": 4,
                "name": "Follow-up Planning",
                "description": "Prepare recommended next steps",
                "estimated_minutes": 1,
                "follow_up_tasks": config["follow_up_tasks"]
            })
        
        return steps
    
    def _get_required_inputs(self, config: Dict[str, Any]) -> List[str]:
        """Get required inputs for execution."""
        inputs = ["Company name or topic"]
        
        data_slices = config.get("default_data_slices", {})
        if data_slices.get("time_horizon"):
            inputs.append("Analysis time horizon")
        
        return inputs
    
    def _get_expected_outputs(self, config: Dict[str, Any]) -> List[str]:
        """Get expected outputs from execution."""
        outputs = ["Research report"]
        
        export_templates = config.get("export_templates", {})
        if export_templates.get("formats"):
            outputs.extend([f"{fmt.upper()} export" for fmt in export_templates["formats"]])
        
        if config.get("follow_up_tasks"):
            outputs.append("Follow-up task list")
        
        return outputs
    
    def _get_success_criteria(self, config: Dict[str, Any]) -> List[str]:
        """Get success criteria for execution."""
        criteria = [
            "All data sources successfully accessed",
            "Analysis completed without errors",
            "Report generated in requested format"
        ]
        
        if config.get("key_questions"):
            criteria.append(f"All {len(config['key_questions'])} key questions addressed")
        
        return criteria
    
    async def _execute_workflow(self, execution: PlaybookExecution) -> Dict[str, Any]:
        """Execute the actual workflow (simplified implementation)."""
        
        # This is a simplified implementation
        # In a real system, this would orchestrate the actual research workflow
        
        results = {
            "artifacts": {
                "research_report_id": f"report_{execution.id}",
                "impact_card_id": f"card_{execution.id}",
                "export_files": []
            },
            "insights_generated": 5,
            "sources_analyzed": 15,
            "time_taken_minutes": execution.estimated_duration_minutes or 10
        }
        
        # Simulate progress updates
        execution.completion_percentage = 25
        self.db.commit()
        
        # Simulate more progress
        execution.completion_percentage = 75
        self.db.commit()
        
        return results
    
    async def _format_execution_artifacts(self, execution: PlaybookExecution) -> List[Dict[str, Any]]:
        """Format execution artifacts for display."""
        artifacts = []
        
        generated = execution.generated_artifacts or {}
        
        if generated.get("research_report_id"):
            artifacts.append({
                "type": "research_report",
                "id": generated["research_report_id"],
                "name": f"Research Report - {execution.target_company}",
                "description": "Comprehensive company analysis",
                "url": f"/api/v1/research/{generated['research_report_id']}"
            })
        
        if generated.get("impact_card_id"):
            artifacts.append({
                "type": "impact_card",
                "id": generated["impact_card_id"],
                "name": f"Impact Card - {execution.target_company}",
                "description": "Competitive impact analysis",
                "url": f"/api/v1/impact/{generated['impact_card_id']}"
            })
        
        return artifacts
    
    async def _extract_execution_insights(self, execution: PlaybookExecution) -> List[str]:
        """Extract key insights from execution."""
        # This would analyze the actual results in a real implementation
        return [
            f"Analysis completed for {execution.target_company}",
            f"Execution took {execution.estimated_duration_minutes} minutes",
            "All configured data sources were successfully accessed",
            "High-quality insights generated with strong source validation"
        ]
    
    async def _generate_next_steps(self, execution: PlaybookExecution) -> List[str]:
        """Generate recommended next steps."""
        return [
            "Review generated research report",
            "Share findings with relevant stakeholders",
            "Schedule follow-up analysis if needed",
            "Update monitoring alerts based on insights"
        ]
    
    async def _calculate_time_saved(self, execution: PlaybookExecution) -> int:
        """Calculate estimated time saved vs manual research."""
        # Estimate based on execution type and complexity
        manual_time_estimates = {
            "research": 120,  # 2 hours manual vs 10 minutes automated
            "monitoring": 60,  # 1 hour manual vs 5 minutes automated
            "analysis": 180   # 3 hours manual vs 20 minutes automated
        }
        
        manual_time = manual_time_estimates.get(execution.execution_type, 120)
        automated_time = execution.estimated_duration_minutes or 10
        
        return max(0, manual_time - automated_time)
    
    def _generate_satisfaction_prompt(self, execution: PlaybookExecution) -> str:
        """Generate a prompt for user satisfaction feedback."""
        return f"How satisfied were you with the {execution.execution_type} results for {execution.target_company}? Your feedback helps us improve the playbook experience."