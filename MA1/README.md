# How to run

1. Run one instance of Server.py (does not need to be interacted with after being run)

2. Run as many instances of Client.py as you want (minimum two). And start giving inputs as the clients.

- Advisees can ask questions right away, but Advisors will not recieve them until they have pressed enter to signal that they are ready. Server.py uses a queue to keep track of available advisors. By pressing enter at the start, the Advisor enters the queue. When answering a question they are assigned to an Advisee and removed from the queue. If the Advisee is told "No available advisor, try again later", the queue is empty. All Advisors have either not pressed enter at the start or is assigned to another Advisee.