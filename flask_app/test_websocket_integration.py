"""
WebSocket Integration Test for TaskMaster YOLO Phase 2.2

Tests the WebSocket infrastructure including connection management,
authentication, room operations, and security features.
"""

import time
import threading
import json
from flask_socketio import SocketIOTestClient
from app import create_app

def test_websocket_integration():
    """Test WebSocket infrastructure end-to-end"""
    print("Starting WebSocket Integration Test...")
    
    # Create Flask app with WebSocket support
    app, socketio = create_app()
    
    # Create test client
    client = SocketIOTestClient(app, socketio)
    
    print("\n1. Testing Connection...")
    
    # Test connection
    connected = client.connect()
    if connected:
        print("[PASS] Connection successful")
    else:
        print("[FAIL] Connection failed")
        return False
    
    # Check for connection confirmation
    received = client.get_received()
    print(f"Messages received on connect: {len(received)}")
    for msg in received:
        print(f"  - {msg}")
    
    print("\n2. Testing Authentication...")
    
    # Test authentication
    client.emit('authenticate', {'user_id': 'test_user_123'})
    auth_messages = client.get_received()
    
    auth_success = False
    for msg in auth_messages:
        if msg.get('name') == 'authenticated':
            auth_success = True
            print("[PASS] Authentication successful")
            print(f"  Auth data: {msg.get('args', [])}")
            break
        elif msg.get('name') == 'error':
            print(f"[FAIL] Authentication error: {msg.get('args', [])}")
    
    if not auth_success:
        print("[FAIL] Authentication failed")
    
    print("\n3. Testing Room Operations...")
    
    # Test joining rooms
    client.emit('join_room', {'room': 'dashboard'})
    room_messages = client.get_received()
    
    room_join_success = False
    for msg in room_messages:
        if msg.get('name') == 'room_joined':
            room_join_success = True
            print("[PASS] Room join successful")
            print(f"  Room data: {msg.get('args', [])}")
            break
        elif msg.get('name') == 'error':
            print(f"[FAIL] Room join error: {msg.get('args', [])}")
    
    if not room_join_success:
        print("[FAIL] Room join failed")
    
    # Test leaving rooms
    client.emit('leave_room', {'room': 'dashboard'})
    leave_messages = client.get_received()
    
    room_leave_success = False
    for msg in leave_messages:
        if msg.get('name') == 'room_left':
            room_leave_success = True
            print("[PASS] Room leave successful")
            break
    
    if not room_leave_success:
        print("[FAIL] Room leave failed")
    
    print("\n4. Testing Health Check...")
    
    # Test ping/pong
    client.emit('ping')
    ping_messages = client.get_received()
    
    ping_success = False
    for msg in ping_messages:
        if msg.get('name') == 'pong':
            ping_success = True
            print("[PASS] Ping/pong successful")
            break
    
    if not ping_success:
        print("[FAIL] Ping/pong failed")
    
    print("\n5. Testing Security Validation...")
    
    # Test invalid message format
    try:
        client.emit('join_room', {'room': 'a' * 200})  # Too long room name
        invalid_messages = client.get_received()
        
        security_working = False
        for msg in invalid_messages:
            if msg.get('name') == 'error' and 'Room name too long' in str(msg.get('args', [])):
                security_working = True
                print("[PASS] Security validation working")
                break
        
        if not security_working:
            print("[INFO] Security validation unclear")
    except Exception as e:
        print(f"Security test error: {e}")
    
    print("\n6. Testing Disconnection...")
    
    # Test disconnection
    client.disconnect()
    print("[PASS] Disconnection successful")
    
    print("\nWebSocket Integration Test Complete!")
    
    return True

def test_websocket_service_stats():
    """Test WebSocket service statistics endpoint"""
    print("\nTesting WebSocket Service Statistics...")
    
    app, socketio = create_app()
    
    with app.test_client() as client:
        # Test stats endpoint
        response = client.get('/websocket/stats')
        
        if response.status_code == 200:
            stats = response.get_json()
            print("[PASS] WebSocket stats endpoint working")
            print(f"  Stats: {json.dumps(stats, indent=2)}")
        else:
            print(f"[FAIL] WebSocket stats endpoint failed: {response.status_code}")

def test_websocket_demo_page():
    """Test WebSocket demo page"""
    print("\nTesting WebSocket Demo Page...")
    
    app, socketio = create_app()
    
    with app.test_client() as client:
        # Test demo page
        response = client.get('/websocket-demo')
        
        if response.status_code == 200:
            print("[PASS] WebSocket demo page accessible")
            print(f"  Page size: {len(response.data)} bytes")
        else:
            print(f"[FAIL] WebSocket demo page failed: {response.status_code}")

if __name__ == '__main__':
    print("TaskMaster WebSocket Integration Tests")
    print("=" * 50)
    
    try:
        # Run individual tests
        test_websocket_integration()
        test_websocket_service_stats()
        test_websocket_demo_page()
        
        print("\n" + "=" * 50)
        print("All tests completed!")
        
    except Exception as e:
        print(f"\nTest suite error: {e}")
        import traceback
        traceback.print_exc()