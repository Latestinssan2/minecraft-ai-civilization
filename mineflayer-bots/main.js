import mineflayer from 'mineflayer';
import * as pfPkg from 'mineflayer-pathfinder';
const pathfinder = pfPkg.pathfinder;
const Movements = pfPkg.Movements;
const goals = pfPkg.default.goals;
import pvpPkg from 'mineflayer-pvp';
const pvp = pvpPkg.plugin;
import autoEatPkg from 'mineflayer-auto-eat';
const autoEat = autoEatPkg.plugin;
import collectBlockPkg from 'mineflayer-collectblock';
const collectBlock = collectBlockPkg.plugin;
import axios from 'axios';

const BACKEND = process.env.BACKEND_URL || 'http://localhost:8000';
const HOST = process.env.MC_HOST || 'localhost';
const PORT = parseInt(process.env.MC_PORT || '25565', 10);

const AGENTS = [
  { id: 'agent_01', name: 'CHAIWALA', personality: 'Curious, ambitious, independent, strategic' },
  { id: 'agent_02', name: 'Arin', personality: 'Intelligent, practical, patient, creative, organized' },
  { id: 'agent_03', name: 'Mira', personality: 'Adventurous, curious, social, independent, adaptable' },
];

async function api(path, method = 'get', body) {
  try {
    const r = await axios({ method, url: BACKEND + path, data: body, timeout: 10000 });
    return r.data;
  } catch (e) {
    return null;
  }
}

function createBot(agent) {
  const bot = mineflayer.createBot({ host: HOST, port: PORT, username: agent.name, auth: 'offline' });
  bot.loadPlugin(pathfinder);
  bot.loadPlugin(pvp);
  bot.loadPlugin(autoEat);
  bot.loadPlugin(collectBlock);

  bot.on('spawn', async () => {
    console.log(`[${agent.name}] spawned`);
    await api('/api/agents/add', 'post', { agent_id: agent.id, name: agent.name, personality: agent.personality, interests: [], skin: '' });
    const mc = new Movements(bot);
    bot.pathfinder.setMovements(mc);
    bot.autoEat.options = { priority: 'foodPoints', startAt: 14, bannedFood: [] };
    startLoops(bot, agent);
  });

  bot.on('chat', (username, message) => {
    if (username === bot.username) return;
    api('/api/chat/ingame', 'post', { sender: username, content: message });
  });

  bot.on('death', () => {
    console.log(`[${agent.name}] died`);
  });

  bot.on('error', (e) => console.log(`[${agent.name}] error:`, e.message));
  bot.on('end', () => { console.log(`[${agent.name}] disconnected`); setTimeout(() => createBot(agent), 5000); });

  async function pushObservation() {
    const pos = bot.entity.position;
    const inv = {};
    for (const item of bot.inventory.items()) {
      inv[item.name] = (inv[item.name] || 0) + item.count;
    }
    const mobs = Object.values(bot.entities)
      .filter(e => e.type === 'mob' || e.type === 'hostile')
      .slice(0, 10)
      .map(e => ({ type: e.name || e.mobType || 'mob', x: Math.floor(e.position.x), y: Math.floor(e.position.y), z: Math.floor(e.position.z) }));
    const dropped = Object.values(bot.entities)
      .filter(e => e.type === 'object')
      .slice(0, 10)
      .map(e => ({ item: 'item', x: Math.floor(e.position.x), y: Math.floor(e.position.y), z: Math.floor(e.position.z) }));
    const obs = {
      agent_id: agent.id,
      position: { x: Math.floor(pos.x), y: Math.floor(pos.y), z: Math.floor(pos.z) },
      biome: 'unknown',
      health: bot.health,
      hunger: bot.food,
      inventory: inv,
      hotbar_slot: bot.quickBarSlot,
      nearby_mobs: mobs,
      dropped_items: dropped,
      nearby_blocks: {},
      nearby_entities: mobs.map(m => m.type),
      nearby_agents: AGENTS.filter(a => a.name !== agent.name).map(a => a.id),
      nearby_signs: [],
      structures: [],
    };
    await api('/api/observations', 'post', { agent_id: agent.id, observation: obs });
  }

  async function pullAndExecute() {
    const actions = await api(`/api/agents/${agent.id}/actions/pending`);
    if (!Array.isArray(actions)) return;
    for (const a of actions) {
      await executeAction(bot, agent, a);
    }
  }

  async function executeAction(bot, agent, a) {
    const action = a.action;
    const p = a.parameters || {};
    let ok = true, result = {}, err = null;
    try {
      switch (action) {
        case 'move_to':
        case 'auto_walk': {
          const g = new goals.GoalBlock(p.x, p.y, p.z);
          await bot.pathfinder.goto(g);
          result = { success: true };
          break;
        }
        case 'mine_block':
        case 'automine': {
          const mcData = (await import('minecraft-data')).default(bot.version);
          const blockName = p.block_type || p.ore || p.resource || 'stone';
          const blockType = mcData.blocksByName[blockName];
          if (!blockType) { ok = false; err = 'unknown block'; break; }
          const block = bot.findBlock({ matching: blockType.id, maxDistance: 32 });
          if (!block) { ok = false; err = 'not found'; break; }
          await bot.collectBlock.collect(block);
          result = { success: true, collected: blockName };
          break;
        }
        case 'attack':
        case 'pvp_attack': {
          const target = p.target
            ? Object.values(bot.entities).find(e => (e.username || e.name || e.displayName) === p.target)
            : Object.values(bot.entities).find(e => e.type === 'mob' || e.type === 'hostile');
          if (target) { bot.pvp.attack(target); result = { success: true }; }
          else { ok = false; err = 'no target'; }
          break;
        }
        case 'eat_food': {
          await bot.autoEat.eat();
          result = { success: true };
          break;
        }
        case 'send_message':
        case 'chat': {
          const msg = p.message || p.content || '';
          bot.chat(msg);
          result = { success: true };
          break;
        }
        case 'look_at': {
          await bot.lookAt(new (await import('vec3')).default(p.x, p.y, p.z));
          result = { success: true };
          break;
        }
        case 'follow_agent': {
          const target = AGENTS.find(a => a.id === p.agent_id);
          const entity = target ? Object.values(bot.entities).find(e => e.username === target.name) : null;
          if (entity) { bot.pathfinder.setGoal(new goals.GoalFollow(entity, 2), true); result = { success: true }; }
          else { ok = false; err = 'target not found'; }
          break;
        }
        case 'stop_moving': {
          bot.pathfinder.setGoal(null);
          result = { success: true };
          break;
        }
        case 'switch_hotbar': {
          bot.quickBarSlot = p.slot || 0;
          result = { success: true };
          break;
        }
        case 'drop_item': {
          const item = bot.inventory.items().find(i => i.name === (p.item || p.resource));
          if (item) await bot.tossStack(item);
          result = { success: true };
          break;
        }
        default:
          result = { success: true, note: 'unhandled ' + action };
      }
    } catch (e) {
      ok = false; err = e.message;
    }
    await api(`/api/actions/${a.action_id}/result`, 'post', { action_id: a.action_id, agent_id: agent.id, status: ok ? 'succeeded' : 'failed', result, error: err });
    await api('/api/memory', 'post', { agent_id: agent.id, content: `Action ${action} ${ok ? 'succeeded' : 'failed'}: ${JSON.stringify(result)}`, memory_type: 'episodic', importance: 0.4 });
  }

  function startLoops(bot, agent) {
    pushObservation();
    setInterval(pushObservation, 2000);
    setInterval(pullAndExecute, 1000);
    setTimeout(() => api(`/api/agents/${agent.id}/decide`, 'post'), 3000);
  }
}

for (const agent of AGENTS) {
  createBot(agent);
}
console.log('Civilization bots starting...');
