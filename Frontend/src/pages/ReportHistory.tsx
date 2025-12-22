import { useEffect, useState } from 'react';
import {
  Box,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  Typography,
  Chip,
  IconButton,
  CircularProgress,
  Stack,
  Button,
} from '@mui/material';
import { Download, Trash2, RefreshCw } from 'lucide-react';
import { useReportStore } from '@/stores/reportStore';
import toast from 'react-hot-toast';

export const ReportHistory = () => {
  const { executions, fetchExecutions, downloadReport, deleteExecution, loading } = useReportStore();

  useEffect(() => {
    fetchExecutions();
    const interval = setInterval(() => {
      fetchExecutions(); // Auto-refresh for running reports
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleDownload = async (id: number) => {
    try {
      await downloadReport(id);
      toast.success('Download started');
    } catch (error) {
      toast.error('Failed to download report');
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Delete this execution?')) return;
    try {
      await deleteExecution(id);
      toast.success('Execution deleted');
    } catch (error) {
      toast.error('Failed to delete');
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString();
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700 }}>
          Report History
        </Typography>
        <Button
          startIcon={<RefreshCw size={20} />}
          onClick={() => fetchExecutions()}
          disabled={loading}
        >
          Refresh
        </Button>
      </Box>

      {loading && executions.length === 0 ? (
        <Typography>Loading history...</Typography>
      ) : executions.length === 0 ? (
        <Typography color="text.secondary">No reports generated yet</Typography>
      ) : (
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Report Name</TableCell>
              <TableCell>Format</TableCell>
              <TableCell>Started</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Records</TableCell>
              <TableCell align="right">Size</TableCell>
              <TableCell>Time</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {executions.map((exec) => (
              <TableRow key={exec.id} hover>
                <TableCell>{exec.template_name || 'Ad-hoc'}</TableCell>
                <TableCell>
                  <Chip label={exec.format.toUpperCase()} size="small" />
                </TableCell>
                <TableCell>{formatDate(exec.started_at)}</TableCell>
                <TableCell>
                  {exec.status === 'completed' ? (
                    <Chip label="Completed" color="success" size="small" />
                  ) : exec.status === 'failed' ? (
                    <Chip label="Failed" color="error" size="small" />
                  ) : exec.status === 'running' ? (
                    <Stack direction="row" spacing={1} alignItems="center">
                      <CircularProgress size={16} />
                      <Typography variant="caption">Running...</Typography>
                    </Stack>
                  ) : (
                    <Chip label={exec.status} size="small" />
                  )}
                </TableCell>
                <TableCell align="right">{exec.row_count?.toLocaleString() || '-'}</TableCell>
                <TableCell align="right">
                  {exec.file_size ? formatFileSize(exec.file_size) : '-'}
                </TableCell>
                <TableCell>
                  {exec.execution_time_ms ? `${(exec.execution_time_ms / 1000).toFixed(2)}s` : '-'}
                </TableCell>
                <TableCell align="right">
                  <Stack direction="row" spacing={1} justifyContent="flex-end">
                    {exec.status === 'completed' && (
                      <IconButton size="small" onClick={() => handleDownload(exec.id)}>
                        <Download size={16} />
                      </IconButton>
                    )}
                    <IconButton size="small" onClick={() => handleDelete(exec.id)}>
                      <Trash2 size={16} />
                    </IconButton>
                  </Stack>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </Box>
  );
};
