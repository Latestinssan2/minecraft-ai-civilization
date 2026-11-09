package com.civilization.observation;

import com.civilization.agents.AgentRuntime;
import com.google.gson.JsonObject;
import net.minecraft.block.BlockState;
import net.minecraft.entity.Entity;
import net.minecraft.entity.ItemEntity;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.mob.MobEntity;
import net.minecraft.registry.Registries;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Box;
import java.util.*;

public class ObservationScanner {
    public static Map<String, Object> scan(MinecraftServer server, AgentRuntime rt) {
        ServerWorld world = server.getOverworld();
        BlockPos pos = rt.position;
        int radius = 16;
        Map<String, Object> obs = new HashMap<>();
        obs.put("agent_id", rt.identity.agentId());
        obs.put("timestamp", java.time.Instant.now().toString());
        obs.put("world_id", world.getRegistryKey().getValue().toString());
        Map<String, Object> p = new HashMap<>();
        p.put("x", pos.getX()); p.put("y", pos.getY()); p.put("z", pos.getZ());
        obs.put("position", p);
        obs.put("biome", world.getBiome(pos).getKey().map(k -> k.getValue().toString()).orElse("unknown"));
        obs.put("health", rt.health);
        obs.put("hunger", 20); // placeholder; real via player entity if used
        obs.put("hotbar_slot", 0);

        Map<String, Integer> blocks = new HashMap<>();
        for (int dx = -radius; dx <= radius; dx++) {
            for (int dz = -radius; dz <= radius; dz++) {
                for (int dy = -4; dy <= 4; dy++) {
                    BlockPos bp = pos.add(dx, dy, dz);
                    if (!world.isChunkLoaded(bp)) continue;
                    BlockState st = world.getBlockState(bp);
                    if (st.isAir()) continue;
                    String name = Registries.BLOCK.getId(st.getBlock()).getPath();
                    blocks.merge(name, 1, Integer::sum);
                }
            }
        }
        obs.put("nearby_blocks", blocks);

        // nearby mobs
        List<Map<String, Object>> mobs = new ArrayList<>();
        for (Entity e : world.getEntitiesByClass(LivingEntity.class, new Box(pos).expand(radius), e -> e instanceof MobEntity)) {
            Map<String, Object> m = new HashMap<>();
            m.put("type", Registries.ENTITY_TYPE.getId(e.getType()).getPath());
            m.put("x", e.getX()); m.put("y", e.getY()); m.put("z", e.getZ());
            m.put("distance", Math.sqrt(e.squaredDistanceTo(pos.getX(), pos.getY(), pos.getZ())));
            mobs.add(m);
        }
        obs.put("nearby_mobs", mobs);

        // dropped items
        List<Map<String, Object>> dropped = new ArrayList<>();
        for (Entity e : world.getEntitiesByClass(ItemEntity.class, new Box(pos).expand(radius), e -> true)) {
            ItemEntity ie = (ItemEntity) e;
            Map<String, Object> d = new HashMap<>();
            d.put("item", Registries.ITEM.getId(ie.getStack().getItem()).getPath());
            d.put("count", ie.getStack().getCount());
            d.put("x", e.getX()); d.put("y", e.getY()); d.put("z", e.getZ());
            dropped.add(d);
        }
        obs.put("dropped_items", dropped);

        // nearby signs
        List<Map<String, Object>> signs = new ArrayList<>();
        // scan for sign blocks
        for (int dx = -radius; dx <= radius; dx++) {
            for (int dz = -radius; dz <= radius; dz++) {
                for (int dy = -4; dy <= 4; dy++) {
                    BlockPos bp = pos.add(dx, dy, dz);
                    if (!world.isChunkLoaded(bp)) continue;
                    BlockState st = world.getBlockState(bp);
                    if (st.getBlock() instanceof net.minecraft.block.AbstractSignBlock) {
                        // read text
                        var be = world.getBlockEntity(bp);
                        List<String> lines = new ArrayList<>();
                        if (be instanceof net.minecraft.block.entity.SignBlockEntity sbe) {
                            for (int i = 0; i < 4; i++) lines.add(sbe.getText(true).getMessage(i, false).getString());
                        }
                        Map<String, Object> s = new HashMap<>();
                        s.put("x", bp.getX()); s.put("y", bp.getY()); s.put("z", bp.getZ());
                        s.put("text", String.join(" | ", lines));
                        signs.add(s);
                    }
                }
            }
        }
        obs.put("nearby_signs", signs);

        // nearby agents placeholder
        obs.put("nearby_agents", new ArrayList<>());
        obs.put("nearby_entities", mobs.stream().map(m -> (String) m.get("type")).distinct().toList());
        obs.put("inventory", new HashMap<>());
        obs.put("structures", new ArrayList<>()); // located via locate_structure action
        return obs;
    }
}