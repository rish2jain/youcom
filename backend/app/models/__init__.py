"""SQLAlchemy models exposed for Alembic and metadata creation."""

# Core models
from .watch import WatchItem  # noqa: F401
from .impact_card import ImpactCard  # noqa: F401
from .company_research import CompanyResearch  # noqa: F401
from .api_call_log import ApiCallLog  # noqa: F401
from .notification import NotificationRule, NotificationLog  # noqa: F401
from .feedback import InsightFeedback  # noqa: F401

# Enterprise models
from .user import User, UserRole  # noqa: F401
from .workspace import Workspace, WorkspaceMember, WorkspaceRole  # noqa: F401
from .shared_watchlist import SharedWatchlist  # noqa: F401
from .comment import Comment  # noqa: F401
from .audit_log import AuditLog, AuditAction  # noqa: F401
from .dashboard import Dashboard, ScheduledReport  # noqa: F401
from .integration import Integration, IntegrationUsageLog, BasicIntegrationReview  # noqa: F401

# Week 4 models - Community Platform
from .community import (  # noqa: F401
    CommunityUser, CommunityContribution, CommunityValidation,
    ExpertNetwork, CommunityChallenge, CommunityInsight,
    CommunityLeaderboard
)

# Week 4 models - White-label Solutions
from .whitelabel import (  # noqa: F401
    WhiteLabelCustomer, BrandingConfiguration, DeploymentConfiguration,
    CustomIntegration, WhiteLabelUsage, SupportTicket, WhiteLabelAnalytics
)

# Week 4 models - Integration Marketplace
from .integration_marketplace import (  # noqa: F401
    IntegrationDeveloper, MarketplaceIntegration, MarketplaceIntegrationInstallation,
    IntegrationReview, IntegrationWebhook, IntegrationAnalytics,
    IntegrationPayout, IntegrationSupport, MarketplaceSettings
)

# Advanced Intelligence Suite - ML Training models
from .ml_training import (  # noqa: F401
    FeedbackRecord, ModelPerformanceMetric, TrainingJob
)

# Advanced Intelligence Suite - Model Registry
from .ml_model_registry import ModelRegistryRecord, ABTestRecord  # noqa: F401

# Advanced Intelligence Suite - Industry Templates
from .industry_template import IndustryTemplate, TemplateApplication  # noqa: F401

# Advanced Intelligence Suite - Benchmarking
from .benchmarking import (  # noqa: F401
    BenchmarkResult, MetricsSnapshot, TrendAnalysis, 
    PerformanceAlert, BenchmarkComparison
)

# Advanced Intelligence Suite - Sentiment Analysis
from .sentiment_analysis import (  # noqa: F401
    SentimentAnalysis, SentimentTrend, SentimentAlert, SentimentProcessingQueue
)

# Advanced Intelligence Suite - HubSpot Integration
from .hubspot_integration import (  # noqa: F401
    HubSpotIntegration, HubSpotSyncLog, HubSpotCustomProperty, HubSpotWorkflowTrigger
)

# Advanced Intelligence Suite - Obsidian Integration
from .obsidian_integration import (  # noqa: F401
    ObsidianIntegration, ObsidianSyncLog, ObsidianNoteMapping, ObsidianNoteTemplate
)

# Timeline and Action Tracking
from .insight_timeline import InsightTimeline  # noqa: F401
from .action_tracker import ActionItem  # noqa: F401
