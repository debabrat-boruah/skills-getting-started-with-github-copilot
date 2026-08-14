"""
Tests for core FastAPI endpoints.

Covers:
- GET /activities — retrieve all activities with participants
- POST /activities/{activity_name}/signup — register a student
- DELETE /activities/{activity_name}/participants/{email} — unregister a student
- GET / — redirect to static HTML
"""

import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self, client, app_with_test_data):
        """Verify GET /activities returns all activities in the database."""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == 9  # 9 activities in default data
        
        # Verify key activities are present
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Basketball Team" in data

    def test_get_activities_includes_participant_details(self, client, app_with_test_data):
        """Verify activity objects contain all required fields including participants."""
        response = client.get("/activities")
        data = response.json()
        
        activity = data["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        
        # Participants should be a list
        assert isinstance(activity["participants"], list)
        assert len(activity["participants"]) == 2  # Chess Club has 2 participants

    def test_get_activities_participant_list_content(self, client, app_with_test_data):
        """Verify participants list contains email addresses."""
        response = client.get("/activities")
        data = response.json()
        
        participants = data["Chess Club"]["participants"]
        assert "michael@mergington.edu" in participants
        assert "daniel@mergington.edu" in participants


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_valid_activity_and_email(self, client, app_with_test_data):
        """Verify successful signup returns 200 with success message."""
        response = client.post(
            "/activities/Art Studio/signup?email=newemail@mergington.edu"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "newemail@mergington.edu" in data["message"]
        assert "Art Studio" in data["message"]

    def test_signup_adds_email_to_participants(self, client, app_with_test_data):
        """Verify signup actually adds the email to the participants list."""
        # Pre-check: Art Studio has 1 participant
        response_before = client.get("/activities")
        art_studio_before = response_before.json()["Art Studio"]
        initial_count = len(art_studio_before["participants"])
        
        # Sign up new email
        client.post("/activities/Art Studio/signup?email=newemail@mergington.edu")
        
        # Post-check: Art Studio now has 2 participants
        response_after = client.get("/activities")
        art_studio_after = response_after.json()["Art Studio"]
        assert len(art_studio_after["participants"]) == initial_count + 1
        assert "newemail@mergington.edu" in art_studio_after["participants"]

    def test_signup_activity_not_found(self, client, app_with_test_data):
        """Verify signup returns 404 when activity does not exist."""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
        assert "Activity not found" in data["detail"]

    def test_signup_duplicate_email(self, client, app_with_test_data):
        """Verify signup returns 400 when email is already registered."""
        # Chess Club has michael@mergington.edu
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
        assert "already signed up" in data["detail"].lower()

    def test_signup_updates_availability_count(self, client, app_with_test_data):
        """Verify that signup reduces available spots."""
        # Get initial availability
        response_before = client.get("/activities")
        activity_before = response_before.json()["Tennis Club"]
        max_participants = activity_before["max_participants"]
        participants_before = len(activity_before["participants"])
        spots_left_before = max_participants - participants_before
        
        # Sign up
        client.post("/activities/Tennis Club/signup?email=newstudent@mergington.edu")
        
        # Check updated availability
        response_after = client.get("/activities")
        activity_after = response_after.json()["Tennis Club"]
        participants_after = len(activity_after["participants"])
        spots_left_after = max_participants - participants_after
        
        assert spots_left_after == spots_left_before - 1
        assert participants_after == participants_before + 1

    def test_signup_multiple_different_emails(self, client, app_with_test_data):
        """Verify multiple different emails can sign up for same activity."""
        activity = "Art Studio"
        
        # Get initial count
        response = client.get("/activities")
        initial_count = len(response.json()[activity]["participants"])
        
        # Sign up 3 different people
        emails = ["alice@mergington.edu", "bob@mergington.edu", "charlie@mergington.edu"]
        for email in emails:
            response = client.post(f"/activities/{activity}/signup?email={email}")
            assert response.status_code == 200
        
        # Verify all 3 are now signed up
        response = client.get("/activities")
        final_participants = response.json()[activity]["participants"]
        assert len(final_participants) == initial_count + 3
        for email in emails:
            assert email in final_participants


class TestDeleteParticipant:
    """Tests for DELETE /activities/{activity_name}/participants/{email} endpoint."""

    def test_delete_valid_participant(self, client, app_with_test_data):
        """Verify successful deletion returns 200 with success message."""
        response = client.delete(
            "/activities/Chess Club/participants/michael@mergington.edu"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "michael@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]

    def test_delete_removes_email_from_participants(self, client, app_with_test_data):
        """Verify deletion actually removes the email from the participants list."""
        # Pre-check: Chess Club has michael@mergington.edu
        response_before = client.get("/activities")
        chess_before = response_before.json()["Chess Club"]
        initial_count = len(chess_before["participants"])
        assert "michael@mergington.edu" in chess_before["participants"]
        
        # Delete
        client.delete("/activities/Chess Club/participants/michael@mergington.edu")
        
        # Post-check: Chess Club no longer has michael@mergington.edu
        response_after = client.get("/activities")
        chess_after = response_after.json()["Chess Club"]
        assert len(chess_after["participants"]) == initial_count - 1
        assert "michael@mergington.edu" not in chess_after["participants"]

    def test_delete_activity_not_found(self, client, app_with_test_data):
        """Verify deletion returns 404 when activity does not exist."""
        response = client.delete(
            "/activities/Nonexistent Activity/participants/test@mergington.edu"
        )
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
        assert "Activity not found" in data["detail"]

    def test_delete_participant_not_found(self, client, app_with_test_data):
        """Verify deletion returns 404 when email is not in activity."""
        response = client.delete(
            "/activities/Chess Club/participants/notregistered@mergington.edu"
        )
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
        assert "Participant not found" in data["detail"]

    def test_delete_updates_availability_count(self, client, app_with_test_data):
        """Verify that deletion increases available spots."""
        activity = "Chess Club"
        
        # Get initial availability
        response_before = client.get("/activities")
        activity_before = response_before.json()[activity]
        max_participants = activity_before["max_participants"]
        participants_before = len(activity_before["participants"])
        spots_left_before = max_participants - participants_before
        
        # Delete a participant
        client.delete(
            f"/activities/{activity}/participants/michael@mergington.edu"
        )
        
        # Check updated availability
        response_after = client.get("/activities")
        activity_after = response_after.json()[activity]
        participants_after = len(activity_after["participants"])
        spots_left_after = max_participants - participants_after
        
        assert spots_left_after == spots_left_before + 1
        assert participants_after == participants_before - 1


class TestRoot:
    """Tests for GET / endpoint."""

    def test_root_redirects_to_static(self, client, app_with_test_data):
        """Verify GET / redirects to /static/index.html."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        
        assert "location" in response.headers
        assert "/static/index.html" in response.headers["location"]

    def test_root_redirect_follows(self, client, app_with_test_data):
        """Verify the redirect can be followed (request content after redirect)."""
        response = client.get("/", follow_redirects=True)
        assert response.status_code == 200
        # Should return HTML content
        assert "html" in response.text.lower() or "<!doctype" in response.text.lower()
