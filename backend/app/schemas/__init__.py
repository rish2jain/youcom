# Schemas package

# ML Feedback schemas
from .ml_feedback import (
    FeedbackCreate, FeedbackResponse, FeedbackBatch, FeedbackStats,
    OneClickFeedback, FeedbackFilter, FeedbackType, ExpertiseLevel
)

# Industry Template schemas
from .industry_template import (
    IndustryTemplateCreate, IndustryTemplateUpdate, IndustryTemplateResponse,
    IndustryTemplateMetadata, TemplateApplicationCreate, TemplateApplicationUpdate,
    TemplateApplicationResponse, TemplateRating, TemplateSearchRequest,
    TemplateFilter, TemplateStatistics, IndustryList, TemplateConfigValidation,
    BulkTemplateOperation, TemplateExport, TemplateStatus
)

# Sentiment Analysis schemas
from .sentiment import (
    SentimentAnalysisCreate, SentimentAnalysisUpdate, SentimentAnalysisResponse,
    SentimentTrendCreate, SentimentTrendResponse, SentimentAlertCreate,
    SentimentAlertUpdate, SentimentAlertResponse, SentimentProcessingQueueCreate,
    SentimentProcessingQueueUpdate, SentimentProcessingQueueResponse,
    EntitySentimentSummary, SentimentVisualizationData, SentimentAnalysisStats,
    BulkSentimentRequest, BulkSentimentResponse, SentimentWebSocketMessage,
    SentimentSystemHealth
)

# HubSpot Integration schemas
from .hubspot_integration import (
    HubSpotOAuthRequest, HubSpotOAuthResponse, HubSpotTokenExchange,
    HubSpotIntegrationCreate, HubSpotIntegrationUpdate, HubSpotIntegrationResponse,
    HubSpotSyncRequest, HubSpotSyncLogResponse, HubSpotHealthCheckResponse,
    HubSpotLeadEnrichmentRequest, HubSpotLeadEnrichmentResponse,
    HubSpotWorkflowTriggerRequest, HubSpotWorkflowTriggerResponse,
    HubSpotCustomPropertyResponse, HubSpotIntegrationStats, HubSpotErrorResponse
)

# Obsidian Integration schemas
from .obsidian_integration import (
    ObsidianIntegrationCreate, ObsidianIntegrationUpdate, ObsidianIntegrationResponse,
    ObsidianSyncRequest, ObsidianSyncResponse, ObsidianSyncStatusResponse,
    ObsidianHealthCheckResponse, ObsidianNoteTemplateCreate, ObsidianNoteTemplateUpdate,
    ObsidianNoteTemplateResponse, ObsidianNoteMappingResponse, ObsidianSyncLogResponse,
    ObsidianExportRequest, ObsidianExportResponse, ObsidianVaultInfoResponse,
    ObsidianNoteSearchRequest, ObsidianNoteSearchResponse
)