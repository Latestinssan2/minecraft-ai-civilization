package com.civilization.config;

import com.civilization.CivilizationMod;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Properties;

public class ModConfig {
    public String backendUrl = "http://localhost:8000";
    public int agentCount = 3;
    public int observationRadius = 32;
    public int decisionPollSeconds = 5;

    public static ModConfig load() {
        ModConfig cfg = new ModConfig();
        Path p = Path.of("config", "civilization-mod.properties");
        if (Files.exists(p)) {
            Properties props = new Properties();
            try (var in = Files.newInputStream(p)) {
                props.load(in);
                cfg.backendUrl = props.getProperty("backendUrl", cfg.backendUrl);
                cfg.agentCount = Integer.parseInt(props.getProperty("agentCount", String.valueOf(cfg.agentCount)));
                cfg.observationRadius = Integer.parseInt(props.getProperty("observationRadius", String.valueOf(cfg.observationRadius)));
            } catch (IOException e) {
                CivilizationMod.LOGGER.warn("Failed to load mod config", e);
            }
        }
        return cfg;
    }
}