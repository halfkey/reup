"""Manual test script for ProfileHandler."""
from reup.managers.profile_handler import ProfileHandler

def test_profile_operations():
    """Test basic profile operations."""
    handler = ProfileHandler(profiles_dir="test_profiles")
    
    # Test data
    test_profile = {
        'products': [
            {'name': 'Test Product 1', 'url': 'https://example.com/1'},
            {'name': 'Test Product 2', 'url': 'https://example.com/2'}
        ]
    }
    
    print("\n1. Testing save profile...")
    try:
        handler.save_profile("test1", test_profile)
        print("✓ Save successful")
    except Exception as e:
        print(f"✗ Save failed: {e}")
    
    print("\n2. Testing list profiles...")
    try:
        profiles = handler.list_profiles()
        print(f"✓ Found profiles: {profiles}")
    except Exception as e:
        print(f"✗ List failed: {e}")
    
    print("\n3. Testing load profile...")
    try:
        loaded = handler.load_profile("test1")
        print(f"✓ Loaded profile data: {loaded}")
        assert loaded == test_profile, "Loaded data doesn't match saved data"
        print("✓ Data verification passed")
    except Exception as e:
        print(f"✗ Load failed: {e}")
    
    print("\n4. Testing delete profile...")
    try:
        handler.delete_profile("test1")
        remaining = handler.list_profiles()
        print(f"✓ Profile deleted. Remaining profiles: {remaining}")
    except Exception as e:
        print(f"✗ Delete failed: {e}")
    
    print("\n5. Testing error handling...")
    try:
        handler.load_profile("nonexistent")
        print("✗ Should have raised FileNotFoundError")
    except FileNotFoundError:
        print("✓ Correctly handled nonexistent profile")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")

if __name__ == "__main__":
    test_profile_operations() 