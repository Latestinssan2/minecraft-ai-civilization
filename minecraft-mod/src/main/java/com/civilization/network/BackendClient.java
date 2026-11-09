package com.civilization.network;

import com.civilization.CivilizationMod;
import com.google.gson.Gson;
import com.google.gson.JsonObject;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.List;
import java.util.Map;

public class BackendClient {
    private final String base;
    private final HttpClient client;
    private final Gson gson = new Gson();

    public BackendClient(String base) {
        this.base = base.replaceAll("/$", "");
        this.client = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(10)).build();
    }

    private void post(String path, Object body) {
        try {
            String json = gson.toJson(body);
            HttpRequest req = HttpRequest.newBuilder(URI.create(base + path))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(json))
                .timeout(Duration.ofSeconds(30)).build();
            client.send(req, HttpResponse.BodyHandlers.discarding());
        } catch (Exception e) {
            CivilizationMod.LOGGER.warn("Backend POST {} failed: {}", path, e.getMessage());
        }
    }

    @SuppressWarnings("unchecked")
    private String get(String path) {
        try {
            HttpRequest req = HttpRequest.newBuilder(URI.create(base + path))
                .GET().timeout(Duration.ofSeconds(30)).build();
            HttpResponse<String> res = client.send(req, HttpResponse.BodyHandlers.ofString());
            return res.body();
        } catch (Exception e) {
            CivilizationMod.LOGGER.warn("Backend GET {} failed: {}", path, e.getMessage());
            return "[]";
        }
    }

    public void registerAgent(String id, String name, String personality, List<String> interests) {
        post("/api/agents/register", Map.of("agent_id", id, "name", name, "personality", personality, "interests", interests));
    }

    public void pushObservation(String agentId, Map<String, Object> obs) {
        post("/api/observations", Map.of("agent_id", agentId, "observation", obs));
    }

    public void sendChat(String sender, String content) {
        post("/api/chat/ingame", Map.of("sender", sender, "content", content));
    }

    @SuppressWarnings("unchecked")
    public List<Map<String, Object>> pullActions(String agentId) {
        String body = get("/api/agents/" + agentId + "/actions/pending");
        try {
            return gson.fromJson(body, List.class);
        } catch (Exception e) {
            return List.of();
        }
    }

    public void reportActionResult(String actionId, String agentId, boolean ok, Map<String, Object> result, String error) {
        post("/api/actions/result", Map.of(
            "action_id", actionId,
            "agent_id", agentId,
            "status", ok ? "succeeded" : "failed",
            "result", result,
            "error", error == null ? "" : error
        ));
    }
}