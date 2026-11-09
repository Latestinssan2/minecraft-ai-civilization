package com.civilization.agents;

import com.civilization.CivilizationMod;
import com.civilization.config.ModConfig;
import com.civilization.actions.ActionExecutor;
import com.civilization.entities.AgentEntity;
import com.civilization.observation.ObservationScanner;
import com.civilization.network.BackendClient;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.math.BlockPos;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

public class AgentManager {
    private static final Map<MinecraftServer, AgentManager> INSTANCES = new ConcurrentHashMap<>();

    public static AgentManager get(MinecraftServer server) {
        return INSTANCES.computeIfAbsent(server, AgentManager::new);
    }

    private final MinecraftServer server;
    private final List<AgentRuntime> agents = new ArrayList<>();
    private final java.util.Map<AgentRuntime, BlockPos> lastSynced = new java.util.HashMap<>();
    private volatile boolean running = false;
    private Thread pollThread;

    private AgentManager(MinecraftServer server) {
        this.server = server;
    }

    public void initialize(ModConfig cfg) {
        String[] names = {"CHAIWALA", "Arin", "Mira"};
        String[] personalities = {
            "Curious, ambitious, independent, strategic",
            "Intelligent, practical, patient, creative, organized",
            "Adventurous, curious, social, independent, adaptable"
        };
        ServerWorld world = server.getOverworld();
        for (int i = 0; i < cfg.agentCount && i < names.length; i++) {
            String id = "agent_0" + (i + 1);
            AgentRuntime rt = new AgentRuntime(id, names[i], personalities[i]);
            // spawn position spread
            BlockPos spawn = world.getSpawnPos().add(i * 4, 0, 0);
            rt.position = spawn;
            agents.add(rt);
            CivilizationMod.LOGGER.info("Spawned agent {} at {}", id, spawn);
            PlayerAgentSpawner.spawn(server, rt);
        }
        // register with backend
        BackendClient bc = CivilizationMod.getBackendClient();
        for (AgentRuntime rt : agents) {
            bc.registerAgent(rt.identity.agentId(), rt.identity.name(), rt.identity.personality(), rt.identity.interests());
        }
        running = true;
        startPolling(cfg);

        // In-game chat -> notify agents
        try {
            net.fabricmc.fabric.api.message.v1.ServerMessageEvents.CHAT_MESSAGE.register((message, sender, params) -> {
                try {
                    String content = message.getContent().getString();
                    String senderName = sender.getName().getString();
                    CivilizationMod.getBackendClient().sendChat(senderName, content);
                } catch (Exception e) {
                    CivilizationMod.LOGGER.warn("Chat forward failed: {}", e.toString());
                }
            });
        } catch (Exception e) {
            CivilizationMod.LOGGER.warn("Chat event registration failed: {}", e.toString());
        }
    }

    private void startPolling(ModConfig cfg) {
        pollThread = new Thread(() -> {
            while (running) {
                try {
                    for (AgentRuntime rt : agents) {
                        // Auto-respawn if dead
                        if (rt.playerEntity != null && rt.playerEntity.isDead()) {
                            try {
                                net.minecraft.server.network.ServerPlayerEntity old = rt.playerEntity;
                                server.getPlayerManager().remove(old);
                                net.minecraft.server.network.ServerPlayerEntity np = server.getPlayerManager().respawnPlayer(old, false, net.minecraft.entity.Entity.RemovalReason.KILLED);
                                np.networkHandler = new FakeNetworkHandler(server, np);
                                np.refreshPositionAndAngles(rt.position.getX() + 0.5, rt.position.getY(), rt.position.getZ() + 0.5, 0.0F, 0.0F);
                                np.setCustomName(net.minecraft.text.Text.literal(rt.identity.name()));
                                np.setCustomNameVisible(true);
                                server.getPlayerManager().getPlayerList().add(np);
                                rt.playerEntity = np;
                                // broadcast tab list entry + entity spawn to real players
                                try {
                                    net.minecraft.network.packet.s2c.play.PlayerListS2CPacket pkt = new net.minecraft.network.packet.s2c.play.PlayerListS2CPacket(net.minecraft.network.packet.s2c.play.PlayerListS2CPacket.Action.ADD_PLAYER, np);
                                    for (var p : server.getPlayerManager().getPlayerList()) {
                                        if (p != np && p.networkHandler != null) p.networkHandler.sendPacket(pkt);
                                    }
                                } catch (Exception ignored) {}
                                CivilizationMod.LOGGER.info("Respawned agent {}", rt.identity.name());
                            } catch (Exception e) {
                                CivilizationMod.LOGGER.warn("Respawn failed for {}: {}", rt.identity.name(), e.toString());
                            }
                        }
                        // Auto-survival (no AI needed)
                        AutoSurvival.tick(server, rt);
                        // push observation
                        var obs = ObservationScanner.scan(server, rt);
                        CivilizationMod.getBackendClient().pushObservation(rt.identity.agentId(), obs);
                        // pull pending actions
                        var actions = CivilizationMod.getBackendClient().pullActions(rt.identity.agentId());
                        ActionExecutor.execute(server, rt, actions);
                        // sync player entity position only when it changed (so knockback/physics aren't overridden)
                        if (rt.playerEntity != null) {
                            try {
                                BlockPos prev = lastSynced.get(rt);
                                if (prev == null || !prev.equals(rt.position)) {
                                    rt.playerEntity.refreshPositionAndAngles(rt.position.getX() + 0.5, rt.position.getY(), rt.position.getZ() + 0.5, 0.0F, 0.0F);
                                    rt.playerEntity.teleport(server.getOverworld(), rt.position.getX() + 0.5, rt.position.getY(), rt.position.getZ() + 0.5, 0.0F, 0.0F);
                                    rt.playerEntity.setVelocity(0, 0, 0);
                                    rt.playerEntity.velocityModified = true;
                                    lastSynced.put(rt, rt.position);
                                    CivilizationMod.LOGGER.info("Synced {} to {}", rt.identity.name(), rt.position);
                                }
                            } catch (Exception e) {
                                CivilizationMod.LOGGER.warn("Teleport failed for {}: {}", rt.identity.name(), e.toString());
                            }
                        }
                    }
                } catch (Exception e) {
                    CivilizationMod.LOGGER.error("Agent loop error", e);
                }
                try { Thread.sleep(cfg.decisionPollSeconds * 1000L); } catch (InterruptedException ignored) {}
            }
        }, "civ-agent-loop");
        pollThread.setDaemon(true);
        pollThread.start();
    }

    public void shutdown() {
        running = false;
        if (pollThread != null) pollThread.interrupt();
        for (AgentRuntime rt : agents) {
            // persist identity/state to backend (best effort)
        }
    }

    public List<AgentRuntime> getAgents() { return agents; }
}