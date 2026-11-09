package com.civilization.agents;

import com.civilization.CivilizationMod;
import com.mojang.authlib.GameProfile;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.text.Text;
import net.minecraft.util.math.BlockPos;
import java.util.UUID;

public class PlayerAgentSpawner {
    public static void spawn(MinecraftServer server, AgentRuntime rt) {
        try {
            ServerWorld world = server.getOverworld();
            BlockPos pos = rt.position;
            GameProfile profile = new GameProfile(UUID.nameUUIDFromBytes(("OfflinePlayer:" + rt.identity.name()).getBytes()), rt.identity.name());
            ServerPlayerEntity player = new ServerPlayerEntity(server, world, profile, net.minecraft.network.packet.c2s.common.SyncedClientOptions.createDefault());
            player.refreshPositionAndAngles(pos.getX() + 0.5, pos.getY(), pos.getZ() + 0.5, 0.0F, 0.0F);
            player.setCustomName(Text.literal(rt.identity.name()));
            player.setCustomNameVisible(true);
            // Fake network handler so the server can treat them as a connected player
            // (tab list, tp-able) without a real client.
            player.networkHandler = new FakeNetworkHandler(server, player);
            rt.playerEntity = player;
            // Add to player manager (tab list)
            server.getPlayerManager().getPlayerList().add(player);
            // Spawn into world
            world.spawnEntity(player);
            // Broadcast tab list entry to real players
            net.minecraft.network.packet.s2c.play.PlayerListS2CPacket packet =
                    new net.minecraft.network.packet.s2c.play.PlayerListS2CPacket(
                            net.minecraft.network.packet.s2c.play.PlayerListS2CPacket.Action.ADD_PLAYER, player);
            for (var p : server.getPlayerManager().getPlayerList()) {
                if (p != player && p.networkHandler != null) {
                    p.networkHandler.sendPacket(packet);
                }
            }
            CivilizationMod.LOGGER.info("Spawned player entity (tab-list) for agent {} at {}", rt.identity.agentId(), pos);
        } catch (Exception e) {
            CivilizationMod.LOGGER.error("Failed to spawn player entity for agent {}", rt.identity.agentId(), e);
        }
    }
}