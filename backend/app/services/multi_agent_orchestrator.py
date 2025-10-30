"""
Multi-Agent Orchestrator - Week 3 Implementation
Coordinates multiple specialized AI agents for comprehensive analysis.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from app.services.multi_agent_system import ResearchAgent, AnalysisAgent, AgentTask, AgentType, AgentStatus
from app.services.strategy_agent import StrategyAgent
from app.services.advanced_orchestrator import AdvancedYouComOrchestrator

logger = logging.getLogger(__name__)

class MultiAgentOrchestrator:
    """Orchestrates multiple specialized AI agents"""
    
    def __init__(self):
        self.orchestrator = None  # Will be initialized when needed
        self.agents = {}
        self.active_tasks = {}
        self.completed_tasks = {}
        
    async def initialize(self):
        """Initialize the orchestrator and agents"""
        self.orchestrator = AdvancedYouComOrchestrator()
        
        # Initialize specialized agents
        self.agents = {
            AgentType.RESEARCH: ResearchAgent(self.orchestrator),
            AgentType.ANALYSIS: AnalysisAgent(self.orchestrator),
            AgentType.STRATEGY: StrategyAgent(),
            # Monitoring agent would be added here
        }
        
        logger.info("🤖 Multi-Agent System initialized with specialized agents")
    
    async def generate_comprehensive_intelligence(
        self,
        competitor: str,
        analysis_depth: str = "comprehensive",
        include_strategy: bool = True,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive competitive intelligence using all agents"""
        logger.info(f"🚀 Starting comprehensive intelligence generation for {competitor}")
        
        if not self.orchestrator:
            await self.initialize()
        
        start_time = datetime.utcnow()
        session_id = str(uuid.uuid4())
        
        try:
            # Phase 1: Research Agent - Data Gathering
            if progress_callback:
                await progress_callback("research_phase", {"status": "starting", "agent": "research"})
            
            research_results = await self._execute_research_phase(competitor, analysis_depth)
            
            if progress_callback:
                await progress_callback("research_phase", {"status": "completed", "results": research_results})
            
            # Phase 2: Analysis Agent - Impact Assessment
            if progress_callback:
                await progress_callback("analysis_phase", {"status": "starting", "agent": "analysis"})
            
            analysis_results = await self._execute_analysis_phase(competitor, research_results)
            
            if progress_callback:
                await progress_callback("analysis_phase", {"status": "completed", "results": analysis_results})
            
            # Phase 3: Strategy Agent - Recommendations (if requested)
            strategy_results = {}
            if include_strategy:
                if progress_callback:
                    await progress_callback("strategy_phase", {"status": "starting", "agent": "strategy"})
                
                strategy_results = await self._execute_strategy_phase(competitor, analysis_results, research_results)
                
                if progress_callback:
                    await progress_callback("strategy_phase", {"status": "completed", "results": strategy_results})
            
            # Phase 4: Synthesis - Combine all results
            if progress_callback:
                await progress_callback("synthesis_phase", {"status": "starting", "agent": "orchestrator"})
            
            comprehensive_intelligence = await self._synthesize_results(
                competitor, research_results, analysis_results, strategy_results, session_id
            )
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            comprehensive_intelligence["processing_time"] = f"{processing_time:.2f}s"
            comprehensive_intelligence["session_id"] = session_id
            
            if progress_callback:
                await progress_callback("synthesis_phase", {"status": "completed", "final_results": comprehensive_intelligence})
            
            logger.info(f"✅ Comprehensive intelligence generated for {competitor} in {processing_time:.2f}s")
            return comprehensive_intelligence
            
        except Exception as e:
            logger.error(f"❌ Comprehensive intelligence generation failed: {str(e)}")
            if progress_callback:
                await progress_callback("error", {"error": str(e), "session_id": session_id})
            raise
    
    async def _execute_research_phase(self, competitor: str, analysis_depth: str) -> Dict[str, Any]:
        """Execute research phase with Research Agent"""
        research_agent = self.agents[AgentType.RESEARCH]
        
        # Create research tasks
        tasks = []
        
        # Task 1: Gather news
        news_task = AgentTask(
            id=str(uuid.uuid4()),
            agent_type=AgentType.RESEARCH,
            task_type="gather_news",
            input_data={"competitor": competitor, "keywords": ["launch", "product", "funding", "partnership"]},
            priority=8
        )
        tasks.append(news_task)
        
        # Task 2: Search context
        context_task = AgentTask(
            id=str(uuid.uuid4()),
            agent_type=AgentType.RESEARCH,
            task_type="search_context",
            input_data={"query": f"{competitor} business strategy competitive analysis", "depth": analysis_depth},
            priority=7
        )
        tasks.append(context_task)
        
        # Execute tasks in parallel
        research_results = await asyncio.gather(
            research_agent.execute_task(news_task),
            research_agent.execute_task(context_task),
            return_exceptions=True
        )
        
        # Process results
        news_data = research_results[0] if not isinstance(research_results[0], Exception) else {}
        context_data = research_results[1] if not isinstance(research_results[1], Exception) else {}
        
        # Task 3: Validate sources (if we have data)
        if news_data.get("articles") or context_data.get("results"):
            sources_to_validate = []
            sources_to_validate.extend(news_data.get("articles", [])[:5])  # Top 5 news articles
            sources_to_validate.extend(context_data.get("results", [])[:5])  # Top 5 search results
            
            validation_task = AgentTask(
                id=str(uuid.uuid4()),
                agent_type=AgentType.RESEARCH,
                task_type="validate_sources",
                input_data={"sources": sources_to_validate},
                priority=6
            )
            
            validation_results = await research_agent.execute_task(validation_task)
        else:
            validation_results = {"validated_sources": [], "high_credibility_count": 0}
        
        return {
            "news_data": news_data,
            "context_data": context_data,
            "source_validation": validation_results,
            "research_quality_score": self._calculate_research_quality_score(news_data, context_data, validation_results)
        }
    
    async def _execute_analysis_phase(self, competitor: str, research_results: Dict[str, Any]) -> Dict[str, Any]:
        """Execute analysis phase with Analysis Agent"""
        analysis_agent = self.agents[AgentType.ANALYSIS]
        
        # Create analysis tasks
        tasks = []
        
        # Task 1: Assess impact
        impact_task = AgentTask(
            id=str(uuid.uuid4()),
            agent_type=AgentType.ANALYSIS,
            task_type="assess_impact",
            input_data={
                "news_data": research_results.get("news_data", {}),
                "context_data": research_results.get("context_data", {}),
                "competitor": competitor
            },
            priority=9
        )
        tasks.append(impact_task)
        
        # Task 2: Score risk
        risk_task = AgentTask(
            id=str(uuid.uuid4()),
            agent_type=AgentType.ANALYSIS,
            task_type="score_risk",
            input_data={
                "events": self._extract_events_from_research(research_results),
                "competitor": competitor
            },
            priority=8
        )
        tasks.append(risk_task)
        
        # Execute tasks in parallel
        analysis_results = await asyncio.gather(
            analysis_agent.execute_task(impact_task),
            analysis_agent.execute_task(risk_task),
            return_exceptions=True
        )
        
        # Process results
        impact_assessment = analysis_results[0] if not isinstance(analysis_results[0], Exception) else {}
        risk_assessment = analysis_results[1] if not isinstance(analysis_results[1], Exception) else {}
        
        # Task 3: Identify trends (if we have sufficient data)
        if impact_assessment and risk_assessment:
            trends_task = AgentTask(
                id=str(uuid.uuid4()),
                agent_type=AgentType.ANALYSIS,
                task_type="identify_trends",
                input_data={
                    "historical_data": [],  # Would be populated with historical data
                    "current_data": {
                        "impact_assessment": impact_assessment,
                        "risk_assessment": risk_assessment
                    }
                },
                priority=7
            )
            
            trends_results = await analysis_agent.execute_task(trends_task)
        else:
            trends_results = {"identified_trends": {}, "trend_strength": 0.5}
        
        return {
            "impact_assessment": impact_assessment,
            "risk_assessment": risk_assessment,
            "trends_analysis": trends_results,
            "analysis_confidence_score": self._calculate_analysis_confidence_score(impact_assessment, risk_assessment, trends_results)
        }
    
    async def _execute_strategy_phase(self, competitor: str, analysis_results: Dict[str, Any], research_results: Dict[str, Any]) -> Dict[str, Any]:
        """Execute strategy phase with Strategy Agent"""
        strategy_agent = self.agents[AgentType.STRATEGY]
        
        # Task 1: Generate recommendations
        recommendations_task = AgentTask(
            id=str(uuid.uuid4()),
            agent_type=AgentType.STRATEGY,
            task_type="generate_recommendations",
            input_data={
                "analysis_results": analysis_results,
                "competitive_landscape": self._build_competitive_landscape(research_results, analysis_results),
                "business_context": {"threat_level": analysis_results.get("risk_assessment", {}).get("overall_risk_score", 0.5)}
            },
            priority=9
        )
        
        recommendations_results = await strategy_agent.execute_task(recommendations_task)
        
        # Task 2: Assess strategic implications
        implications_task = AgentTask(
            id=str(uuid.uuid4()),
            agent_type=AgentType.STRATEGY,
            task_type="assess_strategic_implications",
            input_data={
                "competitive_moves": self._extract_competitive_moves(research_results),
                "market_context": analysis_results.get("impact_assessment", {}).get("market_implications", {})
            },
            priority=8
        )
        
        implications_results = await strategy_agent.execute_task(implications_task)
        
        return {
            "recommendations": recommendations_results,
            "strategic_implications": implications_results,
            "strategy_confidence_score": self._calculate_strategy_confidence_score(recommendations_results, implications_results)
        }
    
    async def _synthesize_results(
        self,
        competitor: str,
        research_results: Dict[str, Any],
        analysis_results: Dict[str, Any],
        strategy_results: Dict[str, Any],
        session_id: str
    ) -> Dict[str, Any]:
        """Synthesize all agent results into comprehensive intelligence"""
        
        # Calculate overall confidence score
        research_quality = research_results.get("research_quality_score", 0.5)
        analysis_confidence = analysis_results.get("analysis_confidence_score", 0.5)
        strategy_confidence = strategy_results.get("strategy_confidence_score", 0.5) if strategy_results else 0.5
        
        overall_confidence = (research_quality * 0.3 + analysis_confidence * 0.4 + strategy_confidence * 0.3)
        
        # Extract key insights
        key_insights = self._extract_key_insights(research_results, analysis_results, strategy_results)
        
        # Determine overall risk level
        risk_score = analysis_results.get("risk_assessment", {}).get("overall_risk_score", 0.5)
        risk_level = self._categorize_risk_level(risk_score)
        
        # Build comprehensive intelligence report
        comprehensive_intelligence = {
            "competitor": competitor,
            "generated_at": datetime.utcnow().isoformat(),
            "session_id": session_id,
            
            # Executive Summary
            "executive_summary": {
                "overall_risk_score": int(risk_score * 100),
                "risk_level": risk_level,
                "confidence_score": int(overall_confidence * 100),
                "key_insights": key_insights[:5],  # Top 5 insights
                "primary_threats": self._extract_primary_threats(analysis_results),
                "recommended_actions": self._extract_top_recommendations(strategy_results)
            },
            
            # Detailed Results
            "research_intelligence": {
                "data_sources": {
                    "news_articles": len(research_results.get("news_data", {}).get("articles", [])),
                    "search_results": len(research_results.get("context_data", {}).get("results", [])),
                    "validated_sources": research_results.get("source_validation", {}).get("high_credibility_count", 0)
                },
                "research_quality_score": research_quality,
                "source_credibility": research_results.get("source_validation", {})
            },
            
            "competitive_analysis": {
                "impact_assessment": analysis_results.get("impact_assessment", {}),
                "risk_breakdown": analysis_results.get("risk_assessment", {}).get("risk_scores", {}),
                "trends_identified": analysis_results.get("trends_analysis", {}).get("identified_trends", {}),
                "analysis_confidence": analysis_confidence
            },
            
            "strategic_intelligence": strategy_results if strategy_results else {},
            
            # Multi-Agent Metadata
            "multi_agent_metadata": {
                "agents_used": list(self.agents.keys()),
                "total_tasks_executed": len([t for t in self.active_tasks.values() if t.status == AgentStatus.COMPLETED]),
                "research_agent_id": self.agents[AgentType.RESEARCH].agent_id,
                "analysis_agent_id": self.agents[AgentType.ANALYSIS].agent_id,
                "strategy_agent_id": self.agents[AgentType.STRATEGY].agent_id if AgentType.STRATEGY in self.agents else None,
                "orchestration_version": "1.0.0"
            },
            
            # Quality Metrics
            "quality_metrics": {
                "overall_confidence": overall_confidence,
                "data_completeness": self._calculate_data_completeness(research_results),
                "analysis_depth": self._calculate_analysis_depth(analysis_results),
                "strategic_coverage": self._calculate_strategic_coverage(strategy_results)
            }
        }
        
        return comprehensive_intelligence
    
    def _calculate_research_quality_score(self, news_data: Dict, context_data: Dict, validation_results: Dict) -> float:
        """Calculate research quality score"""
        score = 0.0
        
        # Data volume score
        news_count = len(news_data.get("articles", []))
        context_count = len(context_data.get("results", []))
        volume_score = min((news_count + context_count) / 20, 1.0)  # Max score at 20 total items
        score += volume_score * 0.4
        
        # Source credibility score
        high_credibility_count = validation_results.get("high_credibility_count", 0)
        total_sources = len(validation_results.get("validated_sources", []))
        credibility_score = high_credibility_count / max(total_sources, 1)
        score += credibility_score * 0.6
        
        return score
    
    def _calculate_analysis_confidence_score(self, impact_assessment: Dict, risk_assessment: Dict, trends_results: Dict) -> float:
        """Calculate analysis confidence score"""
        score = 0.0
        
        # Impact assessment confidence
        if impact_assessment.get("base_analysis"):
            score += 0.4
        
        # Risk assessment confidence
        if risk_assessment.get("overall_risk_score", 0) > 0:
            score += 0.4
        
        # Trends analysis confidence
        trend_strength = trends_results.get("trend_strength", 0)
        score += trend_strength * 0.2
        
        return score
    
    def _calculate_strategy_confidence_score(self, recommendations_results: Dict, implications_results: Dict) -> float:
        """Calculate strategy confidence score"""
        score = 0.0
        
        # Recommendations quality
        recommendations = recommendations_results.get("recommendations", [])
        if recommendations:
            score += min(len(recommendations) / 5, 1.0) * 0.5  # Max score at 5 recommendations
        
        # Strategic implications depth
        implications = implications_results.get("strategic_implications", [])
        if implications:
            score += min(len(implications) / 3, 1.0) * 0.5  # Max score at 3 implications
        
        return score
    
    def _extract_events_from_research(self, research_results: Dict) -> List[Dict[str, Any]]:
        """Extract events from research results"""
        events = []
        
        # Extract from news articles
        articles = research_results.get("news_data", {}).get("articles", [])
        for article in articles[:5]:  # Top 5 articles
            events.append({
                "category": "news",
                "description": article.get("title", ""),
                "source": article.get("source", ""),
                "relevance_score": article.get("relevance_score", 0.5)
            })
        
        return events
    
    def _build_competitive_landscape(self, research_results: Dict, analysis_results: Dict) -> Dict[str, Any]:
        """Build competitive landscape from results"""
        return {
            "opportunities": [
                {"opportunity": "market_gap", "area": "product"},
                {"opportunity": "technology_advantage", "area": "innovation"}
            ],
            "threats": analysis_results.get("impact_assessment", {}).get("competitive_threats", []),
            "market_dynamics": analysis_results.get("impact_assessment", {}).get("market_implications", {})
        }
    
    def _extract_competitive_moves(self, research_results: Dict) -> List[Dict[str, Any]]:
        """Extract competitive moves from research"""
        moves = []
        
        articles = research_results.get("news_data", {}).get("articles", [])
        for article in articles[:3]:  # Top 3 articles
            if any(keyword in article.get("title", "").lower() for keyword in ["launch", "announce", "acquire"]):
                moves.append({
                    "type": "product_launch",
                    "description": article.get("title", ""),
                    "impact_level": "medium",
                    "source": article.get("source", "")
                })
        
        return moves
    
    def _extract_key_insights(self, research_results: Dict, analysis_results: Dict, strategy_results: Dict) -> List[str]:
        """Extract key insights from all results"""
        insights = []
        
        # From research
        if research_results.get("news_data", {}).get("high_relevance_count", 0) > 3:
            insights.append("High volume of relevant competitive activity detected")
        
        # From analysis
        risk_level = analysis_results.get("risk_assessment", {}).get("risk_level", "")
        if risk_level in ["high", "critical"]:
            insights.append(f"Elevated {risk_level} risk level identified")
        
        # From strategy
        if strategy_results and strategy_results.get("recommendations", {}).get("recommendations"):
            insights.append("Strategic response recommendations generated")
        
        # Add more insights based on specific findings
        impact_areas = analysis_results.get("impact_assessment", {}).get("enhanced_impact_areas", [])
        for area in impact_areas[:2]:  # Top 2 impact areas
            insights.append(f"Significant impact identified in {area.get('area', 'unknown')} area")
        
        return insights
    
    def _categorize_risk_level(self, risk_score: float) -> str:
        """Categorize risk level from score"""
        if risk_score >= 0.8:
            return "critical"
        elif risk_score >= 0.6:
            return "high"
        elif risk_score >= 0.4:
            return "medium"
        else:
            return "low"
    
    def _extract_primary_threats(self, analysis_results: Dict) -> List[str]:
        """Extract primary threats from analysis"""
        threats = []
        
        competitive_threats = analysis_results.get("impact_assessment", {}).get("competitive_threats", [])
        for threat in competitive_threats[:3]:  # Top 3 threats
            threats.append(threat.get("threat", "Unknown threat"))
        
        return threats
    
    def _extract_top_recommendations(self, strategy_results: Dict) -> List[str]:
        """Extract top recommendations from strategy results"""
        if not strategy_results:
            return []
        
        recommendations = strategy_results.get("recommendations", {}).get("recommendations", [])
        return [rec.get("action", "") for rec in recommendations[:3]]  # Top 3 recommendations
    
    def _calculate_data_completeness(self, research_results: Dict) -> float:
        """Calculate data completeness score"""
        completeness = 0.0
        
        if research_results.get("news_data", {}).get("articles"):
            completeness += 0.4
        
        if research_results.get("context_data", {}).get("results"):
            completeness += 0.4
        
        if research_results.get("source_validation", {}).get("validated_sources"):
            completeness += 0.2
        
        return completeness
    
    def _calculate_analysis_depth(self, analysis_results: Dict) -> float:
        """Calculate analysis depth score"""
        depth = 0.0
        
        if analysis_results.get("impact_assessment"):
            depth += 0.4
        
        if analysis_results.get("risk_assessment"):
            depth += 0.4
        
        if analysis_results.get("trends_analysis"):
            depth += 0.2
        
        return depth
    
    def _calculate_strategic_coverage(self, strategy_results: Dict) -> float:
        """Calculate strategic coverage score"""
        if not strategy_results:
            return 0.0
        
        coverage = 0.0
        
        if strategy_results.get("recommendations"):
            coverage += 0.6
        
        if strategy_results.get("strategic_implications"):
            coverage += 0.4
        
        return coverage
    
    async def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        if not self.agents:
            return {"status": "not_initialized"}
        
        agent_statuses = {}
        for agent_type, agent in self.agents.items():
            agent_statuses[agent_type.value] = {
                "agent_id": agent.agent_id,
                "status": agent.status.value,
                "last_task_completed": None  # Would track last completed task
            }
        
        return {
            "orchestrator_status": "active",
            "agents": agent_statuses,
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.completed_tasks)
        }

# Global multi-agent orchestrator instance
multi_agent_orchestrator = MultiAgentOrchestrator()