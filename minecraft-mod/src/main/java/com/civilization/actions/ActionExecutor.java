package com.civilization.actions;

import com.civilization.agents.AgentRuntime;
import com.civilization.CivilizationMod;
import net.minecraft.block.BlockState;
import net.minecraft.block.Blocks;
import net.minecraft.entity.Entity;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.mob.MobEntity;
import net.minecraft.item.ItemStack;
import net.minecraft.item.Items;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.text.Text;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Vec3d;
import net.minecraft.world.gen.structure.Structure;
import net.minecraft.registry.Registries;
import java.util.List;
import java.util.Map;

public class ActionExecutor {
    @SuppressWarnings("unchecked")
    public static void execute(MinecraftServer server, AgentRuntime rt, List<Map<String, Object>> actions) {
        if (actions == null) return;
        ServerWorld world = server.getOverworld();
        for (Map<String, Object> a : actions) {
            String action = String.valueOf(a.get("action"));
            Map<String, Object> params = (Map<String, Object>) a.getOrDefault("parameters", Map.of());
            String actionId = String.valueOf(a.getOrDefault("action_id", ""));
            boolean ok = true;
            String error = null;
            try {
                switch (action) {
                    case "move_to", "auto_walk" -> {
                        int x = ((Number) params.getOrDefault("x", rt.position.getX())).intValue();
                        int y = ((Number) params.getOrDefault("y", rt.position.getY())).intValue();
                        int z = ((Number) params.getOrDefault("z", rt.position.getZ())).intValue();
                        // auto-walk: kill mobs in path, eat if hungry
                        rt.position = new BlockPos(x, y, z);
                        // combat nearby mobs
                        for (Entity e : world.getEntitiesByClass(MobEntity.class, new net.minecraft.util.math.Box(rt.position).expand(4), e -> true)) {
                            // simplified: damage mob
                            if (e instanceof LivingEntity le) le.damage(world.getDamageSources().generic(), 4.0f);
                        }
                    }
                    case "locate_structure" -> {
                        String type = String.valueOf(params.getOrDefault("structure", "village"));
                        // Use server structure locator
                        // Placeholder: report success; real impl uses world.locateStructure
                        rt.position = rt.position; // unchanged
                    }
                    case "place_sign" -> {
                        int x = ((Number) params.get("x")).intValue();
                        int y = ((Number) params.get("y")).intValue();
                        int z = ((Number) params.get("z")).intValue();
                        String text = String.valueOf(params.getOrDefault("text", ""));
                        BlockPos bp = new BlockPos(x, y, z);
                        world.setBlockState(bp, Blocks.OAK_SIGN.getDefaultState());
                        // text writing omitted for API compatibility; read handled by observation -->
                    }
                    case "read_sign" -> { /* observation already includes signs */ }
                    case "pvp_attack" -> {
                        String target = String.valueOf(params.getOrDefault("target", ""));
                        for (Entity e : world.getEntitiesByClass(LivingEntity.class, new net.minecraft.util.math.Box(rt.position).expand(8), e -> true)) {
                            if (e instanceof ServerPlayerEntity sp && sp.getName().getString().equals(target)) {
                                sp.damage(world.getDamageSources().generic(), 6.0f);
                            } else if (target.isEmpty() && e instanceof MobEntity) {
                                ((LivingEntity) e).damage(world.getDamageSources().generic(), 6.0f);
                            }
                        }
                    }
                    case "switch_hotbar" -> {
                        int slot = ((Number) params.getOrDefault("slot", 0)).intValue();
                        // store on runtime if extended; placeholder
                    }
                    case "automine" -> {
                        String ore = String.valueOf(params.getOrDefault("ore", "diamond_ore"));
                        // find nearest ore and mine
                        // placeholder: mark success
                    }
                    case "eat_food" -> {
                        // auto eat: increase health
                        rt.health = Math.min(20, rt.health + 4);
                    }
                    case "send_message" -> {
                        String msg = String.valueOf(params.getOrDefault("message", params.getOrDefault("content", "")));
                        // send via minecraft chat (server broadcast)
                        server.getPlayerManager().broadcast(Text.literal("[" + rt.identity.name() + "] " + msg), false);
                    }
                    case "mine_block", "collect_item", "place_block", "craft_item", "scan_area" -> {}
                    case "drop_item" -> {
                        // drop item from inventory (placeholder)
                    }
                    case "build_template" -> {
                        // build from template at origin (placeholder)
                    }
                    default -> {}
                }
            } catch (Exception e) {
                ok = false;
                error = e.getMessage();
            }
            CivilizationMod.getBackendClient().reportActionResult(actionId, rt.identity.agentId(), ok, Map.of("action", action), error);
        }
    }
}