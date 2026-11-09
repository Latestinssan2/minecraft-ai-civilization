package com.civilization.agents;

import java.util.List;

public record AgentIdentity(String agentId, String name, String personality, List<String> interests) {}