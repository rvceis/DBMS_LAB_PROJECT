import { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  Stack,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Paper,
  Divider,
  Alert,
} from '@mui/material';
import { ArrowRight, RotateCcw, Plus, Minus, Edit2, AlertCircle } from 'lucide-react';
import toast from 'react-hot-toast';

interface SchemaVersion {
  id: number;
  name: string;
  version: number;
  asset_type_id: number;
  is_active: boolean;
  created_at: string;
  created_by_name: string;
  fields: any[];
  changes: any[];
}

interface ComparisonResult {
  schema1: SchemaVersion;
  schema2: SchemaVersion;
  comparison: {
    added_fields: any[];
    removed_fields: any[];
    modified_fields: any[];
    unchanged_fields: string[];
  };
  summary: {
    total_changes: number;
    additions: number;
    removals: number;
    modifications: number;
  };
}

interface SchemaComparisonProps {
  schemaId: number;
  schemaName: string;
  onClose: () => void;
}

export const SchemaComparison = ({ schemaId, schemaName, onClose }: SchemaComparisonProps) => {
  const [versions, setVersions] = useState<SchemaVersion[]>([]);
  const [selectedV1, setSelectedV1] = useState<number | ''>('');
  const [selectedV2, setSelectedV2] = useState<number | ''>('');
  const [comparison, setComparison] = useState<ComparisonResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [rollbackDialog, setRollbackDialog] = useState(false);
  const [rollbackTarget, setRollbackTarget] = useState<number | null>(null);

  useEffect(() => {
    fetchVersions();
  }, [schemaId]);

  const fetchVersions = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`/api/schemas/${schemaId}/versions`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error('Failed to fetch versions');
      const data = await res.json();
      setVersions(data);
      
      // Auto-select latest two versions if available
      if (data.length >= 2) {
        setSelectedV1(data[1].id);
        setSelectedV2(data[0].id);
      }
    } catch (e) {
      toast.error((e as Error).message);
    }
  };

  const compareVersions = async () => {
    if (!selectedV1 || !selectedV2) {
      toast.error('Please select two versions to compare');
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const res = await fetch('/api/schemas/compare', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ schema_id_1: selectedV1, schema_id_2: selectedV2 }),
      });
      if (!res.ok) throw new Error('Failed to compare schemas');
      const data = await res.json();
      setComparison(data);
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const handleRollback = async () => {
    if (!rollbackTarget) return;

    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`/api/schemas/${rollbackTarget}/rollback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error || 'Rollback failed');
      }
      const data = await res.json();
      toast.success(data.message);
      setRollbackDialog(false);
      fetchVersions();
      onClose();
    } catch (e) {
      toast.error((e as Error).message);
    }
  };

  useEffect(() => {
    if (selectedV1 && selectedV2) {
      compareVersions();
    }
  }, [selectedV1, selectedV2]);

  return (
    <Box sx={{ p: 3 }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 3 }}>
        <Typography variant="h5" sx={{ fontWeight: 700 }}>
          Schema Version Comparison: {schemaName}
        </Typography>
        <Button onClick={onClose}>Close</Button>
      </Stack>

      {/* Version Selection */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={3} alignItems="center">
            <Grid item xs={12} md={5}>
              <FormControl fullWidth>
                <InputLabel>Version 1 (Older)</InputLabel>
                <Select
                  value={selectedV1}
                  onChange={(e) => setSelectedV1(e.target.value as number)}
                  label="Version 1 (Older)"
                >
                  {versions.map((v) => (
                    <MenuItem key={v.id} value={v.id}>
                      v{v.version} - {new Date(v.created_at).toLocaleDateString()} by {v.created_by_name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={2} sx={{ display: 'flex', justifyContent: 'center' }}>
              <ArrowRight size={32} />
            </Grid>
            <Grid item xs={12} md={5}>
              <FormControl fullWidth>
                <InputLabel>Version 2 (Newer)</InputLabel>
                <Select
                  value={selectedV2}
                  onChange={(e) => setSelectedV2(e.target.value as number)}
                  label="Version 2 (Newer)"
                >
                  {versions.map((v) => (
                    <MenuItem key={v.id} value={v.id}>
                      v{v.version} - {new Date(v.created_at).toLocaleDateString()} by {v.created_by_name}
                      {v.is_active && <Chip label="Active" size="small" color="primary" sx={{ ml: 1 }} />}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Comparison Results */}
      {comparison && (
        <>
          {/* Summary */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Summary
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={6} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center', backgroundColor: 'success.light' }}>
                    <Typography variant="h4" sx={{ fontWeight: 700 }}>
                      {comparison.summary.additions}
                    </Typography>
                    <Typography variant="body2">Fields Added</Typography>
                  </Paper>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center', backgroundColor: 'error.light' }}>
                    <Typography variant="h4" sx={{ fontWeight: 700 }}>
                      {comparison.summary.removals}
                    </Typography>
                    <Typography variant="body2">Fields Removed</Typography>
                  </Paper>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center', backgroundColor: 'warning.light' }}>
                    <Typography variant="h4" sx={{ fontWeight: 700 }}>
                      {comparison.summary.modifications}
                    </Typography>
                    <Typography variant="body2">Fields Modified</Typography>
                  </Paper>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center', backgroundColor: 'info.light' }}>
                    <Typography variant="h4" sx={{ fontWeight: 700 }}>
                      {comparison.comparison.unchanged_fields.length}
                    </Typography>
                    <Typography variant="body2">Unchanged</Typography>
                  </Paper>
                </Grid>
              </Grid>
            </CardContent>
          </Card>

          {/* Detailed Changes */}
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Detailed Changes
              </Typography>

              {/* Added Fields */}
              {comparison.comparison.added_fields.length > 0 && (
                <Box sx={{ mb: 3 }}>
                  <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
                    <Plus size={20} color="#10B981" />
                    <Typography variant="subtitle1" sx={{ fontWeight: 600, color: 'success.main' }}>
                      Added Fields ({comparison.comparison.added_fields.length})
                    </Typography>
                  </Stack>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Field Name</TableCell>
                        <TableCell>Type</TableCell>
                        <TableCell>Required</TableCell>
                        <TableCell>Default</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {comparison.comparison.added_fields.map((field, idx) => (
                        <TableRow key={idx} sx={{ backgroundColor: 'success.light', opacity: 0.7 }}>
                          <TableCell sx={{ fontWeight: 600 }}>{field.field_name}</TableCell>
                          <TableCell><Chip label={field.field_type} size="small" /></TableCell>
                          <TableCell>{field.is_required ? 'Yes' : 'No'}</TableCell>
                          <TableCell>{field.default_value || '-'}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </Box>
              )}

              {/* Removed Fields */}
              {comparison.comparison.removed_fields.length > 0 && (
                <Box sx={{ mb: 3 }}>
                  <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
                    <Minus size={20} color="#EF4444" />
                    <Typography variant="subtitle1" sx={{ fontWeight: 600, color: 'error.main' }}>
                      Removed Fields ({comparison.comparison.removed_fields.length})
                    </Typography>
                  </Stack>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Field Name</TableCell>
                        <TableCell>Type</TableCell>
                        <TableCell>Required</TableCell>
                        <TableCell>Default</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {comparison.comparison.removed_fields.map((field, idx) => (
                        <TableRow key={idx} sx={{ backgroundColor: 'error.light', opacity: 0.7 }}>
                          <TableCell sx={{ fontWeight: 600, textDecoration: 'line-through' }}>
                            {field.field_name}
                          </TableCell>
                          <TableCell><Chip label={field.field_type} size="small" /></TableCell>
                          <TableCell>{field.is_required ? 'Yes' : 'No'}</TableCell>
                          <TableCell>{field.default_value || '-'}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </Box>
              )}

              {/* Modified Fields */}
              {comparison.comparison.modified_fields.length > 0 && (
                <Box sx={{ mb: 3 }}>
                  <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
                    <Edit2 size={20} color="#F59E0B" />
                    <Typography variant="subtitle1" sx={{ fontWeight: 600, color: 'warning.main' }}>
                      Modified Fields ({comparison.comparison.modified_fields.length})
                    </Typography>
                  </Stack>
                  {comparison.comparison.modified_fields.map((field, idx) => (
                    <Paper key={idx} sx={{ p: 2, mb: 2, backgroundColor: 'warning.light', opacity: 0.7 }}>
                      <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                        {field.field_name}
                      </Typography>
                      <Grid container spacing={2}>
                        <Grid item xs={6}>
                          <Typography variant="caption" color="text.secondary">
                            OLD
                          </Typography>
                          <Stack spacing={0.5}>
                            <Typography variant="body2">
                              Type: <Chip label={field.old.field_type} size="small" />
                            </Typography>
                            <Typography variant="body2">
                              Required: {field.old.is_required ? 'Yes' : 'No'}
                            </Typography>
                            <Typography variant="body2">
                              Default: {field.old.default_value || '-'}
                            </Typography>
                          </Stack>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="caption" color="text.secondary">
                            NEW
                          </Typography>
                          <Stack spacing={0.5}>
                            <Typography variant="body2">
                              Type: <Chip label={field.new.field_type} size="small" color="warning" />
                            </Typography>
                            <Typography variant="body2">
                              Required: {field.new.is_required ? 'Yes' : 'No'}
                            </Typography>
                            <Typography variant="body2">
                              Default: {field.new.default_value || '-'}
                            </Typography>
                          </Stack>
                        </Grid>
                      </Grid>
                    </Paper>
                  ))}
                </Box>
              )}

              {/* Rollback Action */}
              {selectedV1 && (
                <Box sx={{ mt: 3, pt: 3, borderTop: '1px solid', borderColor: 'divider' }}>
                  <Alert severity="info" icon={<AlertCircle size={20} />} sx={{ mb: 2 }}>
                    <Typography variant="body2">
                      You can rollback to version {versions.find((v) => v.id === selectedV1)?.version} structure.
                      This will create a new version with the old structure.
                    </Typography>
                  </Alert>
                  <Button
                    variant="outlined"
                    startIcon={<RotateCcw size={18} />}
                    onClick={() => {
                      setRollbackTarget(selectedV1 as number);
                      setRollbackDialog(true);
                    }}
                  >
                    Rollback to v{versions.find((v) => v.id === selectedV1)?.version}
                  </Button>
                </Box>
              )}
            </CardContent>
          </Card>
        </>
      )}

      {/* Rollback Confirmation Dialog */}
      <Dialog open={rollbackDialog} onClose={() => setRollbackDialog(false)}>
        <DialogTitle>Confirm Rollback</DialogTitle>
        <DialogContent>
          <Typography>
            This will create a new version with the structure from v
            {versions.find((v) => v.id === rollbackTarget)?.version}. The current active version will be
            deactivated. This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRollbackDialog(false)}>Cancel</Button>
          <Button variant="contained" color="warning" onClick={handleRollback}>
            Confirm Rollback
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
