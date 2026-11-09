package com.civilization.entities;

import com.civilization.agents.AgentIdentity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.math.BlockPos;

public interface AgentEntity {
    AgentIdentity identity();
    BlockPos position();
    void teleport(ServerWorld world, BlockPos pos);
    int health();
}