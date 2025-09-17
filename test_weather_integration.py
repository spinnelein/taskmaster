#!/usr/bin/env python3
"""
Test script for weather integration with time pools
Tests the complete weather service integration in the Flask app
"""

import requests
import json
from datetime import date, timedelta

BASE_URL = "http://localhost:5000/api"

def test_weather_integration():
    """Test the complete weather integration system"""
    
    print("🌤️  Testing Weather Integration with Time Pools")
    print("=" * 60)
    
    # Test 1: Update weather data
    print("\n1. Updating weather data...")
    try:
        response = requests.post(f"{BASE_URL}/weather/update", timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Weather update: {data['message']}")
        else:
            print(f"   ❌ Weather update failed: {response.status_code}")
    except Exception as e:
        print(f"   ⚠️  Weather update error (may be expected): {e}")
    
    # Test 2: Get current weather
    print("\n2. Getting current weather...")
    try:
        response = requests.get(f"{BASE_URL}/weather/current")
        if response.status_code == 200:
            weather = response.json()
            print(f"   ✅ Current weather: {weather.get('weather_condition', 'Unknown')} - {weather.get('temp_high', 'N/A')}°F")
            print(f"   📊 Outdoor suitable: {weather.get('is_suitable_for_outdoor_work', 'Unknown')}")
            print(f"   💡 Recommendation: {weather.get('recommendation_text', 'N/A')}")
        else:
            print(f"   ⚠️  No current weather data available")
    except Exception as e:
        print(f"   ❌ Current weather error: {e}")
    
    # Test 3: Regenerate time pools
    print("\n3. Regenerating time pools...")
    try:
        response = requests.post(f"{BASE_URL}/time-pools/regenerate")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Time pools: {data['message']}")
        else:
            print(f"   ❌ Pool regeneration failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Pool regeneration error: {e}")
    
    # Give pools time to generate
    import time
    print("   ⏳ Waiting 3 seconds for pool generation...")
    time.sleep(3)
    
    # Test 4: Get time pools with weather data
    print("\n4. Getting time pools with weather data...")
    try:
        today = date.today()
        end_date = today + timedelta(days=3)
        
        response = requests.get(f"{BASE_URL}/time-pools", params={
            'start_date': today.isoformat(),
            'end_date': end_date.isoformat(),
            'include_weather': 'true'
        })
        
        if response.status_code == 200:
            data = response.json()
            pools = data.get('pools', [])
            
            print(f"   ✅ Found {len(pools)} time pools")
            print(f"   📊 Total available time: {data.get('total_minutes', 0)} minutes")
            print(f"   🌤️  Outdoor suitable pools: {data.get('outdoor_suitable', 0)}")
            
            # Show details of first few pools
            for i, pool in enumerate(pools[:3]):
                start_time = pool.get('start_time', '').split('T')[1][:5] if 'T' in pool.get('start_time', '') else 'Unknown'
                pool_date = pool.get('pool_date', 'Unknown')
                available = pool.get('available_minutes', 0)
                
                weather_info = pool.get('weather', {})
                if weather_info:
                    condition = weather_info.get('weather_condition', 'Unknown')
                    temp = weather_info.get('temp_high', 'N/A')
                    outdoor_ok = weather_info.get('is_suitable_for_outdoor_work', False)
                    recommendation = weather_info.get('recommendation', 'N/A')
                    
                    print(f"   📅 Pool {i+1}: {pool_date} {start_time} ({available}min)")
                    print(f"      🌤️  Weather: {condition} {temp}°F - Outdoor: {'✅' if outdoor_ok else '❌'}")
                    print(f"      💡 {recommendation}")
                else:
                    print(f"   📅 Pool {i+1}: {pool_date} {start_time} ({available}min) - No weather data")
        else:
            print(f"   ❌ Failed to get time pools: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Time pools error: {e}")
    
    # Test 5: Test specific weather queries
    print("\n5. Testing weather-specific endpoints...")
    try:
        # Test tasks endpoint to see if it's working
        response = requests.get(f"{BASE_URL}/tasks")
        if response.status_code == 200:
            tasks = response.json()
            print(f"   ✅ API is working - found {len(tasks)} tasks")
        else:
            print(f"   ⚠️  API may have issues: {response.status_code}")
    except Exception as e:
        print(f"   ❌ API test error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Weather integration test complete!")
    print("\nNext steps:")
    print("• Check Flask app logs for any errors")
    print("• Verify time pools are being created with weather data")
    print("• Test weather-based task scheduling recommendations")

if __name__ == "__main__":
    test_weather_integration()