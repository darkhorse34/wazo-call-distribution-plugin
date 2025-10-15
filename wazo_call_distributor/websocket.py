"""WebSocket handler for real-time events."""

import json
import asyncio
import websockets
import redis.asyncio as aioredis
from typing import Dict, Set, Optional
from datetime import datetime

class WebSocketHandler:
    """Handler for WebSocket connections."""
    
    def __init__(self, redis_url: str):
        """Initialize the WebSocket handler."""
        self.redis_url = redis_url
        self.connections: Dict[str, Set[websockets.WebSocketServerProtocol]] = {
            'tenant': {},
            'queue': {},
            'agent': {}
        }
    
    async def handle_connection(self, websocket: websockets.WebSocketServerProtocol,
                              tenant_uuid: str):
        """Handle a new WebSocket connection."""
        try:
            # Add connection to tenant channel
            if tenant_uuid not in self.connections['tenant']:
                self.connections['tenant'][tenant_uuid] = set()
            self.connections['tenant'][tenant_uuid].add(websocket)
            
            # Start Redis subscription
            redis = await aioredis.from_url(self.redis_url)
            pubsub = redis.pubsub()
            
            # Subscribe to tenant channel
            await pubsub.subscribe(f"events:tenant:{tenant_uuid}")
            
            # Handle subscription messages
            try:
                while True:
                    try:
                        message = await pubsub.get_message(ignore_subscribe_messages=True)
                        if message:
                            await websocket.send(message['data'].decode())
                        await asyncio.sleep(0.1)  # Prevent busy loop
                    except websockets.ConnectionClosed:
                        break
            finally:
                await pubsub.unsubscribe()
                await redis.close()
                
                # Remove connection from all channels
                self._remove_connection(websocket)
        
        except Exception as e:
            print(f"WebSocket error: {e}")
            self._remove_connection(websocket)
    
    async def subscribe_queue(self, websocket: websockets.WebSocketServerProtocol,
                            queue_id: int):
        """Subscribe to queue events."""
        if queue_id not in self.connections['queue']:
            self.connections['queue'][queue_id] = set()
        self.connections['queue'][queue_id].add(websocket)
        
        redis = await aioredis.from_url(self.redis_url)
        pubsub = redis.pubsub()
        
        await pubsub.subscribe(f"events:queue:{queue_id}")
        
        try:
            while True:
                try:
                    message = await pubsub.get_message(ignore_subscribe_messages=True)
                    if message:
                        await websocket.send(message['data'].decode())
                    await asyncio.sleep(0.1)
                except websockets.ConnectionClosed:
                    break
        finally:
            await pubsub.unsubscribe()
            await redis.close()
            
            if queue_id in self.connections['queue']:
                self.connections['queue'][queue_id].discard(websocket)
                if not self.connections['queue'][queue_id]:
                    del self.connections['queue'][queue_id]
    
    async def subscribe_agent(self, websocket: websockets.WebSocketServerProtocol,
                            agent_id: int):
        """Subscribe to agent events."""
        if agent_id not in self.connections['agent']:
            self.connections['agent'][agent_id] = set()
        self.connections['agent'][agent_id].add(websocket)
        
        redis = await aioredis.from_url(self.redis_url)
        pubsub = redis.pubsub()
        
        await pubsub.subscribe(f"events:agent:{agent_id}")
        
        try:
            while True:
                try:
                    message = await pubsub.get_message(ignore_subscribe_messages=True)
                    if message:
                        await websocket.send(message['data'].decode())
                    await asyncio.sleep(0.1)
                except websockets.ConnectionClosed:
                    break
        finally:
            await pubsub.unsubscribe()
            await redis.close()
            
            if agent_id in self.connections['agent']:
                self.connections['agent'][agent_id].discard(websocket)
                if not self.connections['agent'][agent_id]:
                    del self.connections['agent'][agent_id]
    
    def _remove_connection(self, websocket: websockets.WebSocketServerProtocol):
        """Remove a connection from all channels."""
        # Remove from tenant channels
        for tenant_connections in self.connections['tenant'].values():
            tenant_connections.discard(websocket)
        
        # Remove from queue channels
        for queue_connections in self.connections['queue'].values():
            queue_connections.discard(websocket)
        
        # Remove from agent channels
        for agent_connections in self.connections['agent'].values():
            agent_connections.discard(websocket)
        
        # Clean up empty sets
        for channel_type in self.connections:
            empty_keys = [
                key for key, connections in self.connections[channel_type].items()
                if not connections
            ]
            for key in empty_keys:
                del self.connections[channel_type][key]
    
    async def broadcast_tenant(self, tenant_uuid: str, message: Dict):
        """Broadcast message to all connections in a tenant."""
        if tenant_uuid in self.connections['tenant']:
            message_str = json.dumps({
                'timestamp': datetime.utcnow().isoformat(),
                'data': message
            })
            
            closed_connections = set()
            for websocket in self.connections['tenant'][tenant_uuid]:
                try:
                    await websocket.send(message_str)
                except websockets.ConnectionClosed:
                    closed_connections.add(websocket)
            
            # Remove closed connections
            for websocket in closed_connections:
                self._remove_connection(websocket)
    
    async def broadcast_queue(self, queue_id: int, message: Dict):
        """Broadcast message to all connections watching a queue."""
        if queue_id in self.connections['queue']:
            message_str = json.dumps({
                'timestamp': datetime.utcnow().isoformat(),
                'data': message
            })
            
            closed_connections = set()
            for websocket in self.connections['queue'][queue_id]:
                try:
                    await websocket.send(message_str)
                except websockets.ConnectionClosed:
                    closed_connections.add(websocket)
            
            # Remove closed connections
            for websocket in closed_connections:
                self._remove_connection(websocket)
    
    async def broadcast_agent(self, agent_id: int, message: Dict):
        """Broadcast message to all connections watching an agent."""
        if agent_id in self.connections['agent']:
            message_str = json.dumps({
                'timestamp': datetime.utcnow().isoformat(),
                'data': message
            })
            
            closed_connections = set()
            for websocket in self.connections['agent'][agent_id]:
                try:
                    await websocket.send(message_str)
                except websockets.ConnectionClosed:
                    closed_connections.add(websocket)
            
            # Remove closed connections
            for websocket in closed_connections:
                self._remove_connection(websocket)
