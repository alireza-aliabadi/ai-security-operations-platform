import type { ElementDefinition, StylesheetStyle } from 'cytoscape'
import CytoscapeComponent from 'react-cytoscapejs'

const elements: ElementDefinition[] = [
  { data: { id: 'vpn', label: 'VPN GW' } },
  { data: { id: 'jump', label: 'finance-jump-03' } },
  { data: { id: 'ad', label: 'AD / IdP' } },
  { data: { id: 'etl', label: 'finance-etl' } },
  { data: { id: 'db', label: 'finance-db' } },
  { data: { id: 'files', label: 'SMB share' } },
  { data: { id: 'siem', label: 'Graylog' } },
  { data: { source: 'vpn', target: 'jump' } },
  { data: { source: 'jump', target: 'ad' } },
  { data: { source: 'jump', target: 'etl' } },
  { data: { source: 'etl', target: 'db' } },
  { data: { source: 'jump', target: 'files' } },
  { data: { source: 'jump', target: 'siem' } },
]

const stylesheet: StylesheetStyle[] = [
  {
    selector: 'node',
    style: {
      label: 'data(label)',
      color: '#e2e8f0',
      'background-color': '#0e7490',
      'border-color': '#22d3ee',
      'border-width': 1,
      'font-size': 10,
      'text-valign': 'center',
      'text-halign': 'center',
      width: 48,
      height: 48,
    },
  },
  {
    selector: 'edge',
    style: {
      width: 1.5,
      'line-color': '#334155',
      'target-arrow-color': '#64748b',
      'target-arrow-shape': 'triangle',
      'curve-style': 'bezier',
    },
  },
  {
    selector: '#jump',
    style: {
      'background-color': '#b45309',
      'border-color': '#f97316',
    },
  },
]

export function ServiceDependencyGraph() {
  return (
    <CytoscapeComponent
      elements={elements}
      stylesheet={stylesheet}
      layout={{ name: 'breadthfirst', directed: true, padding: 24 }}
      style={{ width: '100%', height: '100%', background: 'transparent' }}
    />
  )
}
