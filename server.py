#!/usr/bin/env python3
"""
test-newsapi-mcp MCP Server - FastMCP with D402 Transport Wrapper

Uses FastMCP from official MCP SDK with D402MCPTransport wrapper for HTTP 402.

Architecture:
- FastMCP for tool decorators and Context objects
- D402MCPTransport wraps the /mcp route for HTTP 402 interception
- Proper HTTP 402 status codes (not JSON-RPC wrapped)

Generated from OpenAPI: https://newsapi.org/docs

Environment Variables:
- TEST_NEWSAPI_MCP_API_KEY: Server's internal API key (for paid requests)
- SERVER_ADDRESS: Payment address (IATP wallet contract)
- MCP_OPERATOR_PRIVATE_KEY: Operator signing key
- D402_TESTING_MODE: Skip facilitator (default: true)
"""

import os
import logging
import sys
from typing import Dict, Any, Optional
from datetime import datetime

import requests
from retry import retry
from dotenv import load_dotenv
import uvicorn

load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test-newsapi-mcp_mcp')

# FastMCP from official SDK
from mcp.server.fastmcp import FastMCP, Context
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

# D402 payment protocol - using Starlette middleware
from traia_iatp.d402.starlette_middleware import D402PaymentMiddleware
from traia_iatp.d402.mcp_middleware import require_payment_for_tool, get_active_api_key
from traia_iatp.d402.payment_introspection import extract_payment_configs_from_mcp
from traia_iatp.d402.types import TokenAmount, TokenAsset, EIP712Domain

# Configuration
STAGE = os.getenv("STAGE", "MAINNET").upper()
PORT = int(os.getenv("PORT", "8000"))
SERVER_ADDRESS = os.getenv("SERVER_ADDRESS")
if not SERVER_ADDRESS:
    raise ValueError("SERVER_ADDRESS required for payment protocol")

API_KEY = os.getenv("TEST_NEWSAPI_MCP_API_KEY")
if not API_KEY:
    logger.warning(f"⚠️  TEST_NEWSAPI_MCP_API_KEY not set - payment required for all requests")

logger.info("="*80)
logger.info(f"test-newsapi-mcp MCP Server (FastMCP + D402 Wrapper)")
logger.info(f"API: https://newsapi.org/v2")
logger.info(f"Payment: {SERVER_ADDRESS}")
logger.info(f"API Key: {'✅' if API_KEY else '❌ Payment required'}")
logger.info("="*80)

# Create FastMCP server
mcp = FastMCP("test-newsapi-mcp MCP Server", host="0.0.0.0")

logger.info(f"✅ FastMCP server created")

# ============================================================================
# TOOL IMPLEMENTATIONS
# ============================================================================
# Tool implementations will be added here by endpoint_implementer_crew
# Each tool will use the @mcp.tool() and @require_payment_for_tool() decorators


# D402 Payment Middleware
# The HTTP 402 payment protocol middleware is already configured in the server initialization.
# It's imported from traia_iatp.d402.mcp_middleware and auto-detects configuration from:
# - PAYMENT_ADDRESS or EVM_ADDRESS: Where to receive payments
# - EVM_NETWORK: Blockchain network (default: base-sepolia)
# - DEFAULT_PRICE_USD: Price per request (default: $0.001)
# - TEST_NEWSAPI_MCP_API_KEY: Server's internal API key for payment mode
#
# All payment verification logic is handled by the traia_iatp.d402 module.
# No custom implementation needed!


# API Endpoint Tool Implementations

@mcp.tool()
@require_payment_for_tool(
    price=TokenAmount(
        amount="2000",  # 0.002 tokens
        asset=TokenAsset(
            address="0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238",
            decimals=6,
            network="sepolia",
            eip712=EIP712Domain(
                name="IATPWallet",
                version="1"
            )
        )
    ),
    description="Search through millions of articles. NewsAPI requi"

)
async def search_everything(
    context: Context,
    q: str = None,
    qInTitle: str = None,
    sources: str = None,
    domains: str = None,
    excludeDomains: str = None,
    from_: str = None,
    to: str = None,
    language: str = "en",
    sortBy: str = "publishedAt",
    searchIn: str = None,
    pageSize: int = 20,
    page: int = 1
) -> Dict[str, Any]:
    """
    Search through millions of articles. NewsAPI requirement: you must provide at least one of: q, sources, or domains.

    Generated from OpenAPI endpoint: GET /everything

    Args:
        context: MCP context (auto-injected by framework, not user-provided)
        q: Keywords or phrases to search for in the article title and body. Advanced search operators are supported. (optional) Examples: "artificial intelligence", "crypto AND (ethereum OR solana) NOT bitcoin"
        qInTitle: Keywords or phrases to search for in the article title only. (optional) Examples: "AI regulation", ""OpenAI""
        sources: Comma-separated source IDs (maximum 20). Use /sources to discover IDs. (optional) Examples: "bbc-news", "cnn,reuters,techcrunch"
        domains: Comma-separated domain names to restrict the search to. (optional) Examples: "bbc.co.uk", "techcrunch.com,wired.com"
        excludeDomains: Comma-separated domain names to exclude from the results. (optional) Examples: "medium.com", "substack.com"
        from_: Start date/time in ISO 8601. (NewsAPI accepts ISO 8601; date-only also commonly works.) (API param: 'from') (optional) Examples: "2025-12-01T00:00:00Z", "2025-12-01"
        to: End date/time in ISO 8601. (NewsAPI accepts ISO 8601; date-only also commonly works.) (optional) Examples: "2025-12-18T23:59:59Z", "2025-12-18"
        language: 2-letter language code to narrow articles. (optional, default: "en") Examples: "en", "es", "fr"
        sortBy: Sort order for results. (optional, default: "publishedAt") Examples: "publishedAt", "relevancy"
        searchIn: Comma-separated fields to restrict the search to. (optional) Examples: "title,content"
        pageSize: Number of results per page (1–100). (optional, default: 20)
        page: Page number (>= 1). (optional, default: 1)

    Returns:
        Dictionary with API response

    Example Usage:
        # Minimal (required params only):
        await search_everything(q="artificial intelligence")

        # With optional parameters:
        await search_everything(
        q="artificial intelligence",
        qInTitle="AI regulation",
        sources="bbc-news",
        domains="bbc.co.uk"
    )

        Note: 'context' parameter is auto-injected by MCP framework
    """
    # Payment already verified by @require_payment_for_tool decorator
    # Get API key using helper (handles request.state fallback)
    api_key = get_active_api_key(context)

    try:
        url = f"https://newsapi.org/v2/everything"
        params = {
            "q": q,
            "qInTitle": qInTitle,
            "sources": sources,
            "domains": domains,
            "excludeDomains": excludeDomains,
            "from": from_,
            "to": to,
            "language": language,
            "sortBy": sortBy,
            "searchIn": searchIn,
            "pageSize": pageSize,
            "page": page
        }
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=30
        )
        response.raise_for_status()

        return response.json()

    except Exception as e:
        logger.error(f"Error in search_everything: {e}")
        return {"error": str(e), "endpoint": "/everything"}


# TODO: Add your API-specific functions here

# ============================================================================
# APPLICATION SETUP WITH STARLETTE MIDDLEWARE
# ============================================================================

def create_app_with_middleware():
    """
    Create Starlette app with d402 payment middleware.
    
    Strategy:
    1. Get FastMCP's Starlette app via streamable_http_app()
    2. Extract payment configs from @require_payment_for_tool decorators
    3. Add Starlette middleware with extracted configs
    4. Single source of truth - no duplication!
    """
    logger.info("🔧 Creating FastMCP app with middleware...")
    
    # Get FastMCP's Starlette app
    app = mcp.streamable_http_app()
    logger.info(f"✅ Got FastMCP Starlette app")
    
    # Extract payment configs from decorators (single source of truth!)
    tool_payment_configs = extract_payment_configs_from_mcp(mcp, SERVER_ADDRESS)
    logger.info(f"📊 Extracted {len(tool_payment_configs)} payment configs from @require_payment_for_tool decorators")
    
    # D402 Configuration
    facilitator_url = os.getenv("FACILITATOR_URL") or os.getenv("D402_FACILITATOR_URL")
    operator_key = os.getenv("MCP_OPERATOR_PRIVATE_KEY")
    network = os.getenv("NETWORK", "sepolia")
    testing_mode = os.getenv("D402_TESTING_MODE", "false").lower() == "true"
    
    # Log D402 configuration with prominent facilitator info
    logger.info("="*60)
    logger.info("D402 Payment Protocol Configuration:")
    logger.info(f"  Server Address: {SERVER_ADDRESS}")
    logger.info(f"  Network: {network}")
    logger.info(f"  Operator Key: {'✅ Set' if operator_key else '❌ Not set'}")
    logger.info(f"  Testing Mode: {'⚠️  ENABLED (bypasses facilitator)' if testing_mode else '✅ DISABLED (uses facilitator)'}")
    logger.info("="*60)
    
    if not facilitator_url and not testing_mode:
        logger.error("❌ FACILITATOR_URL required when testing_mode is disabled!")
        raise ValueError("Set FACILITATOR_URL or enable D402_TESTING_MODE=true")
    
    if facilitator_url:
        logger.info(f"🌐 FACILITATOR: {facilitator_url}")
        if "localhost" in facilitator_url or "127.0.0.1" in facilitator_url or "host.docker.internal" in facilitator_url:
            logger.info(f"   📍 Using LOCAL facilitator for development")
        else:
            logger.info(f"   🌍 Using REMOTE facilitator for production")
    else:
        logger.warning("⚠️  D402 Testing Mode - Facilitator bypassed")
    logger.info("="*60)
    
    # Add CORS middleware first (processes before other middleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins
        allow_credentials=True,
        allow_methods=["*"],  # Allow all methods
        allow_headers=["*"],  # Allow all headers
    )
    logger.info("✅ Added CORS middleware (allow all origins)")
    
    # Add D402 payment middleware with extracted configs
    app.add_middleware(
        D402PaymentMiddleware,
        tool_payment_configs=tool_payment_configs,
        server_address=SERVER_ADDRESS,
        requires_auth=True,  # Extracts API keys + checks payment
        internal_api_key=API_KEY,  # Server's internal key (for Mode 2: paid access)
        testing_mode=testing_mode,
        facilitator_url=facilitator_url,
        facilitator_api_key=os.getenv("D402_FACILITATOR_API_KEY"),
        server_name="test-newsapi-mcp-mcp-server"  # MCP server ID for tracking
    )
    logger.info("✅ Added D402PaymentMiddleware")
    logger.info("   - Auth extraction: Enabled")
    logger.info("   - Dual mode: API key OR payment")
    
    # Add health check endpoint (bypasses middleware)
    @app.route("/health", methods=["GET"])
    async def health_check(request: Request) -> JSONResponse:
        """Health check endpoint for container orchestration."""
        return JSONResponse(
            content={
                "status": "healthy",
                "service": "test-newsapi-mcp-mcp-server",
                "timestamp": datetime.now().isoformat()
            }
        )
    logger.info("✅ Added /health endpoint")
    
    return app

if __name__ == "__main__":
    logger.info("="*80)
    logger.info(f"Starting test-newsapi-mcp MCP Server")
    logger.info("="*80)
    logger.info("Architecture:")
    logger.info("  1. D402PaymentMiddleware intercepts requests")
    logger.info("     - Extracts API keys from Authorization header")
    logger.info("     - Checks payment → HTTP 402 if no API key AND no payment")
    logger.info("  2. FastMCP processes valid requests with tool decorators")
    logger.info("="*80)
    
    # Create app with middleware
    app = create_app_with_middleware()
    
    # Run with uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT,
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )
