package com.civilization.agents;

import com.civilization.CivilizationMod;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.mob.MobEntity;
import net.minecraft.item.ItemStack;
import net.minecraft.item.Items;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Vec3d;

public class AutoSurvival {
    private static final java.util.Random RAND = new java.util.Random();

    public static void tick(MinecraftServer server, AgentRuntime rt) {
        ServerWorld world = server.getOverworld();
        // Auto-eat / heal
        if (rt.health < 14) {
            rt.health = Math.min(20, rt.health + 4);
        }
        // Auto-fight: attack nearby hostile mobs
        for (var e : world.getEntitiesByClass(MobEntity.class, new net.minecraft.util.math.Box(rt.position).expand(6), e -> true)) {
            if (e instanceof LivingEntity le) {
                le.damage(world.getDamageSources().generic(), 4.0f);
            }
        }
        // Autonomous wander (deterministic, no AI cost): move to a nearby random spot
        if (RAND.nextInt(4) == 0) {
            int dx = RAND.nextInt(7) - 3;
            int dz = RAND.nextInt(7) - 3;
            BlockPos np = rt.position.add(dx, 0, dz);
            // keep on surface
            int y = world.getTopY(net.minecraft.world.Heightmap.Type.MOTION_BLOCKING, np.getX(), np.getZ());
            rt.position = new BlockPos(np.getX(), y, np.getZ());
        }
        // MLG clutch: if falling, place water (placeholder, no AI)
        // Occasional autonomous chatter (no AI cost)
        if (RAND.nextInt(20) == 0) {
            String[] msgs = {"I am exploring.", "Gathering resources.", "Building our civilization.", "Stay safe out there."};
            String msg = msgs[RAND.nextInt(msgs.length)];
            try { server.getPlayerManager().broadcast(net.minecraft.text.Text.literal("[" + rt.identity.name() + "] " + msg), false); } catch (Exception ignored) {}
        }
    }
}