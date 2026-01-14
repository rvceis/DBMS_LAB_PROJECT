import { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  Stack,
  Checkbox,
  FormControlLabel,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  CircularProgress,
  Chip,
} from '@mui/material';
import { Download, FileText, FileType } from 'lucide-react';
import { useMetadataStore } from '@/stores/metadataStore';
import { useReportStore } from '@/stores/reportStore';
import toast from 'react-hot-toast';

export const RecordReport = () => {
  const { records, fetchRecords, loading } = useMetadataStore();
  const { downloadReport } = useReportStore();
  const [selectedRecords, setSelectedRecords] = useState<Set<number>>(new Set());
  const [reportName, setReportName] = useState('Records Report');
  const [generating, setGenerating] = useState(false);
  const [format, setFormat] = useState<'csv' | 'pdf'>('pdf');

  useEffect(() => {
    fetchRecords({ limit: 1000 });
  }, []);

  const handleSelectRecord = (recordId: number) => {
    const newSelection = new Set(selectedRecords);
    if (newSelection.has(recordId)) {
      newSelection.delete(recordId);
    } else {
      newSelection.add(recordId);
    }
    setSelectedRecords(newSelection);
  };

  const handleSelectAll = () => {
    if (selectedRecords.size === records.length) {
      setSelectedRecords(new Set());
    } else {
      setSelectedRecords(new Set(records.map((r) => r.id)));
    }
  };

  const handleGenerateReport = async () => {
    if (selectedRecords.size === 0) {
      toast.error('Please select at least one record');
      return;
    }

    setGenerating(true);
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Not authenticated');
      }

      const response = await fetch('/api/reports/generate/records', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          record_ids: Array.from(selectedRecords),
          format,
          name: reportName || 'Records Report',
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to generate report');
      }

      const execution = await response.json();
      toast.success('Report generated!');

      // Download the report
      await downloadReport(execution.id);
    } catch (error: any) {
      toast.error(error.message || 'Failed to generate report');
      console.error(error);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <Box>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
          Generate Report from Records
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Select multiple metadata records to generate a combined PDF/CSV report. Records with different schemas will have separate tables.
        </Typography>
      </Box>

      {/* Report Settings */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Stack spacing={2}>
            <TextField
              label="Report Name"
              value={reportName}
              onChange={(e) => setReportName(e.target.value)}
              fullWidth
              placeholder="Records Report"
            />

            <Box sx={{ display: 'flex', gap: 2 }}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={format === 'pdf'}
                    onChange={() => setFormat('pdf')}
                  />
                }
                label="PDF Format"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={format === 'csv'}
                    onChange={() => setFormat('csv')}
                  />
                }
                label="CSV Format"
              />
            </Box>

            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button
                variant="contained"
                startIcon={<FileText size={20} />}
                onClick={handleGenerateReport}
                disabled={selectedRecords.size === 0 || generating}
              >
                {generating ? 'Generating...' : 'Generate Report'}
              </Button>
              <Typography variant="body2" color="text.secondary" sx={{ alignSelf: 'center' }}>
                {selectedRecords.size} record{selectedRecords.size !== 1 ? 's' : ''} selected
              </Typography>
            </Box>
          </Stack>
        </CardContent>
      </Card>

      {/* Records Selection */}
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      ) : records.length === 0 ? (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 4 }}>
            <Typography color="text.secondary">No metadata records found</Typography>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow sx={{ backgroundColor: 'action.hover' }}>
                    <TableCell>
                      <Checkbox
                        checked={selectedRecords.size === records.length}
                        indeterminate={selectedRecords.size > 0 && selectedRecords.size < records.length}
                        onChange={handleSelectAll}
                      />
                    </TableCell>
                    <TableCell>Name</TableCell>
                    <TableCell>Asset Type</TableCell>
                    <TableCell>Schema</TableCell>
                    <TableCell>Created</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {records.map((record) => (
                    <TableRow key={record.id} hover>
                      <TableCell>
                        <Checkbox
                          checked={selectedRecords.has(record.id)}
                          onChange={() => handleSelectRecord(record.id)}
                        />
                      </TableCell>
                      <TableCell sx={{ fontWeight: 500 }}>{record.name}</TableCell>
                      <TableCell>
                        <Chip label={record.asset_type_name || 'Unknown'} size="small" variant="outlined" />
                      </TableCell>
                      <TableCell>
                        <Chip label={`Schema #${record.schema_id}`} size="small" variant="outlined" />
                      </TableCell>
                      <TableCell>{new Date(record.created_at).toLocaleDateString()}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};
