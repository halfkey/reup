"""Tests for profile management logic."""

import pytest
from pathlib import Path
from reup.managers.profile_handler import ProfileHandler


@pytest.fixture
def profile_handler(tmp_path):
    """Create ProfileHandler with temporary directory."""
    return ProfileHandler(profiles_dir=tmp_path)


def test_save_and_load_profile(profile_handler):
    """Test saving and loading a profile."""
    # Test data
    profile_data = {
        "products": [{"name": "Test Product", "url": "https://example.com/product"}]
    }

    # Save profile
    profile_handler.save_profile("test_profile", profile_data)

    # Load and verify
    loaded_data = profile_handler.load_profile("test_profile")
    assert loaded_data == profile_data


def test_list_profiles(profile_handler):
    """Test listing available profiles."""
    # Create test profiles
    profiles = {"profile1": {"products": []}, "profile2": {"products": []}}

    for name, data in profiles.items():
        profile_handler.save_profile(name, data)

    # List and verify
    available_profiles = profile_handler.list_profiles()
    assert sorted(available_profiles) == sorted(profiles.keys())


def test_delete_profile(profile_handler):
    """Test profile deletion."""
    # Create and then delete a profile
    profile_handler.save_profile("test_profile", {"products": []})
    assert "test_profile" in profile_handler.list_profiles()

    profile_handler.delete_profile("test_profile")
    assert "test_profile" not in profile_handler.list_profiles()


def test_error_handling(profile_handler):
    """Test error conditions."""
    # Test empty profile name
    with pytest.raises(ValueError):
        profile_handler.save_profile("", {})

    # Test loading non-existent profile
    with pytest.raises(FileNotFoundError):
        profile_handler.load_profile("nonexistent")

    # Test deleting non-existent profile
    with pytest.raises(FileNotFoundError):
        profile_handler.delete_profile("nonexistent")
