"""
Tests for edge cases, URL encoding, and state consistency.

Covers:
- URL encoding and special characters in emails and activity names
- State consistency across sequential operations
- Boundary conditions (empty lists, full activities, etc.)
"""

import pytest
from urllib.parse import quote


class TestUrlEncoding:
    """Tests for proper URL encoding of special characters."""

    def test_signup_email_with_plus(self, client, app_with_test_data):
        """Verify emails with + character (common in email aliases) work correctly."""
        email = "student+activity@mergington.edu"
        response = client.post(
            f"/activities/Art Studio/signup?email={quote(email)}"
        )
        assert response.status_code == 200
        
        # Verify it was added
        activities_response = client.get("/activities")
        assert email in activities_response.json()["Art Studio"]["participants"]

    def test_signup_email_with_dot(self, client, app_with_test_data):
        """Verify emails with multiple dots work correctly."""
        email = "john.doe.jr@mergington.edu"
        response = client.post(
            f"/activities/Art Studio/signup?email={quote(email)}"
        )
        assert response.status_code == 200
        
        # Verify it was added
        activities_response = client.get("/activities")
        assert email in activities_response.json()["Art Studio"]["participants"]

    def test_activity_name_with_spaces(self, client, app_with_test_data):
        """Verify activity names with spaces are handled correctly."""
        # Programming Class has spaces
        response = client.post(
            f"/activities/{quote('Programming Class')}/signup?email=newprogrammer@mergington.edu"
        )
        assert response.status_code == 200
        
        # Verify it was added
        activities_response = client.get("/activities")
        assert "newprogrammer@mergington.edu" in activities_response.json()["Programming Class"]["participants"]

    def test_delete_with_url_encoded_email(self, client, app_with_test_data):
        """Verify DELETE with URL encoded email works."""
        email = "michael@mergington.edu"
        response = client.delete(
            f"/activities/Chess Club/participants/{quote(email)}"
        )
        assert response.status_code == 200
        
        # Verify it was removed
        activities_response = client.get("/activities")
        assert email not in activities_response.json()["Chess Club"]["participants"]


class TestStateConsistency:
    """Tests for state consistency across sequential operations."""

    def test_signup_then_delete_restores_state(self, client, app_with_test_data):
        """Verify signup followed by delete returns activity to original state."""
        activity = "Art Studio"
        email = "tempstudent@mergington.edu"
        
        # Get initial state
        response_initial = client.get("/activities")
        initial_participants = response_initial.json()[activity]["participants"].copy()
        initial_count = len(initial_participants)
        
        # Sign up
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Delete
        client.delete(f"/activities/{activity}/participants/{quote(email)}")
        
        # Verify back to initial state
        response_final = client.get("/activities")
        final_participants = response_final.json()[activity]["participants"]
        final_count = len(final_participants)
        
        assert final_count == initial_count
        assert email not in final_participants
        # Check that original participants are still there
        for original_email in initial_participants:
            assert original_email in final_participants

    def test_multiple_signups_same_activity_independent(self, client, app_with_test_data):
        """Verify multiple signups to same activity are all tracked correctly."""
        activity = "Art Studio"
        emails = [
            "student1@mergington.edu",
            "student2@mergington.edu",
            "student3@mergington.edu"
        ]
        
        # Sign up multiple students
        for email in emails:
            response = client.post(f"/activities/{activity}/signup?email={email}")
            assert response.status_code == 200
        
        # Verify all are registered
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity]["participants"]
        
        for email in emails:
            assert email in participants
        
        # Delete one and verify others remain
        client.delete(f"/activities/{activity}/participants/{quote(emails[1])}")
        
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity]["participants"]
        
        assert emails[0] in participants
        assert emails[1] not in participants
        assert emails[2] in participants

    def test_sequential_operations_maintain_consistency(self, client, app_with_test_data):
        """Verify complex sequence of operations maintains consistency."""
        activity = "Drama Club"
        
        # Get initial count
        response = client.get("/activities")
        initial_count = len(response.json()[activity]["participants"])
        
        # Add 2, delete 1, add 1
        client.post(f"/activities/{activity}/signup?email=e1@mergington.edu")
        client.post(f"/activities/{activity}/signup?email=e2@mergington.edu")
        client.delete(f"/activities/{activity}/participants/{quote('e1@mergington.edu')}")
        client.post(f"/activities/{activity}/signup?email=e3@mergington.edu")
        
        # Should be initial_count + 2 (net: -1 then +1)
        response = client.get("/activities")
        final_count = len(response.json()[activity]["participants"])
        final_participants = response.json()[activity]["participants"]
        
        assert final_count == initial_count + 2
        assert "e1@mergington.edu" not in final_participants
        assert "e2@mergington.edu" in final_participants
        assert "e3@mergington.edu" in final_participants


class TestBoundaryConditions:
    """Tests for boundary conditions and edge cases."""

    def test_activity_with_no_participants(self, client, app_with_test_data):
        """Verify activities with no participants are handled correctly."""
        # First, create an activity with no participants by deleting all
        activity = "Art Studio"  # Has 1 initial participant
        response = client.get("/activities")
        participants = response.json()[activity]["participants"].copy()
        
        # Delete the one participant
        client.delete(f"/activities/{activity}/participants/{quote(participants[0])}")
        
        # Verify activity still exists and has empty participants list
        response = client.get("/activities")
        activity_data = response.json()[activity]
        assert len(activity_data["participants"]) == 0
        assert activity_data["max_participants"] > 0  # Max is still defined

    def test_empty_participants_list_on_signup(self, client, app_with_test_data):
        """Verify signup works for activity that has no participants."""
        # First clear Art Studio
        activity = "Art Studio"
        response = client.get("/activities")
        original_participant = response.json()[activity]["participants"][0]
        client.delete(f"/activities/{activity}/participants/{quote(original_participant)}")
        
        # Now sign up to empty activity
        response = client.post(f"/activities/{activity}/signup?email=firstsignup@mergington.edu")
        assert response.status_code == 200
        
        # Verify signup was successful
        response = client.get("/activities")
        assert "firstsignup@mergington.edu" in response.json()[activity]["participants"]
        assert len(response.json()[activity]["participants"]) == 1

    def test_delete_from_single_participant_activity(self, client, app_with_test_data):
        """Verify deleting the only participant leaves an empty list."""
        activity = "Tennis Club"  # Has 1 participant
        
        response = client.get("/activities")
        participant = response.json()[activity]["participants"][0]
        
        # Delete the only participant
        response = client.delete(
            f"/activities/{activity}/participants/{quote(participant)}"
        )
        assert response.status_code == 200
        
        # Verify empty
        response = client.get("/activities")
        assert len(response.json()[activity]["participants"]) == 0

    def test_idempotent_delete_then_signup(self, client, app_with_test_data):
        """Verify attempting to delete non-existent participant fails, doesn't affect state."""
        activity = "Basketball Team"
        email = "nonexistent@mergington.edu"
        
        # Attempt to delete non-existent
        response = client.delete(f"/activities/{activity}/participants/{quote(email)}")
        assert response.status_code == 404
        
        # State unchanged, can still sign up with that email
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200

    def test_case_sensitivity_in_emails(self, client, app_with_test_data):
        """Verify email handling (emails should typically be case-insensitive, but test current behavior)."""
        # Note: This test documents current behavior. Emails are typically case-insensitive,
        # but the current implementation treats them literally. This test ensures consistency.
        email_lower = "teststudent@mergington.edu"
        email_upper = "TestStudent@mergington.edu"  # Different case
        
        # Sign up with lowercase
        response = client.post(f"/activities/Art Studio/signup?email={quote(email_lower)}")
        assert response.status_code == 200
        
        # Sign up with uppercase (should succeed as they're different strings currently)
        response = client.post(f"/activities/Art Studio/signup?email={quote(email_upper)}")
        # Note: Current implementation treats these as different emails
        # If case-insensitivity is desired, this test should be updated after fixing the backend
        assert response.status_code == 200  # Succeeds (treats as different)
        
        # Both should be in participants
        response = client.get("/activities")
        participants = response.json()["Art Studio"]["participants"]
        assert email_lower in participants
        assert email_upper in participants
