-- The N+1 Query Sequence: 1 initial query + 100 child queries
SELECT * FROM orders LIMIT 100;                           -- Round-Trip 1: Returns 100 parent rows
SELECT * FROM order_lines WHERE order_id = 1;             -- Round-Trip 2: Fetches child lines
SELECT * FROM order_lines WHERE order_id = 2;             -- Round-Trip 3: Fetches child lines
-- ... repeats for all 100 orders                         -- Round-Trip 101: 303ms transit delay!
