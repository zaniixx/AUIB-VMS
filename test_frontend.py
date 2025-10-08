#!/usr/bin/env python
"""
Frontend Validation Test Script
Tests that the new frontend components are properly integrated
"""

from vms import create_app
from flask import url_for
import os

def test_app_creation():
    """Test that the Flask app creates without errors"""
    try:
        app = create_app()
        print("✓ App created successfully")
        return app
    except Exception as e:
        print(f"✗ Failed to create app: {e}")
        return None

def test_static_files(app):
    """Test that static files exist in the correct location"""
    static_folder = app.static_folder
    print(f"\n📁 Static folder: {static_folder}")
    
    required_files = [
        'css/design-system.css',
        'css/base.css',
        'css/components.css',
        'js/app.js'
    ]
    
    all_exist = True
    for file in required_files:
        filepath = os.path.join(static_folder, file)
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            print(f"  ✓ {file} ({size:,} bytes)")
        else:
            print(f"  ✗ {file} NOT FOUND")
            all_exist = False
    
    return all_exist

def test_routes(app):
    """Test that key routes can be generated"""
    print("\n🔗 Testing routes:")
    
    with app.app_context():
        routes_to_test = [
            ('auth.home_page', 'Home'),
            ('auth.login', 'Login'),
            ('auth.register', 'Register'),
            ('auth.logout', 'Logout'),
            ('auth.volunteer_dashboard', 'Volunteer Dashboard'),
            ('officer.create_event', 'Create Event'),
            ('officer.approvals', 'Approvals'),
            ('officer.reports', 'Reports'),
            ('club.submit_hours', 'Submit Hours'),
            ('admin.settings', 'Admin Settings'),
            ('admin.users', 'Admin Users'),
        ]
        
        all_pass = True
        for endpoint, name in routes_to_test:
            try:
                url = url_for(endpoint)
                print(f"  ✓ {name:25s} -> {url}")
            except Exception as e:
                print(f"  ✗ {name:25s} -> ERROR: {e}")
                all_pass = False
        
        # Test static file URLs
        try:
            css_url = url_for('static', filename='css/design-system.css')
            js_url = url_for('static', filename='js/app.js')
            print(f"  ✓ {'Static CSS':25s} -> {css_url}")
            print(f"  ✓ {'Static JS':25s} -> {js_url}")
        except Exception as e:
            print(f"  ✗ Static files -> ERROR: {e}")
            all_pass = False
        
        return all_pass

def test_templates(app):
    """Test that key templates exist"""
    print("\n📄 Testing templates:")
    
    template_folder = app.template_folder
    required_templates = [
        'base.html',
        '_header.html',
        '_macros.html',
        'login.html',
        'register.html',
        'home_guest.html',
    ]
    
    all_exist = True
    for template in required_templates:
        filepath = os.path.join(template_folder, template)
        if os.path.exists(filepath):
            print(f"  ✓ {template}")
        else:
            print(f"  ✗ {template} NOT FOUND")
            all_exist = False
    
    return all_exist

def test_template_rendering(app):
    """Test that templates can be rendered without errors"""
    print("\n🎨 Testing template rendering:")
    
    with app.test_client() as client:
        # Test unauthenticated routes
        routes_to_test = [
            ('/', 'Home'),
            ('/login', 'Login'),
            ('/register', 'Register'),
        ]
        
        all_pass = True
        for route, name in routes_to_test:
            try:
                response = client.get(route)
                if response.status_code in [200, 302]:  # 302 for redirects
                    print(f"  ✓ {name:20s} (Status: {response.status_code})")
                else:
                    print(f"  ⚠ {name:20s} (Status: {response.status_code})")
            except Exception as e:
                print(f"  ✗ {name:20s} ERROR: {e}")
                all_pass = False
        
        return all_pass

def main():
    """Run all tests"""
    print("=" * 60)
    print("AUIB VMS Frontend Validation Test")
    print("=" * 60)
    
    # Test 1: App creation
    app = test_app_creation()
    if not app:
        print("\n❌ Cannot proceed with tests - app creation failed")
        return False
    
    # Test 2: Static files
    static_ok = test_static_files(app)
    
    # Test 3: Routes
    routes_ok = test_routes(app)
    
    # Test 4: Templates
    templates_ok = test_templates(app)
    
    # Test 5: Template rendering
    rendering_ok = test_template_rendering(app)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Static Files:      {'✓ PASS' if static_ok else '✗ FAIL'}")
    print(f"Routes:            {'✓ PASS' if routes_ok else '✗ FAIL'}")
    print(f"Templates:         {'✓ PASS' if templates_ok else '✗ FAIL'}")
    print(f"Rendering:         {'✓ PASS' if rendering_ok else '✗ FAIL'}")
    
    all_pass = static_ok and routes_ok and templates_ok and rendering_ok
    print("=" * 60)
    if all_pass:
        print("✅ ALL TESTS PASSED!")
        print("\nYour frontend rebuild is working correctly!")
        print("You can start the server with: python app.py")
    else:
        print("⚠️  SOME TESTS FAILED")
        print("Review the errors above and fix any issues.")
    print("=" * 60)
    
    return all_pass

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
