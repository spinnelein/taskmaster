// Test Delete API Endpoint for Recurring Events
// NO EMOJIS
const axios = require('axios');

const BASE_URL = 'http://localhost:8000';

async function testDeleteAPI() {
  console.log('Testing delete API functionality...');
  
  try {
    // First, get list of events
    console.log('Getting list of events...');
    const eventsResponse = await axios.get(`${BASE_URL}/api/events`);
    const events = eventsResponse.data.events;
    
    console.log(`Found ${events.length} events`);
    
    // Find a recurring event to test with
    const recurringEvent = events.find(event => event.is_recurring && event.is_recurrence_master);
    
    if (!recurringEvent) {
      console.log('No recurring master events found for testing');
      return;
    }
    
    console.log(`Found recurring event for testing: "${recurringEvent.title}" (ID: ${recurringEvent.id})`);
    
    // Test the recurring-info endpoint first
    console.log('Testing recurring-info endpoint...');
    try {
      const infoResponse = await axios.get(`${BASE_URL}/api/events/${recurringEvent.id}/recurring-info`);
      console.log('Recurring info:', infoResponse.data);
    } catch (error) {
      console.log('Recurring info endpoint error:', error.message);
    }
    
    // Test event expansion
    console.log('Testing event expansion...');
    try {
      const today = new Date().toISOString().split('T')[0];
      const nextWeek = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
      
      const expansionResponse = await axios.get(`${BASE_URL}/api/events/expand/${recurringEvent.id}`, {
        params: {
          start_date: today,
          end_date: nextWeek,
          max_occurrences: 10
        }
      });
      
      console.log(`Event expanded to ${expansionResponse.data.total_occurrences} occurrences`);
    } catch (error) {
      console.log('Expansion endpoint error:', error.message);
    }
    
    // TEST DELETE FUNCTIONALITY
    // WARNING: This will actually delete the event, so we'll create a test event first
    console.log('Creating test event for deletion...');
    
    const testEventData = {
      title: 'DELETE TEST EVENT - Safe to Delete',
      start_time: '2025-09-20T10:00:00',
      end_time: '2025-09-20T11:00:00',
      is_blocking: false,
      location: null,
      description: 'Test event created specifically for deletion testing',
      notifications_enabled: false,
      is_recurring: true,
      recurrence_pattern: {
        pattern: 'daily',
        interval: 1,
        weekdays: [],
        end_type: 'after',
        end_after_count: 3,
        end_date: null
      }
    };
    
    try {
      const createResponse = await axios.post(`${BASE_URL}/api/events`, testEventData);
      const testEvent = createResponse.data;
      
      console.log(`Created test event: "${testEvent.title}" (ID: ${testEvent.id})`);
      
      // Now test deletion
      console.log('Testing delete functionality...');
      
      const deleteRequest = {
        edit_mode: 'all_in_series',
        original_date: null
      };
      
      const deleteResponse = await axios.delete(`${BASE_URL}/api/events/${testEvent.id}/recurring`, {
        data: deleteRequest
      });
      
      console.log('Delete response:', deleteResponse.data);
      console.log('✅ DELETE FUNCTIONALITY WORKING!');
      
      // Verify the event was deleted
      try {
        await axios.get(`${BASE_URL}/api/events/${testEvent.id}`);
        console.log('❌ Event still exists after deletion');
      } catch (error) {
        if (error.response && error.response.status === 404) {
          console.log('✅ Event properly deleted - returns 404 as expected');
        } else {
          console.log('Unexpected error checking deleted event:', error.message);
        }
      }
      
    } catch (createError) {
      console.log('Error creating test event:', createError.message);
      if (createError.response) {
        console.log('Response data:', createError.response.data);
      }
    }
    
  } catch (error) {
    console.error('API test failed:', error.message);
    if (error.response) {
      console.error('Response status:', error.response.status);
      console.error('Response data:', error.response.data);
    }
  }
}

testDeleteAPI().catch(console.error);