#!/usr/bin/env python3
"""
AI Agent Context Management System - System Startup Script

This script provides various ways to start the MCP server system:
- Development mode: Individual server control
- Production mode: Full orchestration
- Testing mode: With additional logging and debugging
"""

import argparse
import asyncio
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.orchestrator import MCPServerOrchestrator, MCPServerManager, print_banner

def create_parser():
    """Create command line argument parser"""
    
    parser = argparse.ArgumentParser(
        description="AI Agent Context Management System - MCP Server Startup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start all servers in production mode
  python scripts/start_system.py --mode production
  
  # Start specific server for development
  python scripts/start_system.py --mode development --server context_storage
  
  # Start with enhanced debugging
  python scripts/start_system.py --mode testing --debug
  
  # Get system status
  python scripts/start_system.py --status
        """
    )
    
    parser.add_argument(
        '--mode',
        choices=['production', 'development', 'testing'],
        default='production',
        help='Startup mode (default: production)'
    )
    
    parser.add_argument(
        '--server',
        choices=['context_storage', 'retrieval_engine', 'intelligence_engine', 'session_manager'],
        help='Start specific server (development mode only)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show system status and exit'
    )
    
    parser.add_argument(
        '--stop',
        action='store_true',
        help='Stop all running servers'
    )
    
    parser.add_argument(
        '--restart',
        action='store_true',
        help='Restart all servers'
    )
    
    parser.add_argument(
        '--config',
        default='config/claude_mcp_config.json',
        help='Configuration file path'
    )
    
    return parser

async def production_mode(orchestrator: MCPServerOrchestrator):
    """Run in production mode - start all servers with monitoring"""
    
    print("🚀 Starting in PRODUCTION mode...")
    print("   - All servers will be started")
    print("   - Health monitoring enabled") 
    print("   - Automatic restart on failure")
    print()
    
    return await orchestrator.run()

async def development_mode(orchestrator: MCPServerOrchestrator, specific_server: str = None):
    """Run in development mode - optionally start specific server"""
    
    print("🔧 Starting in DEVELOPMENT mode...")
    
    if specific_server:
        print(f"   - Starting only: {specific_server}")
        print("   - No health monitoring")
        print("   - Manual control required")
        print()
        
        success = await orchestrator.start_server(specific_server)
        if success:
            print(f"✅ {specific_server} server started successfully")
            print("Press Ctrl+C to stop...")
            
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 Stopping server...")
                await orchestrator.stop_server(specific_server)
                return True
        else:
            print(f"❌ Failed to start {specific_server} server")
            return False
    else:
        print("   - All servers will be started")
        print("   - Basic monitoring enabled")
        print("   - Manual restart required")
        print()
        
        return await orchestrator.run()

async def testing_mode(orchestrator: MCPServerOrchestrator):
    """Run in testing mode - enhanced logging and debugging"""
    
    print("🧪 Starting in TESTING mode...")
    print("   - Enhanced debugging enabled")
    print("   - Detailed health monitoring")
    print("   - Performance metrics collected")
    print()
    
    # Set debug environment variables
    os.environ['DEBUG'] = 'true'
    os.environ['LOG_LEVEL'] = 'DEBUG'
    
    return await orchestrator.run()

async def show_status(orchestrator: MCPServerOrchestrator):
    """Show system status"""
    
    manager = MCPServerManager(orchestrator)
    status = await manager.status()
    
    print("📊 System Status Report")
    print("=" * 50)
    print(f"System Running: {'Yes' if status['system_info']['running'] else 'No'}")
    print(f"System Healthy: {'Yes' if status['system_info']['healthy'] else 'No'}")
    print(f"Server Count: {status['system_info']['server_count']}")
    print()
    
    print("Server Details:")
    print("-" * 50)
    for server_name, server_info in status['servers'].items():
        health = status['health_details'].get(server_name, {})
        status_emoji = "🟢" if server_info['status'] == 'running' else "🔴"
        health_emoji = "💚" if health.get('status') == 'healthy' else "💔"
        
        print(f"{status_emoji} {health_emoji} {server_name}")
        print(f"   Port: {server_info['port']}")
        print(f"   Status: {server_info['status']}")
        print(f"   Description: {server_info['description']}")
        print(f"   PID: {server_info['pid'] or 'N/A'}")
        print()

async def stop_all_servers(orchestrator: MCPServerOrchestrator):
    """Stop all running servers"""
    
    print("🛑 Stopping all servers...")
    success = await orchestrator.shutdown_all()
    
    if success:
        print("✅ All servers stopped successfully")
    else:
        print("❌ Some servers failed to stop properly")
    
    return success

async def restart_all_servers(orchestrator: MCPServerOrchestrator):
    """Restart all servers"""
    
    print("🔄 Restarting all servers...")
    success = await orchestrator.restart_all()
    
    if success:
        print("✅ All servers restarted successfully")
        print("Press Ctrl+C to stop...")
        
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping servers...")
            await orchestrator.shutdown_all()
            return True
    else:
        print("❌ Failed to restart servers")
    
    return success

async def main():
    """Main entry point"""
    
    parser = create_parser()
    args = parser.parse_args()
    
    # Set up debugging if requested
    if args.debug:
        import logging
        logging.basicConfig(level=logging.DEBUG)
        os.environ['DEBUG'] = 'true'
    
    # Print banner unless showing status
    if not args.status:
        print_banner()
    
    # Create orchestrator
    orchestrator = MCPServerOrchestrator()
    
    try:
        # Handle different commands
        if args.status:
            await show_status(orchestrator)
            return
        
        elif args.stop:
            success = await stop_all_servers(orchestrator)
            sys.exit(0 if success else 1)
        
        elif args.restart:
            success = await restart_all_servers(orchestrator)
            sys.exit(0 if success else 1)
        
        else:
            # Start servers based on mode
            if args.mode == 'production':
                success = await production_mode(orchestrator)
            elif args.mode == 'development':
                success = await development_mode(orchestrator, args.server)
            elif args.mode == 'testing':
                success = await testing_mode(orchestrator)
            else:
                print(f"❌ Unknown mode: {args.mode}")
                sys.exit(1)
            
            sys.exit(0 if success else 1)
    
    except KeyboardInterrupt:
        print("\n👋 Received interrupt signal, shutting down...")
        await orchestrator.shutdown_all()
        sys.exit(0)
    
    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")
        await orchestrator.shutdown_all()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())