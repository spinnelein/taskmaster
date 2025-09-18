-- Fix recurring events by converting to master/instance pattern
BEGIN TRANSACTION;

-- Update Wake Up events: Keep first one as master, delete others
UPDATE events 
SET is_recurring = 1,
    recurrence_pattern = '{"pattern":"daily","interval":1,"weekdays":[],"end_type":"never"}',
    is_recurrence_master = 1,
    description = 'Daily wake up routine'
WHERE id = '3a0b83cc-9cac-4fb3-bb36-2e6dfced176d';

DELETE FROM events 
WHERE title = 'Wake Up' 
AND id != '3a0b83cc-9cac-4fb3-bb36-2e6dfced176d';

-- Update Breakfast/Get Ready events: Keep first one as master, delete others  
UPDATE events 
SET is_recurring = 1,
    recurrence_pattern = '{"pattern":"daily","interval":1,"weekdays":[],"end_type":"never"}',
    is_recurrence_master = 1,
    description = 'Daily breakfast and morning routine'
WHERE id = 'f0d7f5e3-eb16-4f6f-9fa4-71999fa1dd66';

DELETE FROM events 
WHERE title = 'Breakfast/Get Ready' 
AND id != 'f0d7f5e3-eb16-4f6f-9fa4-71999fa1dd66'
AND (is_recurring = 0 OR is_recurring IS NULL);

-- Update Take Kids to School events: Keep first one as master, delete others
UPDATE events 
SET is_recurring = 1,
    recurrence_pattern = '{"pattern":"daily","interval":1,"weekdays":[],"end_type":"never"}',
    is_recurrence_master = 1,
    description = 'Daily school drop-off'
WHERE id = '16ce2eeb-b897-4110-881f-47fa05b8f035';

DELETE FROM events 
WHERE title = 'Take Kids to School' 
AND id != '16ce2eeb-b897-4110-881f-47fa05b8f035';

COMMIT;