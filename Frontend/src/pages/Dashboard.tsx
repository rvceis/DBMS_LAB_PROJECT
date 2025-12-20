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
} from '@mui/material';
import { useEffect, useState } from 'react';
import { useSchemaStore } from '@/stores/schemaStore';
import { useMetadataStore } from '@/stores/metadataStore';
import { TrendingUp, Database, FileText, Users } from 'lucide-react';

export const Dashboard = () => {
  const { schemas, fetchSchemas } = useSchemaStore();
  const { records, fetchRecords } = useMetadataStore();
  const [stats, setStats] = useState({
    totalSchemas: 0,
    totalRecords: 0,
    activeUsers: 0,
    changesThisWeek: 0,
  });

  useEffect(() => {
    fetchSchemas();
    fetchRecords({ limit: 10 });
  }, []);

  useEffect(() => {
    setStats({
      totalSchemas: schemas.length,
      totalRecords: records.length,
      activeUsers: 5, // Mock data
      changesThisWeek: 12, // Mock data
    });
  }, [schemas, records]);

  const StatCard = ({ icon: Icon, label, value, trend }: any) => (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Box>
            <Typography color="textSecondary" gutterBottom>
              {label}
            </Typography>
            <Typography variant="h4" sx={{ fontWeight: 700 }}>
              {value}
            </Typography>
            {trend && (
              <Typography variant="body2" sx={{ color: 'success.main', mt: 1 }}>
                <TrendingUp size={16} style={{ display: 'inline', marginRight: 4 }} />
                {trend}
              </Typography>
            )}
          </Box>
          <Icon size={32} style={{ color: '#6366F1' }} />
        </Box>
      </CardContent>
    </Card>
  );

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 4, fontWeight: 700 }}>
        Dashboard
      </Typography>

      {/* Stats Row */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard icon={Database} label="Total Schemas" value={stats.totalSchemas} trend="+2 this week" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard icon={FileText} label="Metadata Records" value={stats.totalRecords} trend="+45 today" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard icon={Users} label="Active Users" value={stats.activeUsers} trend="+1 this week" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard icon={Database} label="Changes Today" value={stats.changesThisWeek} />
        </Grid>
      </Grid>

      {/* Recent Records Table */}
      <Card>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
            Recent Metadata Records
          </Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow sx={{ backgroundColor: 'action.hover' }}>
                  <TableCell>Name</TableCell>
                  <TableCell>Schema</TableCell>
                  <TableCell>Created By</TableCell>
                  <TableCell>Created At</TableCell>
                  <TableCell>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {records.slice(0, 5).map((record) => (
                  <TableRow key={record.id} hover>
                    <TableCell>{record.name}</TableCell>
                    <TableCell>Schema #{record.schema_id}</TableCell>
                    <TableCell>{record.created_by_name || 'Unknown'}</TableCell>
                    <TableCell>{new Date(record.created_at).toLocaleDateString()}</TableCell>
                    <TableCell>
                      <Chip label="Active" size="small" color="success" variant="outlined" />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    </Box>
  );
};
