package com.civilization.agents;

import net.minecraft.network.ClientConnection;
import net.minecraft.network.NetworkSide;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ConnectedClientData;
import net.minecraft.server.network.ServerPlayNetworkHandler;
import net.minecraft.server.network.ServerPlayerEntity;

public class FakeNetworkHandler extends ServerPlayNetworkHandler {
    public FakeNetworkHandler(MinecraftServer server, ServerPlayerEntity player) {
        super(server, new ClientConnection(NetworkSide.SERVERBOUND), player,
              ConnectedClientData.createDefault(player.getGameProfile(), false));
    }

    @Override
    public void sendPacket(net.minecraft.network.packet.Packet<?> packet) {
        // no-op: agent is not a real client
    }

    @Override
    public void send(net.minecraft.network.packet.Packet<?> packet, net.minecraft.network.PacketCallbacks callbacks) {
        // no-op
    }
}