import { useEffect, useMemo, useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Grid,
  Stack,
  Typography,
  Divider,
  Button,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
} from '@mui/material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  Legend,
} from 'recharts';
import { useAuthStore } from '@/stores/authStore';
import { useSchemaStore } from '@/stores/schemaStore';
import { useMetadataStore } from '@/stores/metadataStore';

type DashboardStats = {
  total_metadata_records: number;
  total_schemas: number;
  total_users: number;
  total_asset_types: number;
  recent_records_7days: number;
};

type ActivityItem = {
  id: number;
  schema_id: number | null;
  schema_version: number | null;
  change_type: string;
  description: string | null;
  changed_by: number | null;
  changed_by_name: string | null;
  timestamp: string | null;
};

const COLORS = ['#6366F1', '#10B981', '#F59E0B', '#EF4444', '#3B82F6', '#8B5CF6'];

export const Analytics = () => {
  const { token, user } = useAuthStore();
  const { schemas, fetchSchemas } = useSchemaStore();
  const { records, fetchRecords } = useMetadataStore();

  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [byAssetType, setByAssetType] = useState<{ name: string; value: number }[]>([]);
  const [timeline, setTimeline] = useState<{ date: string; records: number }[]>([]);
  const [topTypes, setTopTypes] = useState<{ name: string; count: number }[]>([]);
  const [recent, setRecent] = useState<ActivityItem[]>([]);
  const [userActivity, setUserActivity] = useState<{ username: string; count: number }[]>([]);

  useEffect(() => {
    fetchSchemas();
    fetchRecords({ limit: 50 });
  }, []);

  useEffect(() => {
    const fetchAnalytics = async () => {
      const headers: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};
      const safeJson = async (res: Response) => {
        if (!res.ok) throw new Error((await res.text()) || 'Request failed');
        return res.json();
      };
      const [s, bat, tl, ta, ra] = await Promise.all([
        fetch('/api/analytics/dashboard', { headers }).then(safeJson),
        fetch('/api/analytics/metadata-by-asset-type', { headers }).then(safeJson),
        fetch('/api/analytics/metadata-timeline', { headers }).then(safeJson),
        fetch('/api/analytics/top-asset-types', { headers }).then(safeJson),
        fetch('/api/analytics/recent-activity', { headers }).then(safeJson),
      ]);
      setStats(s);
      setByAssetType(bat);
      setTimeline(tl);
      setTopTypes(ta);
      setRecent(ra);
      // Admin-only aggregated user activity
      try {
        if (user?.role === 'admin') {
          const ua = await fetch('/api/analytics/user-activity', { headers }).then(safeJson);
          setUserActivity(ua);
        } else {
          setUserActivity([]);
        }
      } catch (e) {
        console.warn('user-activity fetch failed', e);
      }
    };
    fetchAnalytics().catch(console.error);
  }, [token]);

  // Simple relationship graph layout: columns for AssetType -> Schema -> Metadata
  const relationGraph = useMemo(() => {
    // Build unique asset type nodes from schemas and records
    const assetTypes = new Map<number | 'none', { id: string; label: string; col: number }>();
    const schemaNodes = new Map<number, { id: string; label: string; col: number; asset_type_id?: number }>();
    const recordNodes = new Map<number, { id: string; label: string; col: number; schema_id?: number }>();

    schemas.forEach((s) => {
      schemaNodes.set(s.id, { id: `S${s.id}`, label: `${s.name} v${s.version}`, col: 1, asset_type_id: s.asset_type_id });
      const k = (s.asset_type_id ?? -1) as number | 'none';
      if (!assetTypes.has(k)) {
        assetTypes.set(k, { id: `A${k}`, label: s.asset_type_id ? `AssetType #${s.asset_type_id}` : 'Unassigned', col: 0 });
      }
    });
    records.slice(0, 30).forEach((r) => {
      recordNodes.set(r.id, { id: `M${r.id}`, label: r.name || `Record #${r.id}`, col: 2, schema_id: r.schema_id });
    });

    // layout positions
    const rowsA = Array.from(assetTypes.values());
    const rowsS = Array.from(schemaNodes.values());
    const rowsM = Array.from(recordNodes.values());
    const colX = [50, 360, 670];
    const vGap = 50;
    const nodes = [
      ...rowsA.map((n, i) => ({ ...n, x: colX[0], y: 40 + i * vGap })),
      ...rowsS.map((n, i) => ({ ...n, x: colX[1], y: 40 + i * vGap })),
      ...rowsM.map((n, i) => ({ ...n, x: colX[2], y: 40 + i * vGap })),
    ];

    const find = (id: string) => nodes.find((n) => n.id === id)!;
    const links: { from: string; to: string; color: string }[] = [];
    schemaNodes.forEach((s) => {
      const atKey = (s.asset_type_id ?? -1) as number | 'none';
      const a = assetTypes.get(atKey);
      if (a) links.push({ from: a.id, to: s.id, color: '#94A3B8' });
    });
    recordNodes.forEach((m) => {
      if (m.schema_id && schemaNodes.has(m.schema_id)) links.push({ from: `S${m.schema_id}`, to: m.id, color: '#6366F1' });
    });

    return { nodes, links, width: 760, height: Math.max(nodes.length * 22 + 80, 260) };
  }, [schemas, records]);

  const [flowMode, setFlowMode] = useState<'assign' | 'auto'>('assign');

  return (
    <Box>
      <Typography variant="h4" sx={{ fontWeight: 700, mb: 3 }}>Analytics</Typography>

      <Grid container spacing={3}>
        {/* Stat cards */}
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="overline" color="text.secondary">Total Records</Typography>
              <Typography variant="h4" sx={{ fontWeight: 700 }}>{stats?.total_metadata_records ?? 0}</Typography>
              <Typography variant="body2" color="text.secondary">Last 7d: {stats?.recent_records_7days ?? 0}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card><CardContent>
            <Typography variant="overline" color="text.secondary">Schemas</Typography>
            <Typography variant="h4" sx={{ fontWeight: 700 }}>{stats?.total_schemas ?? 0}</Typography>
          </CardContent></Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card><CardContent>
            <Typography variant="overline" color="text.secondary">Asset Types</Typography>
            <Typography variant="h4" sx={{ fontWeight: 700 }}>{stats?.total_asset_types ?? 0}</Typography>
          </CardContent></Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card><CardContent>
            <Typography variant="overline" color="text.secondary">Users</Typography>
            <Typography variant="h4" sx={{ fontWeight: 700 }}>{stats?.total_users ?? (user ? 1 : 0)}</Typography>
          </CardContent></Card>
        </Grid>

        {/* Timeline */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardHeader title="Metadata Created (Last 30 days)" />
            <CardContent sx={{ height: 300 }}>
              {timeline.length === 0 ? (
                <Box sx={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'text.secondary' }}>
                  No data yet
                </Box>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={timeline} margin={{ left: 8, right: 16, top: 8, bottom: 8 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                    <YAxis allowDecimals={false} />
                    <Tooltip />
                    <Line type="monotone" dataKey="records" stroke="#6366F1" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* By asset type */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardHeader title="By Asset Type" />
            <CardContent sx={{ height: 300 }}>
              {byAssetType.length === 0 ? (
                <Box sx={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'text.secondary' }}>
                  No data yet
                </Box>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={byAssetType} dataKey="value" nameKey="name" outerRadius={90}>
                      {byAssetType.map((_, i) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Top asset types */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader title="Top Asset Types" />
            <CardContent sx={{ height: 280 }}>
              {topTypes.length === 0 ? (
                <Box sx={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'text.secondary' }}>
                  No data yet
                </Box>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={topTypes}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis allowDecimals={false} />
                    <Tooltip />
                    <Bar dataKey="count" fill="#10B981" />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Recent activity */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader title="Recent Activity" />
            <CardContent sx={{ maxHeight: 280, overflow: 'auto' }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Change</TableCell>
                    <TableCell>Schema</TableCell>
                    <TableCell>By</TableCell>
                    <TableCell align="right">When</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {recent.map((r) => (
                    <TableRow key={r.id} hover>
                      <TableCell>{r.change_type}</TableCell>
                      <TableCell>{r.schema_id ? `#${r.schema_id} v${r.schema_version ?? ''}` : '-'}</TableCell>
                      <TableCell>{r.changed_by_name ?? r.changed_by ?? '-'}</TableCell>
                      <TableCell align="right">{r.timestamp?.replace('T', ' ').slice(0, 19) ?? '-'}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </Grid>

        {/* Relationship graph */}
        <Grid item xs={12}>
          <Card>
            <CardHeader title="Relationships: Asset Types → Schemas → Metadata" />
            <CardContent>
              <Box sx={{ width: '100%', overflow: 'auto' }}>
                <svg width={relationGraph.width} height={relationGraph.height}>
                  {/* links */}
                  {relationGraph.links.map((l, i) => {
                    const from = relationGraph.nodes.find((n) => n.id === l.from)!;
                    const to = relationGraph.nodes.find((n) => n.id === l.to)!;
                    return (
                      <line key={i} x1={from.x + 90} y1={from.y + 14} x2={to.x} y2={to.y + 14} stroke={l.color} strokeWidth={1.5} />
                    );
                  })}
                  {/* nodes */}
                  {relationGraph.nodes.map((n) => (
                    <g key={n.id}>
                      <rect x={n.x} y={n.y} width={180} height={28} rx={6} fill="#0F172A" stroke="#1F2937" />
                      <text x={n.x + 10} y={n.y + 18} fontSize={12} fill="#E5E7EB">{n.label}</text>
                    </g>
                  ))}
                </svg>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Admin: user activity */}
        {user?.role === 'admin' && (
          <Grid item xs={12} md={6}>
            <Card>
              <CardHeader title="User Activity (admin)" />
              <CardContent sx={{ height: 280 }}>
                {userActivity.length === 0 ? (
                  <Box sx={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'text.secondary' }}>
                    No data yet
                  </Box>
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={userActivity}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="username" />
                      <YAxis allowDecimals={false} />
                      <Tooltip />
                      <Bar dataKey="count" fill="#6366F1" />
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Dynamic assignment/auto-create explainer */}
        <Grid item xs={12}>
          <Card>
            <CardHeader
              title="How new metadata assigns/creates schemas"
              action={
                <Stack direction="row" spacing={1}>
                  <Button size="small" variant={flowMode === 'assign' ? 'contained' : 'outlined'} onClick={() => setFlowMode('assign')}>Assign Existing</Button>
                  <Button size="small" variant={flowMode === 'auto' ? 'contained' : 'outlined'} onClick={() => setFlowMode('auto')}>Auto-Create</Button>
                </Stack>
              }
            />
            <CardContent>
              {flowMode === 'assign' ? (
                <Stack spacing={1}>
                  <Typography variant="body2">1. User submits metadata with values (e.g., title, width, height)</Typography>
                  <Typography variant="body2">2. Backend compares incoming keys to existing schemas (overlap score)</Typography>
                  <Typography variant="body2">3. If a best match exists, the record is linked to that schema</Typography>
                  <Typography variant="body2">4. Values are validated and stored against defined fields</Typography>
                </Stack>
              ) : (
                <Stack spacing={1}>
                  <Typography variant="body2">1. No existing schema sufficiently matches the incoming values</Typography>
                  <Typography variant="body2">2. If allowed and asset type is provided, a new schema is created from the values</Typography>
                  <Typography variant="body2">3. The record links to this new schema; fields can be refined later</Typography>
                  <Typography variant="body2">4. This mirrors your current auto-create behavior when submitting metadata</Typography>
                </Stack>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};
