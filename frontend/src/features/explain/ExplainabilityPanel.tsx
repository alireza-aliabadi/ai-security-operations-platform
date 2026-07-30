import Editor from '@monaco-editor/react'

const evidence = `{
  "hypothesis": "Compromised service account used for lateral movement into finance VPC",
  "confidence": 0.82,
  "features": [
    { "name": "auth_anomaly_score", "weight": 0.31, "value": 0.94 },
    { "name": "smb_enumeration_burst", "weight": 0.24, "value": 0.88 },
    { "name": "geo_novelty", "weight": 0.18, "value": 0.76 },
    { "name": "mitre_overlap", "weight": 0.15, "value": 0.71 },
    { "name": "ti_hit_rate", "weight": 0.12, "value": 0.55 }
  ],
  "counterfactuals": [
    "If SMB probes < 20, severity drops to medium",
    "If source ASN is corporate egress, confidence -0.22"
  ]
}`

export function ExplainabilityPanel() {
  return (
    <div className="space-y-3">
      <p className="text-sm text-slate-400">
        Feature attributions and counterfactuals for the current investigation verdict.
      </p>
      <div className="overflow-hidden rounded-md border border-slate-700">
        <Editor
          height="320px"
          defaultLanguage="json"
          value={evidence}
          theme="vs-dark"
          options={{
            readOnly: true,
            minimap: { enabled: false },
            fontSize: 12,
            fontFamily: 'IBM Plex Mono, monospace',
            scrollBeyondLastLine: false,
            lineNumbers: 'on',
          }}
        />
      </div>
    </div>
  )
}
