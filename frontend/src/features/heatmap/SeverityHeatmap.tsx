import {
  CartesianGrid,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from 'recharts'

const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
const sevs = ['low', 'medium', 'high', 'critical']

const data = days.flatMap((day, di) =>
  sevs.map((sev, si) => ({
    x: di,
    y: si,
    z: 6 + ((di * 7 + si * 11) % 37) + si * 4,
    day,
    sev,
  })),
)

export function SeverityHeatmap() {
  return (
    <div className="h-56 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart margin={{ top: 8, right: 8, bottom: 8, left: 8 }}>
          <CartesianGrid stroke="#1e293b" />
          <XAxis
            type="number"
            dataKey="x"
            domain={[-0.5, 6.5]}
            tickFormatter={(v) => days[v] ?? ''}
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            axisLine={{ stroke: '#334155' }}
          />
          <YAxis
            type="number"
            dataKey="y"
            domain={[-0.5, 3.5]}
            tickFormatter={(v) => sevs[v] ?? ''}
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            width={64}
            axisLine={{ stroke: '#334155' }}
          />
          <ZAxis type="number" dataKey="z" range={[40, 400]} />
          <Tooltip
            cursor={{ strokeDasharray: '3 3' }}
            contentStyle={{ background: '#0f172a', border: '1px solid #334155' }}
            formatter={(value, _name, item) => {
              const p = item?.payload as { day?: string; sev?: string; z?: number }
              return [`${p?.z ?? value} alerts`, `${p?.day} · ${p?.sev}`]
            }}
          />
          <Scatter
            data={data}
            fill="#22d3ee"
            fillOpacity={0.75}
          />
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  )
}
