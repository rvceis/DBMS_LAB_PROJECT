import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  LinearProgress,
  Paper,
  Stack,
  Avatar,
} from '@mui/material';
import { useEffect, useState } from 'react';
import { useSchemaStore } from '@/stores/schemaStore';
import { useMetadataStore } from '@/stores/metadataStore';
import { useAssetTypesStore } from '@/stores/assetTypesStore';
import { TrendingUp, Database, FileText, Users, Activity, ArrowUp } from 'lucide-react';

export const Dashboard = () => {
  const { schemas, fetchSchemas } = useSchemaStore();
  const { records, fetchRecords } = useMetadataStore();
  const { assetTypes, fetchAssetTypes } = useAssetTypesStore();
  const [stats, setStats] = useState({
    totalSchemas: 0,
    totalRecords: 0,
    activeSchemas: 0,
    assetTypes: 0,
  });
  const [recordsByType, setRecordsByType] = useState<any[]>([]);

  useEffect(() => {
    fetchSchemas();
    fetchRecords({ limit: 100 });
    fetchAssetTypes();
  }, []);

  useEffect(() => {
    const activeCount = schemas.filter((s) => s.is_active !== false).length;
    setStats({
      totalSchemas: schemas.length,
      totalRecords: records.length,
      activeSchemas: activeCount,
      assetTypes: assetTypes.length,
    });

    // Group records by asset type
    const grouped = assetTypes.map((at) => ({
      name: at.name,
      count: records.filter((r) => r.asset_type_id === at.id).length,
      percentage: records.length > 0 ? ((records.filter((r) => r.asset_type_id === at.id).length / records.length) * 100).toFixed(1) : 0,
    })).filter((item) => item.count > 0);
    setRecordsByType(grouped);
  }, [schemas, records, assetTypes]);

  const StatCard = ({ icon: Icon, label, value, trend, color }: any) => (
    <Card sx={{ height: '100%', background: `linear-gradient(135deg, ${color}15 0%, ${color}05 100%)`, border: `1px solid ${color}30` }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Box sx={{ flex: 1 }}>
            <Typography color="textSecondary" gutterBottom variant="body2" sx={{ fontWeight: 500 }}>
              {label}
            </Typography>
            <Typography variant="h3" sx={{ fontWeight: 700, my: 1 }}>
              {value}
            </Typography>
            {trend && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <ArrowUp size={14} style={{ color: '#10B981' }} />
                <Typography variant="caption" sx={{ color: 'success.main', fontWeight: 600 }}>
                  {trend}
                </Typography>
              </Box>
            )}
          </Box>
          <Avatar sx={{ bgcolor: color, width: 56, height: 56 }}>
            <Icon size={28} />
          </Avatar>
        </Box>
      </CardContent>
    </Card>
  );

  return (
    <Box>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
          Dashboard Overview
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Welcome back! Here's what's happening with your metadata today.
        </Typography>
      </Box>

      {/* Stats Row */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            icon={Database}
            label="Total Schemas"
            value={stats.totalSchemas}
            trend={`${stats.activeSchemas} active`}
            color="#6366F1"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            icon={FileText}
            label="Metadata Records"
            value={stats.totalRecords}
            trend="All time"
            color="#EC4899"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            icon={Activity}
            label="Asset Types"
            value={stats.assetTypes}
            trend="Categories"
            color="#10B981"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            icon={TrendingUp}
            label="Storage Used"
            value={`${(stats.totalRecords * 0.5).toFixed(1)} MB`}
            trend="Estimated"
            color="#F59E0B"
          />
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Records by Asset Type */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
                Records by Asset Type
              </Typography>
              {recordsByType.length === 0 ? (
                <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
                  No records yet. Upload some files to get started!
                </Typography>
              ) : (
                <Stack spacing={2.5}>
                  {recordsByType.map((item, idx) => (
                    <Box key={idx}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {item.name}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {item.count} records ({item.percentage}%)
                        </Typography>
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={parseFloat(item.percentage)}
                        sx={{
                          height: 8,
                          borderRadius: 4,
                          bgcolor: 'action.hover',
                          '& .MuiLinearProgress-bar': {
                            borderRadius: 4,
                            bgcolor: ['#6366F1', '#EC4899', '#10B981', '#F59E0B', '#8B5CF6'][idx % 5],
                          },
                        }}
                      />
                    </Box>
                  ))}
                </Stack>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Records Table */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
                Recent Activity
              </Typography>
              {records.length === 0 ? (
                <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
                  No recent activity
                </Typography>
              ) : (
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell sx={{ fontWeight: 600 }}>Name</TableCell>
                        <TableCell sx={{ fontWeight: 600 }}>Type</TableCell>
                        <TableCell sx={{ fontWeight: 600 }}>Date</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {records.slice(0, 6).map((record) => (
                        <TableRow key={record.id} hover>
                          <TableCell>
                            <Typography variant="body2" sx={{ fontWeight: 500 }}>
                              {record.name}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={record.asset_type_name || 'Unknown'}
                              size="small"
                              variant="outlined"
                              sx={{ fontSize: '0.7rem' }}
                            />
                          </TableCell>
                          <TableCell>
                            <Typography variant="caption" color="text.secondary">
                              {new Date(record.created_at).toLocaleDateString('en-US', {
                                month: 'short',
                                day: 'numeric',
                              })}
                            </Typography>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};
