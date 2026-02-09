from __future__ import annotations

from loguru import logger
from strands.hooks import HookProvider, HookRegistry
from strands.hooks.events import (
    AfterInvocationEvent,
    AfterModelCallEvent,
    AfterMultiAgentInvocationEvent,
    AfterNodeCallEvent,
    AfterToolCallEvent,
    AgentInitializedEvent,
    BeforeInvocationEvent,
    BeforeModelCallEvent,
    BeforeMultiAgentInvocationEvent,
    BeforeNodeCallEvent,
    BeforeToolCallEvent,
    MessageAddedEvent,
    MultiAgentInitializedEvent,
)


class LoggingHook(HookProvider):
    def register_hooks(self, registry: HookRegistry, **_: object) -> None:
        registry.add_callback(AgentInitializedEvent, self.on_agent_initialized)
        registry.add_callback(BeforeInvocationEvent, self.on_before_invocation)
        registry.add_callback(AfterInvocationEvent, self.on_after_invocation)
        registry.add_callback(MessageAddedEvent, self.on_message_added)
        registry.add_callback(BeforeModelCallEvent, self.on_before_model_call)
        registry.add_callback(AfterModelCallEvent, self.on_after_model_call)
        registry.add_callback(BeforeToolCallEvent, self.on_before_tool_call)
        registry.add_callback(AfterToolCallEvent, self.on_after_tool_call)

        registry.add_callback(MultiAgentInitializedEvent, self.on_multi_agent_initialized)
        registry.add_callback(BeforeMultiAgentInvocationEvent, self.on_before_multi_agent_invocation)
        registry.add_callback(AfterMultiAgentInvocationEvent, self.on_after_multi_agent_invocation)
        registry.add_callback(BeforeNodeCallEvent, self.on_before_node_call)
        registry.add_callback(AfterNodeCallEvent, self.on_after_node_call)

    def on_agent_initialized(self, event: AgentInitializedEvent) -> None:
        logger.debug(f"[Agent Initialized] Agent name: {event.agent.name}")

    def on_before_invocation(self, event: BeforeInvocationEvent) -> None:
        logger.debug(
            f"[Before Invocation] Starting new request | "
            f"Agent Id: {event.agent.agent_id} | "
            f"Agent Name: {event.agent.name} | "
            f"Agent Desc: {event.agent.description} | "
            f"Tools: {event.agent.tool_names} | "
            f"Input messages count: {len(event.messages or '')}"
        )

    def on_after_invocation(self, event: AfterInvocationEvent) -> None:
        success = "success" if event.result else "failure"
        logger.debug(
            f"[After Invocation] Request completed ({success}) | "
            f"Agent Id: {event.agent.agent_id} | "
            f"Agent Name: {event.agent.name} | "
            f"Agent Desc: {event.agent.description} | "
            f"Tools: {event.agent.tool_names} | "
            f"Output content: {event.result.message if event.result else 'None'} | "
        )

    def on_message_added(self, event: MessageAddedEvent) -> None:
        role = event.message.get("role", "unknown")
        content_summary = event.message.get("content")[0].get("text") or "None"
        logger.debug(f"[Message Added] Role: {role} | Content summary: {content_summary}")

    def on_before_model_call(self, event: BeforeModelCallEvent) -> None:
        logger.debug(
            f"[Before Model Call] Invoking model | "
            f"Agent Id: {event.agent.agent_id} | "
            f"Agent Name: {event.agent.name} | "
            f"Agent Desc: {event.agent.description} | "
            f"Tools: {event.agent.tool_names} | "
            f"Invocation State: {event.invocation_state} | "
        )

    def on_after_model_call(self, event: AfterModelCallEvent) -> None:
        logger.debug(
            f"[After Model Call] Model response received | "
            f"Invocation State: {event.invocation_state}| "
            f"Exception: {event.exception} | "
            f"Retry requested: {getattr(event, 'retry', False)}"
        )

    def on_before_tool_call(self, event: BeforeToolCallEvent) -> None:
        tool_name = event.tool_use.get("name", "unknown")
        tool_input = event.tool_use.get("input", {})
        logger.debug(
            f"[Before Tool Call] Tool: {tool_name} | "
            f"Input: {tool_input} | "
            f"Cancel tool: {getattr(event, 'cancel_tool', None)}"
        )

    def on_after_tool_call(self, event: AfterToolCallEvent) -> None:
        tool_name = event.tool_use.get("name", "unknown")
        result_summary = (
            str(event.result.get("content", "")[:200]) + "..."
            if event.result
            else "None"
        )
        logger.debug(
            f"[After Tool Call] Tool: {tool_name} | "
            f"Result summary: {result_summary} | "
            f"Exception: {event.exception}"
        )

    def on_multi_agent_initialized(self, event: MultiAgentInitializedEvent) -> None:
        logger.debug(f"[Multi-Agent Initialized] Orchestrator type: {type(event.source).__name__}")

    def on_before_multi_agent_invocation(self, event: BeforeMultiAgentInvocationEvent) -> None:
        logger.debug(
            f"[Before Multi-Agent Invocation] Starting orchestrator execution | "
            f"Orchestrator: {type(event.source).__name__}"
        )

    def on_after_multi_agent_invocation(self, event: AfterMultiAgentInvocationEvent) -> None:
        logger.debug(
            f"[After Multi-Agent Invocation] Orchestrator execution completed | "
            f"Invocation State: {event.invocation_state}"
        )

    def on_before_node_call(self, event: BeforeNodeCallEvent) -> None:
        logger.debug(
            f"[Before Node Call] Node ID: {event.node_id} | "
            f"Orchestrator: {type(event.source).__name__}"
        )

    def on_after_node_call(self, event: AfterNodeCallEvent) -> None:
        logger.debug(
            f"[After Node Call] Node ID: {event.node_id} | "
            f"Invocation State: {event.invocation_state}"
        )
