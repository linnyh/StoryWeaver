<template>
  <div class="relative w-full h-full">
    <div class="relationship-graph-container" ref="graphContainer"></div>
    
    <!-- Tooltip -->
    <div 
        v-if="tooltip.visible"
        class="absolute z-50 p-3 bg-space-900/90 backdrop-blur-md border border-neon-blue/30 rounded-lg shadow-[0_0_15px_rgba(0,240,255,0.2)] text-xs text-gray-200 w-[250px] pointer-events-none transition-all duration-200"
        :style="{ left: tooltip.x + 'px', top: tooltip.y + 'px' }"
    >
        <div class="flex items-center justify-between mb-2 border-b border-white/10 pb-1">
            <span class="font-bold text-neon-blue text-sm">{{ tooltip.data.name }}</span>
            <span class="text-[10px] px-1.5 py-0.5 rounded bg-white/10 text-gray-400">{{ tooltip.data.role || 'NPC' }}</span>
        </div>
        
        <div class="space-y-1.5">
            <div v-if="tooltip.data.bio">
                <span class="text-gray-500 font-bold">Bio:</span>
                <span class="text-gray-300 ml-1 line-clamp-3">{{ tooltip.data.bio }}</span>
            </div>
            <div v-if="tooltip.data.personality">
                <span class="text-gray-500 font-bold">Personality:</span>
                <span class="text-gray-300 ml-1">{{ tooltip.data.personality }}</span>
            </div>
            <div v-if="tooltip.data.power_state?.realm">
                <span class="text-gray-500 font-bold">Realm:</span>
                <span class="text-neon-purple ml-1">{{ tooltip.data.power_state.realm }}</span>
            </div>
        </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick, reactive } from 'vue';
import { Graph, ElementEvent } from '@antv/g6';

const props = defineProps<{
  characters: any[];
  relationships: any[];
}>();

const graphContainer = ref<HTMLElement | null>(null);
let graph: any = null;

const tooltip = reactive({
    visible: false,
    x: 0,
    y: 0,
    data: {} as any
});

const initGraph = () => {
  if (!graphContainer.value) return;

  const width = graphContainer.value.clientWidth || 800;
  const height = graphContainer.value.clientHeight || 500;

  const nodes = props.characters.map(char => ({
    id: char.id,
    data: {
      label: char.name,
      ...char
    },
    style: {
      fill: '#16213e',
      stroke: '#00f0ff',
      lineWidth: 2,
    }
  }));

  const edges = props.relationships.map(rel => {
    let color = '#999';
    let label = rel.affinity_score.toString();
    
    if (rel.affinity_score > 60) color = '#00ff9d'; // 亲密 (Neon Green)
    else if (rel.affinity_score > 20) color = '#00f0ff'; // 友善 (Neon Blue)
    else if (rel.affinity_score < -60) color = '#ff2a6d'; // 仇恨 (Neon Red)
    else if (rel.affinity_score < -20) color = '#f5d300'; // 敌对 (Neon Yellow)

    return {
      source: rel.character_a_id,
      target: rel.character_b_id,
      data: {
        label: label,
        ...rel
      },
      style: {
        stroke: color,
        lineWidth: Math.max(1, Math.abs(rel.affinity_score) / 20),
        endArrow: true,
        labelText: label,
        labelFill: color,
        labelBackground: true,
        labelBackgroundFill: '#1a1a2e',
        labelBackgroundOpacity: 0.8,
        labelBackgroundRadius: 4,
      }
    };
  });
  
  // Debug log
  console.log('Graph Nodes:', nodes);
  console.log('Graph Edges:', edges);
  
  // Clean up old instance
  if (graph) {
    graph.destroy();
  }

  graph = new Graph({
    container: graphContainer.value,
    width,
    height,
    data: {
      nodes,
      edges,
    },
    layout: {
      type: 'force',
      preventOverlap: true,
      nodeSize: 50,
      linkDistance: 200,
    },
    behaviors: ['drag-canvas', 'zoom-canvas', 'drag-element'],
    node: {
        type: 'circle',
        style: {
            size: 40,
            fill: '#0f3460',
            stroke: '#e94560',
            lineWidth: 2,
            labelText: (d: any) => d.data.label,
            labelPlacement: 'bottom',
            labeloffset: 5,
            labelFill: '#fff',
            labelFontSize: 12,
        }
    },
    edge: {
        type: 'line',
        style: {
            labelText: (d: any) => d.data.label,
            labelBackground: true,
            labelFill: '#fff',
        }
    }
  });

  graph.render();

  // Event Listeners for Tooltip
  graph.on('node:pointerenter', (e: any) => {
      const node = e.target;
      // Get the model data from the node
      // In G6 v5, we might need to access data differently depending on the event object structure
      // e.target.id usually gives the node ID
      // We can find the data from our props or if G6 attaches it
      
      const nodeId = e.target.id;
      const charData = props.characters.find(c => c.id === nodeId);
      
      if (charData) {
          tooltip.data = charData;
          tooltip.visible = true;
          
          // Calculate position
          // e.client or e.canvas might be available
          // We need relative position to the container
          const containerRect = graphContainer.value!.getBoundingClientRect();
          
          // Use client coordinates for simplicity relative to viewport, but we need relative to container
          // e.client is viewport coordinates
          // But wait, G6 event object might have different properties
          // Let's try to use the canvas coordinates if available, or just use mouse position
          
          tooltip.x = e.client.x - containerRect.left + 15;
          tooltip.y = e.client.y - containerRect.top + 15;
          
          // Boundary check
          if (tooltip.x + 250 > containerRect.width) {
              tooltip.x = e.client.x - containerRect.left - 265;
          }
          if (tooltip.y + 200 > containerRect.height) {
              tooltip.y = e.client.y - containerRect.top - 200;
          }
      }
  });

  graph.on('node:pointerleave', () => {
      tooltip.visible = false;
  });
  
  graph.on('node:pointermove', (e: any) => {
      if (tooltip.visible) {
          const containerRect = graphContainer.value!.getBoundingClientRect();
          tooltip.x = e.client.x - containerRect.left + 15;
          tooltip.y = e.client.y - containerRect.top + 15;
          
           // Boundary check
          if (tooltip.x + 250 > containerRect.width) {
              tooltip.x = e.client.x - containerRect.left - 265;
          }
           if (tooltip.y + 200 > containerRect.height) {
              tooltip.y = e.client.y - containerRect.top - 200;
          }
      }
  });
};

watch(() => [props.characters, props.relationships], () => {
    nextTick(() => {
        initGraph();
    });
}, { deep: true });

onMounted(() => {
    nextTick(() => {
        initGraph();
    });
});

onUnmounted(() => {
  if (graph) {
    graph.destroy();
  }
});
</script>

<style scoped>
.relationship-graph-container {
  width: 100%;
  height: 600px;
  border-radius: 8px;
  background-color: transparent; /* Transparent for glassmorphism */
}
</style>