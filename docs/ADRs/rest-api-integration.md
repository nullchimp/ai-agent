---
title: REST API Integration ADR
description: Architectural decision for integrating a REST API endpoint.
status: proposed
date: 2025-05-25
---

# ADR: REST API Integration

**Status:** Proposed

**Date:** 2025-05-25

## Context

The current AI agent is initiated and interacted with via a command-line interface (as seen in `src/main.py`). To allow broader access and integration with other services or user interfaces, a REST API endpoint is required. This API will serve as an entry point for submitting queries to the agent. The agent's core processing loop, including RAG, LLM interaction, MCP tool usage, and other functionalities, needs to run in the background and be triggered by incoming API requests. The API should then return the agent's final response.

The existing architecture (documented in `docs/architecture.md`) details a modular system with components for LLM handling, RAG, MCP, and various tools. The new API component must integrate smoothly with these existing parts, particularly with the `Agent` class in `src/agent.py` which orchestrates the main logic.

## Decision

We will introduce a lightweight REST API framework, such as FastAPI or Flask, to expose an endpoint (e.g., `/ask`). This API will run as a separate process or thread alongside the main agent logic.

1.  **API Framework Selection:** FastAPI is chosen due to its modern features, asynchronous support (which is beneficial for I/O-bound operations like LLM calls and tool interactions), automatic data validation (Pydantic), and interactive API documentation (Swagger UI/OpenAPI).
2.  **Agent Interaction:**
    *   The `Agent` instance will be initialized and run in a background thread or managed by an asynchronous task runner (e.g., `asyncio`).
    *   The API endpoint handler will receive a user query, place it into a request queue, or directly invoke a method on the `Agent` instance.
    *   The `Agent` will process the query using its existing workflow (RAG, LLM, Tools, MCP).
    *   Once the agent has a response, it will be returned to the API handler, which then sends it back to the client.
3.  **Concurrency Model:**
    *   The API server (e.g., Uvicorn for FastAPI) will handle incoming HTTP requests concurrently.
    *   The agent itself might process requests sequentially if it maintains significant internal state per query that is not easily parallelizable. If parallel processing by the agent is desired, careful state management and resource pooling (e.g., for LLM API clients) will be necessary. Initially, a single-threaded agent processing loop responding to queued requests is simpler to implement.
4.  **Configuration:** API server configurations (host, port) will be managed via environment variables or a dedicated configuration file.
5.  **Entry Point Modification:** `src/main.py` will be updated to initialize and start both the API server and the background agent.

## Consequences

### Positive

*   **Accessibility:** Provides a standard HTTP interface, making the agent accessible to a wider range of clients (web UIs, other backend services, mobile apps).
*   **Decoupling:** Separates the agent's core logic from the user interaction mechanism.
*   **Scalability:** FastAPI with Uvicorn can handle multiple concurrent requests efficiently. The agent's processing can be scaled independently if designed stateless or with proper session management.
*   **Standardization:** Leverages OpenAPI standards for API documentation and client generation.
*   **Asynchronous Operations:** Aligns well with the potentially long-running nature of agent tasks (LLM calls, tool execution).

### Negative

*   **Increased Complexity:** Adds another component (API server) to the system.
*   **Process Management:** Requires managing the lifecycle of both the API server and the agent's background process/thread.
*   **State Management:** If the agent needs to handle multiple users or sessions concurrently through the API, robust state management or a stateless agent design will be crucial. (Implementation details to be determined during planning/implementation phases)
*   **Security:** Exposing an API endpoint requires careful consideration of authentication, authorization, input validation, and rate limiting. (Implementation details to be determined during planning/implementation phases)
*   **Resource Consumption:** Running an additional server process will consume more system resources.

## Alternatives Considered

1.  **Flask API:**
    *   **Pros:** Simpler for small APIs, widely adopted.
    *   **Cons:** Asynchronous support is less integrated than FastAPI (requires Werkzeug's WSGI to ASGI bridge or separate async libraries). Less out-of-the-box data validation and API docs.
    *   **Rejected because:** FastAPI's native async capabilities and Pydantic integration are better suited for the I/O-bound nature of the agent and for robust data handling.

2.  **gRPC:**
    *   **Pros:** High performance, uses Protocol Buffers for schema definition, good for inter-service communication.
    *   **Cons:** Less browser-friendly than REST/HTTP. More complex setup for simple request/response patterns.
    *   **Rejected because:** A REST API is more universally accessible for typical client integrations (UIs, general services) than gRPC.

3.  **Directly Exposing Agent via a Network Socket (Custom Protocol):**
    *   **Pros:** Potentially more lightweight than a full HTTP server.
    *   **Cons:** Requires designing and implementing a custom communication protocol, lacks standardization, no built-in security features or documentation tools.
    *   **Rejected because:** The benefits do not outweigh the significant development overhead and lack of interoperability.

## Future Considerations

*   **Authentication/Authorization:** Implement mechanisms (e.g., API keys, OAuth2) to secure the API endpoint.
*   **Scalability of Agent Processing:** Investigate options for running multiple agent workers to handle higher loads if necessary. This might involve message queues (e.g., RabbitMQ, Redis Streams) to distribute tasks.
*   **Webhook/Callback Support:** For very long-running agent tasks, consider adding support for webhooks or callbacks instead of keeping HTTP connections open.
*   **API Versioning:** Introduce API versioning as the API evolves.
*   **Detailed API Specification:** Create a comprehensive OpenAPI specification for all endpoints.
*   **Monitoring and Logging:** Integrate robust logging and monitoring for API traffic, performance, and errors.
