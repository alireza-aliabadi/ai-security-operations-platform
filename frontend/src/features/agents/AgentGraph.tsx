import {
  Background,
  Controls,
  MarkerType,
  MiniMap,
  ReactFlow,
  type Edge,
  type Node,
} from '@xyflow/react'

const nodes: Node[] = [
  { id: 'planner', position: { x: 40, y: 160 }, data: { label: 'Planner' }, style: nodeStyle('#22d3ee') },
  { id: 'coordinator', position: { x: 220, y: 160 }, data: { label: 'Coordinator' }, style: nodeStyle('#67e8f9') },
  { id: 'keywords', position: { x: 400, y: 40 }, data: { label: 'Keyword Extractor' }, style: nodeStyle('#94a3b8') },
  { id: 'retriever', position: { x: 400, y: 160 }, data: { label: 'Retriever' }, style: nodeStyle('#94a3b8') },
  { id: 'correlator', position: { x: 400, y: 280 }, data: { label: 'Correlator' }, style: nodeStyle('#94a3b8') },
  { id: 'rag', position: { x: 600, y: 80 }, data: { label: 'RAG Agent' }, style: nodeStyle('#2dd4bf') },
  { id: 'analyzer', position: { x: 600, y: 200 }, data: { label: 'Analyzer' }, style: nodeStyle('#2dd4bf') },
  { id: 'mitre', position: { x: 780, y: 80 }, data: { label: 'MITRE Mapper' }, style: nodeStyle('#38bdf8') },
  { id: 'ti', position: { x: 780, y: 200 }, data: { label: 'Threat Intel' }, style: nodeStyle('#38bdf8') },
  { id: 'reporter', position: { x: 960, y: 120 }, data: { label: 'Reporter' }, style: nodeStyle('#34d399') },
  { id: 'critic', position: { x: 960, y: 240 }, data: { label: 'Critic' }, style: nodeStyle('#fbbf24') },
  { id: 'memory', position: { x: 1140, y: 180 }, data: { label: 'Memory' }, style: nodeStyle('#a78bfa') },
]

const edges: Edge[] = [
  e('planner', 'coordinator'),
  e('coordinator', 'keywords'),
  e('coordinator', 'retriever'),
  e('coordinator', 'correlator'),
  e('keywords', 'rag'),
  e('retriever', 'analyzer'),
  e('correlator', 'analyzer'),
  e('rag', 'mitre'),
  e('analyzer', 'ti'),
  e('mitre', 'reporter'),
  e('ti', 'reporter'),
  e('reporter', 'critic'),
  e('critic', 'memory'),
  e('memory', 'planner'),
]

function nodeStyle(border: string) {
  return {
    background: '#0f172a',
    color: '#e2e8f0',
    border: `1px solid ${border}`,
    borderRadius: 8,
    fontSize: 12,
    padding: '8px 12px',
    width: 140,
  }
}

function e(source: string, target: string): Edge {
  return {
    id: `${source}-${target}`,
    source,
    target,
    animated: true,
    style: { stroke: '#334155' },
    markerEnd: { type: MarkerType.ArrowClosed, color: '#64748b' },
  }
}

export function AgentGraph() {
  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      fitView
      proOptions={{ hideAttribution: true }}
      nodesDraggable={false}
      nodesConnectable={false}
      elementsSelectable={false}
    >
      <Background color="#1e293b" gap={18} />
      <MiniMap
        nodeColor="#164e63"
        maskColor="rgba(15,23,42,0.8)"
        style={{ background: '#0f172a' }}
      />
      <Controls />
    </ReactFlow>
  )
}
