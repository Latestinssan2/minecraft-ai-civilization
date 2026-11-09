package com.civilization.agents;

import com.civilization.agents.AgentIdentity;
import net.minecraft.util.math.BlockPos;
import java.util.List;

public class AgentRuntime {
    public final AgentIdentity identity;
    public BlockPos position;
    public int health = 20;
    public net.minecraft.server.network.ServerPlayerEntity playerEntity;
    public AgentRuntime(String id, String name, String personality) {
        List<String> interests = switch (name) {
            case "CHAIWALA" -> List.of("leadership", "exploration", "civilization planning");
            case "Arin" -> List.of("construction", "engineering", "mining");
            case "Mira" -> List.of("exploration", "farming", "trading");
            default -> List.of();
        };
        this.identity = new AgentIdentity(id, name, personality, interests);
    }
}