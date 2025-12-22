import { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Box,
  Typography,
  Stepper,
  Step,
  StepLabel,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  Stack,
  Chip,
  Paper,
  IconButton,
} from '@mui/material';
import { Upload, FileText, Check, X, RefreshCw } from 'lucide-react';
import toast from 'react-hot-toast';

interface DataImportDialogProps {
  open: boolean;
  onClose: () => void;
  schemaId: number;
  onSuccess: () => void;
}

export const DataImportDialog = ({ open, onClose, schemaId, onSuccess }: DataImportDialogProps) => {
  const [activeStep, setActiveStep] = useState(0);
  const [rawData, setRawData] = useState('');
  const [format, setFormat] = useState('auto');
  const [preview, setPreview] = useState<any[]>([]);
  const [dataFields, setDataFields] = useState<string[]>([]);
  const [schemaFields, setSchemaFields] = useState<string[]>([]);
  const [fieldMapping, setFieldMapping] = useState<Record<string, string>>({});
  const [formatDetected, setFormatDetected] = useState('');
  const [loading, setLoading] = useState(false);
  const [importing, setImporting] = useState(false);

  const steps = ['Paste/Upload Data', 'Review & Map Fields', 'Import'];

  const handleParse = async () => {
    if (!rawData.trim()) {
      toast.error('Please enter some data');
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/uploads/parse', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          content: rawData,
          schema_id: schemaId,
          format,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Parse failed');
      }

      const result = await response.json();
      setPreview(result.preview || []);
      setDataFields(result.data_fields || []);
      setSchemaFields(result.schema_fields || []);
      setFieldMapping(result.suggested_mapping || {});
      setFormatDetected(result.format_detected);

      toast.success(`Detected ${result.format_detected} format - ${result.record_count} records`);
      setActiveStep(1);
    } catch (error: any) {
      toast.error(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleImport = async () => {
    setImporting(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/uploads/import', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          content: rawData,
          schema_id: schemaId,
          format,
          field_mapping: fieldMapping,
          skip_validation: false,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        if (error.validation_errors) {
          toast.error(`Validation failed: ${error.validation_errors.slice(0, 3).join(', ')}`);
        } else {
          throw new Error(error.error || 'Import failed');
        }
        return;
      }

      const result = await response.json();
      toast.success(`Imported ${result.created_count} records successfully!`);
      
      if (result.failed_count > 0) {
        toast.error(`${result.failed_count} records failed`);
      }

      onSuccess();
      handleClose();
    } catch (error: any) {
      toast.error(error.message);
    } finally {
      setImporting(false);
    }
  };

  const handleClose = () => {
    setActiveStep(0);
    setRawData('');
    setPreview([]);
    setFieldMapping({});
    onClose();
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const content = event.target?.result as string;
      setRawData(content);
      
      // Auto-detect format from file extension
      const ext = file.name.split('.').pop()?.toLowerCase();
      if (ext === 'json') setFormat('json');
      else if (ext === 'csv') setFormat('csv');
      else if (ext === 'tsv' || ext === 'txt') setFormat('tsv');
      else setFormat('auto');
    };
    reader.readAsText(file);
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="lg" fullWidth>
      <DialogTitle>Import Data</DialogTitle>
      <DialogContent>
        <Stepper activeStep={activeStep} sx={{ mb: 3, mt: 2 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        {activeStep === 0 && (
          <Stack spacing={3}>
            <Alert severity="info">
              <Typography variant="body2">
                Paste or upload data in any format: JSON, CSV, TSV, Key-Value pairs, or plain text.
                We'll auto-detect the format and map fields to your schema.
              </Typography>
            </Alert>

            <Box>
              <input
                type="file"
                accept=".json,.csv,.tsv,.txt"
                onChange={handleFileUpload}
                style={{ display: 'none' }}
                id="file-upload"
              />
              <label htmlFor="file-upload">
                <Button variant="outlined" component="span" startIcon={<Upload size={16} />}>
                  Upload File
                </Button>
              </label>
            </Box>

            <TextField
              label="Or Paste Data Here"
              multiline
              rows={12}
              value={rawData}
              onChange={(e) => setRawData(e.target.value)}
              fullWidth
              placeholder={`Examples:

JSON:
[{"name": "John", "age": 30}, {"name": "Jane", "age": 25}]

CSV:
name,age,email
John,30,john@example.com
Jane,25,jane@example.com

Key-Value:
name: John
age: 30
---
name: Jane
age: 25`}
            />

            <FormControl fullWidth>
              <InputLabel>Format Hint</InputLabel>
              <Select value={format} label="Format Hint" onChange={(e) => setFormat(e.target.value)}>
                <MenuItem value="auto">Auto-detect</MenuItem>
                <MenuItem value="json">JSON</MenuItem>
                <MenuItem value="csv">CSV (comma-separated)</MenuItem>
                <MenuItem value="tsv">TSV (tab-separated)</MenuItem>
                <MenuItem value="pipe">Pipe-separated (|)</MenuItem>
                <MenuItem value="semicolon">Semicolon-separated (;)</MenuItem>
                <MenuItem value="keyvalue">Key-Value pairs</MenuItem>
              </Select>
            </FormControl>
          </Stack>
        )}

        {activeStep === 1 && (
          <Stack spacing={3}>
            <Alert severity="success">
              <Typography variant="body2">
                Detected <strong>{formatDetected}</strong> format with {preview.length} records (showing preview)
              </Typography>
            </Alert>

            <Box>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Field Mapping
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Map your data fields to schema fields. Auto-detected mappings shown below.
              </Typography>

              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Data Field</TableCell>
                    <TableCell>→</TableCell>
                    <TableCell>Schema Field</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {dataFields.map((dataField) => (
                    <TableRow key={dataField}>
                      <TableCell>
                        <Chip label={dataField} size="small" />
                      </TableCell>
                      <TableCell>→</TableCell>
                      <TableCell>
                        <FormControl fullWidth size="small">
                          <Select
                            value={fieldMapping[dataField] || ''}
                            onChange={(e) =>
                              setFieldMapping({ ...fieldMapping, [dataField]: e.target.value })
                            }
                          >
                            <MenuItem value="">
                              <em>Skip this field</em>
                            </MenuItem>
                            {schemaFields.map((schemaField) => (
                              <MenuItem key={schemaField} value={schemaField}>
                                {schemaField}
                              </MenuItem>
                            ))}
                          </Select>
                        </FormControl>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Box>

            <Box>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Data Preview (first 10 records)
              </Typography>
              <Paper variant="outlined" sx={{ maxHeight: 300, overflow: 'auto' }}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      {dataFields.map((field) => (
                        <TableCell key={field}>{field}</TableCell>
                      ))}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {preview.map((row, idx) => (
                      <TableRow key={idx}>
                        {dataFields.map((field) => (
                          <TableCell key={field}>{String(row[field] || '')}</TableCell>
                        ))}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </Paper>
            </Box>
          </Stack>
        )}

        {activeStep === 2 && (
          <Stack spacing={2} alignItems="center" sx={{ py: 4 }}>
            <Check size={64} color="green" />
            <Typography variant="h6">Ready to Import</Typography>
            <Typography color="text.secondary">
              Click "Import" to create {preview.length}+ metadata records
            </Typography>
          </Stack>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={handleClose} disabled={loading || importing}>
          Cancel
        </Button>

        {activeStep > 0 && (
          <Button onClick={() => setActiveStep(activeStep - 1)} disabled={loading || importing}>
            Back
          </Button>
        )}

        {activeStep === 0 && (
          <Button variant="contained" onClick={handleParse} disabled={loading || !rawData.trim()}>
            {loading ? 'Parsing...' : 'Parse Data'}
          </Button>
        )}

        {activeStep === 1 && (
          <Button variant="contained" onClick={() => setActiveStep(2)}>
            Next
          </Button>
        )}

        {activeStep === 2 && (
          <Button variant="contained" onClick={handleImport} disabled={importing}>
            {importing ? 'Importing...' : 'Import'}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};
