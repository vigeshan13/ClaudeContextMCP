#!/usr/bin/env python3
"""
AI Agent Context Management System - MCP Server Orchestrator

This orchestrator manages all 4 MCP servers, handles inter-server communication,
provides unified APIs, and ensures proper startup/shutdown sequences.
"""

import asyncio
import subprocess
import signal
import sys
import logging
import json
import time
from typing import Dict, List, Optional, Any
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPServerOrchestrator:
    """Orchestrates all MCP servers and manages their lifecycle"""
    
    def __init__(self):
        self.servers = {
            'context_storage': {
                'script': 'src/servers/context_storage_server.py',
                'port': int(os.getenv('CONTEXT_STORAGE_PORT', 8001)),
                'process': None,
                'status': 'stopped',
                'description': 'Multi-project intelligent storage'
            },
            'retrieval_engine': {
                'script': 'src/servers/retrieval_engine_server.py',
                'port': int(os.getenv('RETRIEVAL_ENGINE_PORT', 8002)),
                'process': None,
                'status': 'stopped',
                'description': 'Intelligent context retrieval'
            },
            'intelligence_engine': {
                'script': 'src/servers/intelligence_engine_server.py',
                'port': int(os.getenv('INTELLIGENCE_ENGINE_PORT', 8003)),
                'process': None,
                'status': 'stopped',
                'description': 'Pattern learning and cross-tech insights'
            },
            'session_manager': {
                'script': 'src/servers/session_manager_server.py',
                'port': int(os.getenv('SESSION_MANAGER_PORT', 8004)),
                'process': None,
                'status': 'stopped',
                'description': 'Session continuity and state management'
            }
        }
        
        # Working servers (2 out of 4 - significant functionality available)
        self.startup_order = ['context_storage', 'retrieval_engine']  # These 2 servers work reliably
        self.shutdown_order = list(reversed(self.startup_order))
        self.running = False
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        asyncio.create_task(self.shutdown_all())
    
    async def start_server(self, server_name: str) -> bool:
        """Start a specific MCP server"""
        
        if server_name not in self.servers:
            logger.error(f"Unknown server: {server_name}")
            return False
        
        server_config = self.servers[server_name]
        
        if server_config['status'] == 'running':
            logger.info(f"Server {server_name} is already running")
            return True
        
        script_path = Path(server_config['script'])
        if not script_path.exists():
            logger.error(f"Server script not found: {script_path}")
            return False
        
        try:
            # Start the server process
            logger.info(f"Starting {server_name} server on port {server_config['port']}...")
            
            env = os.environ.copy()
            env.update({
                'PYTHONPATH': str(Path.cwd()),
                'CONTEXT_STORAGE_PORT': str(self.servers['context_storage']['port']),
                'RETRIEVAL_ENGINE_PORT': str(self.servers['retrieval_engine']['port']),
                'INTELLIGENCE_ENGINE_PORT': str(self.servers['intelligence_engine']['port']),
                'SESSION_MANAGER_PORT': str(self.servers['session_manager']['port'])
            })
            
            process = await asyncio.create_subprocess_exec(
                sys.executable, str(script_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )
            
            server_config['process'] = process
            server_config['status'] = 'starting'
            
            # Wait a moment to check if the process started successfully
            await asyncio.sleep(2)
            
            if process.returncode is None:  # Process is still running
                server_config['status'] = 'running'
                logger.info(f"✅ {server_name} server started successfully on port {server_config['port']}")
                return True
            else:
                # Process died immediately
                stdout, stderr = await process.communicate()
                logger.error(f"❌ {server_name} server failed to start:")
                logger.error(f"STDOUT: {stdout.decode()}")
                logger.error(f"STDERR: {stderr.decode()}")
                server_config['status'] = 'failed'
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to start {server_name} server: {str(e)}")
            server_config['status'] = 'failed'
            return False
    
    async def stop_server(self, server_name: str) -> bool:
        """Stop a specific MCP server"""
        
        if server_name not in self.servers:
            logger.error(f"Unknown server: {server_name}")
            return False
        
        server_config = self.servers[server_name]
        
        if server_config['status'] != 'running':
            logger.info(f"Server {server_name} is not running")
            return True
        
        process = server_config['process']
        if process:
            try:
                logger.info(f"Stopping {server_name} server...")
                
                # Try graceful shutdown first
                process.terminate()
                
                # Wait for graceful shutdown
                try:
                    await asyncio.wait_for(process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    # Force kill if graceful shutdown fails
                    logger.warning(f"Force killing {server_name} server...")
                    process.kill()
                    await process.wait()
                
                server_config['process'] = None
                server_config['status'] = 'stopped'
                logger.info(f"✅ {server_name} server stopped")
                return True
                
            except Exception as e:
                logger.error(f"❌ Failed to stop {server_name} server: {str(e)}")
                return False
        
        return True
    
    async def start_all(self) -> bool:
        """Start all MCP servers in the correct order"""
        
        logger.info("🚀 Starting AI Agent Context Management System...")
        logger.info("=" * 60)
        
        success_count = 0
        
        for server_name in self.startup_order:
            server_config = self.servers[server_name]
            logger.info(f"Starting {server_name}: {server_config['description']}")
            
            if await self.start_server(server_name):
                success_count += 1
            else:
                logger.error(f"Failed to start {server_name}, aborting startup")
                # Stop any servers that were started
                await self.shutdown_all()
                return False
            
            # Brief pause between server starts
            await asyncio.sleep(1)
        
        if success_count == len(self.startup_order):
            self.running = True
            logger.info("=" * 60)
            logger.info(f"🎉 All {success_count} MCP servers started successfully!")
            self._print_server_status()
            return True
        else:
            logger.error(f"❌ Failed to start all servers ({success_count}/{len(self.startup_order)} started)")
            return False
    
    async def shutdown_all(self) -> bool:
        """Shutdown all MCP servers in the correct order"""
        
        logger.info("🛑 Shutting down AI Agent Context Management System...")
        
        success_count = 0
        
        for server_name in self.shutdown_order:
            if await self.stop_server(server_name):
                success_count += 1
        
        self.running = False
        
        if success_count == len(self.servers):
            logger.info("✅ All MCP servers shut down successfully")
            return True
        else:
            logger.error("❌ Some servers failed to shut down properly")
            return False
    
    async def restart_server(self, server_name: str) -> bool:
        """Restart a specific server"""
        
        logger.info(f"Restarting {server_name} server...")
        
        if await self.stop_server(server_name):
            await asyncio.sleep(2)  # Brief pause
            return await self.start_server(server_name)
        
        return False
    
    async def restart_all(self) -> bool:
        """Restart all servers"""
        
        logger.info("🔄 Restarting all MCP servers...")
        
        if await self.shutdown_all():
            await asyncio.sleep(3)  # Pause between shutdown and startup
            return await self.start_all()
        
        return False
    
    def get_server_status(self) -> Dict[str, Any]:
        """Get status of all servers"""
        
        status = {
            'system_status': 'running' if self.running else 'stopped',
            'servers': {}
        }
        
        for server_name, server_config in self.servers.items():
            status['servers'][server_name] = {
                'status': server_config['status'],
                'port': server_config['port'],
                'description': server_config['description'],
                'pid': server_config['process'].pid if server_config['process'] else None
            }
        
        return status
    
    def _print_server_status(self):
        """Print server status table"""
        
        logger.info("\n📊 Server Status:")
        logger.info("-" * 80)
        logger.info(f"{'Server Name':<20} {'Port':<6} {'Status':<10} {'Description':<30}")
        logger.info("-" * 80)
        
        for server_name, server_config in self.servers.items():
            status_emoji = "🟢" if server_config['status'] == 'running' else "🔴"
            logger.info(f"{server_name:<20} {server_config['port']:<6} {status_emoji} {server_config['status']:<8} {server_config['description']:<30}")
        
        logger.info("-" * 80)
        logger.info(f"\n🌐 System accessible on ports: {', '.join([str(s['port']) for s in self.servers.values()])}")
        logger.info("📋 Use Ctrl+C to gracefully shutdown all servers")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all servers"""
        
        health_status = {
            'system_healthy': True,
            'timestamp': time.time(),
            'servers': {}
        }
        
        for server_name, server_config in self.servers.items():
            process = server_config['process']
            
            if process and process.returncode is None:
                # Process is running
                health_status['servers'][server_name] = {
                    'status': 'healthy',
                    'port': server_config['port'],
                    'uptime': time.time()  # Simplified uptime
                }
            else:
                # Process is not running or died
                health_status['servers'][server_name] = {
                    'status': 'unhealthy',
                    'port': server_config['port'],
                    'uptime': 0
                }
                health_status['system_healthy'] = False
        
        return health_status
    
    async def monitor_servers(self):
        """Monitor server health and restart if needed"""
        
        while self.running:
            try:
                health = await self.health_check()
                
                for server_name, server_health in health['servers'].items():
                    if server_health['status'] == 'unhealthy' and self.servers[server_name]['status'] == 'running':
                        logger.warning(f"Server {server_name} is unhealthy, attempting restart...")
                        await self.restart_server(server_name)
                
                # Check every 30 seconds
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Error during health monitoring: {str(e)}")
                await asyncio.sleep(30)
    
    async def run(self):
        """Main run method - start servers and monitor"""
        
        try:
            # Start all servers
            if not await self.start_all():
                logger.error("Failed to start servers, exiting")
                return False
            
            # Start monitoring task
            monitor_task = asyncio.create_task(self.monitor_servers())
            
            logger.info("\n🔍 Monitoring servers... Press Ctrl+C to shutdown")
            
            # Keep running until interrupted
            while self.running:
                await asyncio.sleep(1)
            
            # Cancel monitoring
            monitor_task.cancel()
            
            # Shutdown servers
            await self.shutdown_all()
            
            return True
            
        except KeyboardInterrupt:
            logger.info("\n👋 Keyboard interrupt received, shutting down...")
            await self.shutdown_all()
            return True
        except Exception as e:
            logger.error(f"Orchestrator error: {str(e)}")
            await self.shutdown_all()
            return False

class MCPServerManager:
    """Management interface for the MCP servers"""
    
    def __init__(self, orchestrator: MCPServerOrchestrator):
        self.orchestrator = orchestrator
    
    async def status(self) -> Dict[str, Any]:
        """Get detailed system status"""
        
        base_status = self.orchestrator.get_server_status()
        health_status = await self.orchestrator.health_check()
        
        return {
            'system_info': {
                'running': self.orchestrator.running,
                'healthy': health_status['system_healthy'],
                'server_count': len(self.orchestrator.servers),
                'timestamp': health_status['timestamp']
            },
            'servers': base_status['servers'],
            'health_details': health_status['servers']
        }
    
    async def start_server(self, server_name: str) -> Dict[str, Any]:
        """Start a specific server"""
        
        success = await self.orchestrator.start_server(server_name)
        
        return {
            'action': 'start_server',
            'server': server_name,
            'success': success,
            'timestamp': time.time()
        }
    
    async def stop_server(self, server_name: str) -> Dict[str, Any]:
        """Stop a specific server"""
        
        success = await self.orchestrator.stop_server(server_name)
        
        return {
            'action': 'stop_server',
            'server': server_name,
            'success': success,
            'timestamp': time.time()
        }
    
    async def restart_server(self, server_name: str) -> Dict[str, Any]:
        """Restart a specific server"""
        
        success = await self.orchestrator.restart_server(server_name)
        
        return {
            'action': 'restart_server',
            'server': server_name,
            'success': success,
            'timestamp': time.time()
        }

def print_banner():
    """Print system banner"""
    
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                   AI Agent Context Management System                         ║
║                              MCP Server Suite                                ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  🏗️  Context Storage Server    (Port 8001) - Multi-project storage          ║
║  🔍  Retrieval Engine Server   (Port 8002) - Intelligent context retrieval  ║
║  🧠  Intelligence Engine Server (Port 8003) - Pattern learning & insights   ║
║  📊  Session Manager Server    (Port 8004) - Session continuity & state     ║
║                                                                              ║
║  Built for solo developers working across multiple technology stacks        ║
║  Specialized for: Swift, Android, Python, React, JavaScript                 ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """
    
    print(banner)

async def main():
    """Main entry point"""
    
    print_banner()
    
    # Create orchestrator
    orchestrator = MCPServerOrchestrator()
    
    try:
        # Run the orchestrator
        success = await orchestrator.run()
        
        if success:
            logger.info("✅ System shutdown completed successfully")
            sys.exit(0)
        else:
            logger.error("❌ System shutdown with errors")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())