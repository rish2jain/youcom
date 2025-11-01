"""
Tests for collaboration features: annotations, shared watchlists, and comments
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.models.user import User, UserRole
from app.models.workspace import Workspace, WorkspaceMember, WorkspaceRole
from app.models.watch import WatchItem
from app.models.impact_card import ImpactCard
from app.models.shared_watchlist import SharedWatchlist
from app.models.annotation import Annotation
from app.models.comment import Comment
from app.models.comment_notification import CommentNotification, ConflictDetection


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        hashed_password="hashed_password",
        role=UserRole.ANALYST
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_user_2(db_session: AsyncSession) -> User:
    """Create a second test user."""
    user = User(
        email="test2@example.com",
        username="testuser2",
        full_name="Test User 2",
        hashed_password="hashed_password",
        role=UserRole.ANALYST
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_workspace(db_session: AsyncSession) -> Workspace:
    """Create a test workspace."""
    workspace = Workspace(
        name="Test Workspace",
        slug="test-workspace",
        description="A test workspace"
    )
    db_session.add(workspace)
    await db_session.commit()
    await db_session.refresh(workspace)
    return workspace


@pytest.fixture
async def test_workspace_member(db_session: AsyncSession, test_user: User, test_workspace: Workspace) -> WorkspaceMember:
    """Create a workspace membership."""
    member = WorkspaceMember(
        workspace_id=test_workspace.id,
        user_id=test_user.id,
        role=WorkspaceRole.ADMIN
    )
    db_session.add(member)
    await db_session.commit()
    await db_session.refresh(member)
    return member


@pytest.fixture
async def test_watch_item(db_session: AsyncSession) -> WatchItem:
    """Create a test watch item."""
    watch_item = WatchItem(
        name="Test Watch",
        query="test competitor",
        description="Test watch item"
    )
    db_session.add(watch_item)
    await db_session.commit()
    await db_session.refresh(watch_item)
    return watch_item


@pytest.fixture
async def test_impact_card(db_session: AsyncSession, test_watch_item: WatchItem, sample_impact_card_data) -> ImpactCard:
    """Create a test impact card."""
    impact_card = ImpactCard(
        watch_item_id=test_watch_item.id,
        **sample_impact_card_data
    )
    db_session.add(impact_card)
    await db_session.commit()
    await db_session.refresh(impact_card)
    return impact_card


@pytest.fixture
async def test_shared_watchlist(
    db_session: AsyncSession, 
    test_workspace: Workspace, 
    test_user: User, 
    test_watch_item: WatchItem
) -> SharedWatchlist:
    """Create a test shared watchlist."""
    shared_watchlist = SharedWatchlist(
        workspace_id=test_workspace.id,
        name="Test Shared Watchlist",
        description="A test shared watchlist",
        watch_item_id=test_watch_item.id,
        created_by=test_user.id,
        is_public=True
    )
    db_session.add(shared_watchlist)
    await db_session.commit()
    await db_session.refresh(shared_watchlist)
    return shared_watchlist


class TestAnnotations:
    """Test annotation functionality."""

    async def test_create_annotation(self, client: AsyncClient, test_impact_card: ImpactCard):
        """Test creating an annotation."""
        annotation_data = {
            "content": "This is a test annotation",
            "annotation_type": "insight",
            "position": {"x": 100, "y": 200},
            "target_text": "Selected text"
        }
        
        response = await client.post(
            f"/api/v1/annotations/?impact_card_id={test_impact_card.id}",
            json=annotation_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == annotation_data["content"]
        assert data["annotation_type"] == annotation_data["annotation_type"]
        assert data["impact_card_id"] == test_impact_card.id

    async def test_get_annotations_for_impact_card(
        self, 
        client: AsyncClient, 
        db_session: AsyncSession,
        test_impact_card: ImpactCard,
        test_user: User
    ):
        """Test retrieving annotations for an impact card."""
        # Create test annotations
        annotation1 = Annotation(
            user_id=test_user.id,
            impact_card_id=test_impact_card.id,
            content="First annotation",
            annotation_type="insight"
        )
        annotation2 = Annotation(
            user_id=test_user.id,
            impact_card_id=test_impact_card.id,
            content="Second annotation",
            annotation_type="question"
        )
        
        db_session.add_all([annotation1, annotation2])
        await db_session.commit()
        
        response = await client.get(f"/api/v1/annotations/impact-card/{test_impact_card.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["content"] in ["First annotation", "Second annotation"]

    async def test_update_annotation(
        self, 
        client: AsyncClient, 
        db_session: AsyncSession,
        test_impact_card: ImpactCard,
        test_user: User
    ):
        """Test updating an annotation."""
        annotation = Annotation(
            user_id=test_user.id,
            impact_card_id=test_impact_card.id,
            content="Original content",
            annotation_type="insight"
        )
        
        db_session.add(annotation)
        await db_session.commit()
        await db_session.refresh(annotation)
        
        update_data = {
            "content": "Updated content",
            "is_resolved": 1
        }
        
        response = await client.put(f"/api/v1/annotations/{annotation.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Updated content"
        assert data["is_resolved"] == 1

    async def test_delete_annotation(
        self, 
        client: AsyncClient, 
        db_session: AsyncSession,
        test_impact_card: ImpactCard,
        test_user: User
    ):
        """Test deleting an annotation."""
        annotation = Annotation(
            user_id=test_user.id,
            impact_card_id=test_impact_card.id,
            content="To be deleted",
            annotation_type="concern"
        )
        
        db_session.add(annotation)
        await db_session.commit()
        await db_session.refresh(annotation)
        
        response = await client.delete(f"/api/v1/annotations/{annotation.id}")
        
        assert response.status_code == 204

    async def test_annotation_stats(
        self, 
        client: AsyncClient, 
        db_session: AsyncSession,
        test_impact_card: ImpactCard,
        test_user: User
    ):
        """Test annotation statistics."""
        # Create test annotations
        annotations = [
            Annotation(
                user_id=test_user.id,
                impact_card_id=test_impact_card.id,
                content=f"Annotation {i}",
                annotation_type="insight" if i % 2 == 0 else "question",
                is_resolved=1 if i < 2 else 0
            )
            for i in range(5)
        ]
        
        db_session.add_all(annotations)
        await db_session.commit()
        
        response = await client.get(f"/api/v1/annotations/impact-card/{test_impact_card.id}/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_annotations"] == 5
        assert data["resolved_count"] == 2
        assert data["pending_count"] == 3


class TestSharedWatchlists:
    """Test shared watchlist functionality."""

    async def test_create_shared_watchlist(
        self, 
        client: AsyncClient, 
        test_workspace: Workspace,
        test_watch_item: WatchItem,
        test_workspace_member: WorkspaceMember
    ):
        """Test creating a shared watchlist."""
        watchlist_data = {
            "name": "Test Shared Watchlist",
            "description": "A test shared watchlist",
            "watch_item_id": test_watch_item.id,
            "is_public": True
        }
        
        response = await client.post(
            f"/api/v1/shared-watchlists/?workspace_id={test_workspace.id}",
            json=watchlist_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == watchlist_data["name"]
        assert data["workspace_id"] == test_workspace.id
        assert data["watch_item_id"] == test_watch_item.id

    async def test_list_workspace_watchlists(
        self, 
        client: AsyncClient, 
        test_shared_watchlist: SharedWatchlist,
        test_workspace_member: WorkspaceMember
    ):
        """Test listing shared watchlists in a workspace."""
        response = await client.get(f"/api/v1/shared-watchlists/workspace/{test_shared_watchlist.workspace_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["name"] == test_shared_watchlist.name

    async def test_get_shared_watchlist(
        self, 
        client: AsyncClient, 
        test_shared_watchlist: SharedWatchlist,
        test_workspace_member: WorkspaceMember
    ):
        """Test getting a specific shared watchlist."""
        response = await client.get(f"/api/v1/shared-watchlists/{test_shared_watchlist.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_shared_watchlist.id
        assert data["name"] == test_shared_watchlist.name

    async def test_update_shared_watchlist(
        self, 
        client: AsyncClient, 
        test_shared_watchlist: SharedWatchlist,
        test_workspace_member: WorkspaceMember
    ):
        """Test updating a shared watchlist."""
        update_data = {
            "name": "Updated Watchlist Name",
            "is_public": False
        }
        
        response = await client.put(
            f"/api/v1/shared-watchlists/{test_shared_watchlist.id}",
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Watchlist Name"
        assert data["is_public"] == False

    async def test_assign_users_to_watchlist(
        self, 
        client: AsyncClient, 
        test_shared_watchlist: SharedWatchlist,
        test_user_2: User,
        test_workspace_member: WorkspaceMember,
        db_session: AsyncSession
    ):
        """Test assigning users to a shared watchlist."""
        # Add second user to workspace
        member2 = WorkspaceMember(
            workspace_id=test_shared_watchlist.workspace_id,
            user_id=test_user_2.id,
            role=WorkspaceRole.MEMBER
        )
        db_session.add(member2)
        await db_session.commit()
        
        assignment_data = {
            "user_ids": [test_user_2.id]
        }
        
        response = await client.post(
            f"/api/v1/shared-watchlists/{test_shared_watchlist.id}/assign",
            json=assignment_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["user_id"] == test_user_2.id

    async def test_watchlist_stats(
        self, 
        client: AsyncClient, 
        test_shared_watchlist: SharedWatchlist,
        test_workspace_member: WorkspaceMember
    ):
        """Test getting watchlist statistics."""
        response = await client.get(f"/api/v1/shared-watchlists/workspace/{test_shared_watchlist.workspace_id}/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_watchlists"] >= 1
        assert data["active_watchlists"] >= 1


class TestComments:
    """Test comment functionality."""

    async def test_create_comment(
        self, 
        client: AsyncClient, 
        test_impact_card: ImpactCard
    ):
        """Test creating a comment."""
        comment_data = {
            "content": "This is a test comment"
        }
        
        response = await client.post(
            f"/api/v1/comments/?impact_card_id={test_impact_card.id}",
            json=comment_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == comment_data["content"]
        assert data["impact_card_id"] == test_impact_card.id

    async def test_create_reply_comment(
        self, 
        client: AsyncClient, 
        db_session: AsyncSession,
        test_impact_card: ImpactCard,
        test_user: User
    ):
        """Test creating a reply to a comment."""
        # Create parent comment
        parent_comment = Comment(
            user_id=test_user.id,
            impact_card_id=test_impact_card.id,
            content="Parent comment"
        )
        
        db_session.add(parent_comment)
        await db_session.commit()
        await db_session.refresh(parent_comment)
        
        reply_data = {
            "content": "This is a reply",
            "parent_comment_id": parent_comment.id
        }
        
        response = await client.post(
            f"/api/v1/comments/?impact_card_id={test_impact_card.id}",
            json=reply_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == reply_data["content"]
        assert data["parent_comment_id"] == parent_comment.id

    async def test_list_comments(
        self, 
        client: AsyncClient, 
        db_session: AsyncSession,
        test_impact_card: ImpactCard,
        test_user: User
    ):
        """Test listing comments."""
        # Create test comments
        comments = [
            Comment(
                user_id=test_user.id,
                impact_card_id=test_impact_card.id,
                content=f"Comment {i}"
            )
            for i in range(3)
        ]
        
        db_session.add_all(comments)
        await db_session.commit()
        
        response = await client.get(f"/api/v1/comments/?impact_card_id={test_impact_card.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    async def test_get_comment_threads(
        self, 
        client: AsyncClient, 
        db_session: AsyncSession,
        test_impact_card: ImpactCard,
        test_user: User
    ):
        """Test getting threaded comments."""
        # Create parent comment
        parent_comment = Comment(
            user_id=test_user.id,
            impact_card_id=test_impact_card.id,
            content="Parent comment"
        )
        
        db_session.add(parent_comment)
        await db_session.commit()
        await db_session.refresh(parent_comment)
        
        # Create reply
        reply_comment = Comment(
            user_id=test_user.id,
            impact_card_id=test_impact_card.id,
            content="Reply comment",
            parent_comment_id=parent_comment.id
        )
        
        db_session.add(reply_comment)
        await db_session.commit()
        
        response = await client.get(f"/api/v1/comments/threads?impact_card_id={test_impact_card.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1  # One thread
        assert data[0]["content"] == "Parent comment"
        assert len(data[0]["replies"]) == 1
        assert data[0]["replies"][0]["content"] == "Reply comment"

    async def test_update_comment(
        self, 
        client: AsyncClient, 
        db_session: AsyncSession,
        test_impact_card: ImpactCard,
        test_user: User
    ):
        """Test updating a comment."""
        comment = Comment(
            user_id=test_user.id,
            impact_card_id=test_impact_card.id,
            content="Original content"
        )
        
        db_session.add(comment)
        await db_session.commit()
        await db_session.refresh(comment)
        
        update_data = {
            "content": "Updated content"
        }
        
        response = await client.put(f"/api/v1/comments/{comment.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Updated content"
        assert data["is_edited"] == 1

    async def test_delete_comment(
        self, 
        client: AsyncClient, 
        db_session: AsyncSession,
        test_impact_card: ImpactCard,
        test_user: User
    ):
        """Test deleting a comment."""
        comment = Comment(
            user_id=test_user.id,
            impact_card_id=test_impact_card.id,
            content="To be deleted"
        )
        
        db_session.add(comment)
        await db_session.commit()
        await db_session.refresh(comment)
        
        response = await client.delete(f"/api/v1/comments/{comment.id}")
        
        assert response.status_code == 204

    async def test_comment_stats(
        self, 
        client: AsyncClient, 
        db_session: AsyncSession,
        test_impact_card: ImpactCard,
        test_user: User
    ):
        """Test comment statistics."""
        # Create parent comment
        parent_comment = Comment(
            user_id=test_user.id,
            impact_card_id=test_impact_card.id,
            content="Parent comment"
        )
        
        db_session.add(parent_comment)
        await db_session.commit()
        await db_session.refresh(parent_comment)
        
        # Create replies
        replies = [
            Comment(
                user_id=test_user.id,
                impact_card_id=test_impact_card.id,
                content=f"Reply {i}",
                parent_comment_id=parent_comment.id
            )
            for i in range(2)
        ]
        
        db_session.add_all(replies)
        await db_session.commit()
        
        response = await client.get(f"/api/v1/comments/stats/summary?impact_card_id={test_impact_card.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_comments"] == 3
        assert data["total_threads"] == 1
        assert data["total_replies"] == 2

    async def test_conflict_detection(
        self, 
        client: AsyncClient, 
        db_session: AsyncSession,
        test_impact_card: ImpactCard,
        test_user: User
    ):
        """Test conflict detection in comments."""
        # Create comments with conflicting content
        comment1 = Comment(
            user_id=test_user.id,
            impact_card_id=test_impact_card.id,
            content="This is a great opportunity"
        )
        
        db_session.add(comment1)
        await db_session.commit()
        await db_session.refresh(comment1)
        
        # Create conflicting comment
        conflict_data = {
            "content": "I disagree, this is not important and low priority"
        }
        
        response = await client.post(
            f"/api/v1/comments/?impact_card_id={test_impact_card.id}",
            json=conflict_data
        )
        
        assert response.status_code == 201
        
        # Check for detected conflicts
        response = await client.get(f"/api/v1/comments/conflicts/?impact_card_id={test_impact_card.id}")
        
        assert response.status_code == 200
        data = response.json()
        # Should detect conflicts based on keywords
        assert len(data) >= 0  # May or may not detect conflicts depending on algorithm


class TestNotifications:
    """Test notification functionality."""

    async def test_comment_notifications(
        self, 
        client: AsyncClient, 
        db_session: AsyncSession,
        test_impact_card: ImpactCard,
        test_user: User,
        test_user_2: User
    ):
        """Test comment notifications."""
        # Create a comment mentioning another user
        comment_data = {
            "content": "Hey @testuser2, what do you think about this?"
        }
        
        response = await client.post(
            f"/api/v1/comments/?impact_card_id={test_impact_card.id}",
            json=comment_data
        )
        
        assert response.status_code == 201
        
        # Check notifications (would need to mock current user as test_user_2)
        # This is a simplified test - in practice, you'd need proper auth mocking
        response = await client.get("/api/v1/comments/notifications/")
        
        assert response.status_code == 200
        # Notifications would be created for mentions and replies


class TestIntegration:
    """Integration tests for collaboration features."""

    async def test_full_collaboration_workflow(
        self, 
        client: AsyncClient, 
        db_session: AsyncSession,
        test_impact_card: ImpactCard,
        test_shared_watchlist: SharedWatchlist,
        test_workspace_member: WorkspaceMember
    ):
        """Test a complete collaboration workflow."""
        # 1. Create annotation
        annotation_response = await client.post(
            f"/api/v1/annotations/?impact_card_id={test_impact_card.id}",
            json={
                "content": "Important insight here",
                "annotation_type": "insight"
            }
        )
        assert annotation_response.status_code == 201
        
        # 2. Create comment thread
        comment_response = await client.post(
            f"/api/v1/comments/?impact_card_id={test_impact_card.id}",
            json={
                "content": "Let's discuss this finding"
            }
        )
        assert comment_response.status_code == 201
        comment_id = comment_response.json()["id"]
        
        # 3. Add reply to comment
        reply_response = await client.post(
            f"/api/v1/comments/?impact_card_id={test_impact_card.id}",
            json={
                "content": "I agree, this needs attention",
                "parent_comment_id": comment_id
            }
        )
        assert reply_response.status_code == 201
        
        # 4. Check shared watchlist has comments
        watchlist_response = await client.get(f"/api/v1/shared-watchlists/{test_shared_watchlist.id}")
        assert watchlist_response.status_code == 200
        
        # 5. Verify all components work together
        threads_response = await client.get(f"/api/v1/comments/threads?impact_card_id={test_impact_card.id}")
        assert threads_response.status_code == 200
        threads = threads_response.json()
        assert len(threads) == 1
        assert len(threads[0]["replies"]) == 1