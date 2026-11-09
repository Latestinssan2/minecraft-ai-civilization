package com.civilization.agents;

import com.civilization.CivilizationMod;
import com.civilization.config.ModConfig;
import com.civilization.entities.AgentEntity;
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
        }
        // register with backend
        BackendClient bc = CivilizationMod.getBackendClient();
        for (AgentRuntime rt : agents) {
            bc.registerAgent(rt.identity.agentId, rt.identity.name, rt.identity.personality, rt.identity.interests());
        }
        running = true;
        startPolling(cfg);
    }

    private void startPolling(ModConfig cfg) {
        pollThread = new Thread(() -> {
            while (running) {
                try {
                    for (AgentRuntime rt : agents) {
                        // push observation
                        var obs = ObservationScanner.scan(server, rt);
                        CivilizationMod.getBackendClient().pushObservation(rt.identity.agentId, obs);
                        // pull pending actions
                        var actions = CivilizationMod.getBackendClient().pullActions(rt.identity.agentId);
                        ActionExecutor.execute(server, rt, actions);
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