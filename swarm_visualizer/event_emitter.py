from pydantic import BaseModel
import json
import asyncio # For potential async operations if needed by WebSocket library

class EventEmitter:
    def __init__(self):
        self.clients = set() # Using a set for efficient add/remove

    async def add_client(self, websocket_client):
        """Adds a new WebSocket client to the list."""
        self.clients.add(websocket_client)
        print(f"Client added. Total clients: {len(self.clients)}")

    def remove_client(self, websocket_client):
        """Removes a WebSocket client from the list."""
        self.clients.discard(websocket_client) # Use discard to avoid errors if not found
        print(f"Client removed. Total clients: {len(self.clients)}")

    async def broadcast(self, message: str):
        """Sends a message to all connected WebSocket clients."""
        # Create a list of tasks for sending messages
        # This allows messages to be sent concurrently without waiting for each one
        if not self.clients:
            # print("No clients connected, message not broadcast.")
            return

        tasks = [client.send_text(message) for client in self.clients]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Handle error, e.g., client disconnected abruptly
                # Potentially remove the client: self.remove_client(list(self.clients)[i])
                # This part needs careful handling to map results back to clients if removal is needed here.
                # For now, just log. The main server loop should handle disconnections more robustly.
                print(f"Error sending message to a client: {result}")


    async def emit(self, event_name: str, data: BaseModel):
        """
        Emits an event by serializing it to JSON and broadcasting to all clients.
        The event_name is implicitly part of data.event_type.
        """
        try:
            json_data = data.model_dump_json(indent=None) #indent=None for more compact messages
            # print(f"Emitting Event: {json_data}") # Keep for server-side logging if desired
            await self.broadcast(json_data)
        except Exception as e:
            print(f"Error during event emission: {e}")


# Global emitter instance
emitter = EventEmitter()

# Example Usage (can be removed later or kept for testing emitter directly)
if __name__ == "__main__":
    # This example won't run directly with asyncio broadcast without a loop
    # and mock WebSocket clients.
    # For testing, you'd typically integrate with an actual WebSocket server setup.

    from swarm_visualizer.event_definitions import SwarmRunStartEvent, BaseEvent
    import time

    class TestEvent(BaseEvent):
        event_type: str = "TEST_EVENT"
        message: str

    # To test emitter.emit, you'd need an asyncio event loop
    async def main_test():
        # Mock WebSocket client for testing
        class MockWebSocketClient:
            async def send_text(self, message):
                print(f"MockClient received: {message}")

        client1 = MockWebSocketClient()
        await emitter.add_client(client1)

        await emitter.emit("SWARM_RUN_START", SwarmRunStartEvent(config={"llm": "gpt-4-test", "temperature": 0.7}))
        await emitter.emit("TEST_EVENT", TestEvent(message="This is an async test"))

        emitter.remove_client(client1)

    if False: # Disable direct run of this block, server will use it
         asyncio.run(main_test())
