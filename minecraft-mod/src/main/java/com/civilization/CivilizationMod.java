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