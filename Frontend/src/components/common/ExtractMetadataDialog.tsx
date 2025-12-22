import { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
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
  Alert,
  Stack,
  Chip,
  Paper,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import { Upload, Check, AlertCircle, ChevronRight } from 'lucide-react';
import toast from 'react-hot-toast';
import { useAssetTypesStore } from '@/stores/assetTypesStore';

interface ExtractMetadataDialogProps {
  open: boolean;
  onClose: () => void;
  onSuccess: (schemaId: number) => void;
}

export const ExtractMetadataDialog = ({ open, onClose, onSuccess }: ExtractMetadataDialogProps) => {
  const [activeStep, setActiveStep] = useState(0);
  const [file, setFile] = useState<File | null>(null);
  const [assetTypeId, setAssetTypeId] = useState<string>('');
  const [metadata, setMetadata] = useState<any>({});
  const [suggestedFields, setSuggestedFields] = useState<any[]>([]);
  const [schemaName, setSchemaName] = useState('');
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [createRecord, setCreateRecord] = useState(true);

  const { assetTypes } = useAssetTypesStore();

  const steps = ['Upload File', 'Review Metadata', 'Create Schema'];

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
    }
  };

  const handleExtract = async () => {
    if (!file || !assetTypeId) {
      toast.error('Please select a file and asset type');
      return;
    }

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('asset_type_id', assetTypeId);

      const token = localStorage.getItem('token');
      const response = await fetch('/api/uploads/extract-metadata', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Extraction failed');
      }

      const result = await response.json();
      setMetadata(result.metadata);
      setSuggestedFields(result.suggested_fields);
      setSchemaName(result.schema_name);
      toast.success('Metadata extracted successfully!');
      setActiveStep(1);
    } catch (error: any) {
      toast.error(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSchema = async () => {
    if (!schemaName) {
      toast.error('Please enter a schema name');
      return;
    }

    setCreating(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/uploads/create-schema-from-metadata', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          asset_type_id: parseInt(assetTypeId),
          schema_name: schemaName,
          fields: suggestedFields,
          metadata,
          create_record: createRecord,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Schema creation failed');
      }

      const result = await response.json();
      toast.success(`Schema created with ${result.field_count} fields!`);
      if (result.record_id) {
        toast.success(`Metadata record also created!`);
      }
      onSuccess(result.schema_id);
      handleClose();
    } catch (error: any) {
      toast.error(error.message);
    } finally {
      setCreating(false);
    }
  };

  const handleClose = () => {
    setActiveStep(0);
    setFile(null);
    setAssetTypeId('');
    setMetadata({});
    setSuggestedFields([]);
    setSchemaName('');
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>Auto-Generate Schema from File</DialogTitle>
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
                Upload any file (image, video, PDF, JSON, CSV, etc.) and we'll automatically extract metadata
                and generate a schema with appropriate field types.
              </Typography>
            </Alert>

            <FormControl fullWidth required>
              <InputLabel>Asset Type</InputLabel>
              <Select value={assetTypeId} label="Asset Type" onChange={(e) => setAssetTypeId(e.target.value)}>
                <MenuItem value="">
                  <em>Select Asset Type</em>
                </MenuItem>
                {assetTypes.map((at) => (
                  <MenuItem key={at.id} value={at.id}>
                    {at.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <Box>
              <input
                type="file"
                onChange={handleFileChange}
                style={{ display: 'none' }}
                id="metadata-file-upload"
              />
              <label htmlFor="metadata-file-upload">
                <Button variant="outlined" component="span" startIcon={<Upload size={16} />}>
                  Select File
                </Button>
              </label>
              {file && (
                <Typography variant="body2" sx={{ mt: 1 }}>
                  Selected: <strong>{file.name}</strong> ({(file.size / 1024).toFixed(2)} KB)
                </Typography>
              )}
            </Box>

            <Typography variant="caption" color="text.secondary">
              Supported: Images (PNG, JPG, GIF), Videos (MP4, MOV), Documents (PDF), Data (JSON, CSV, TSV), Text
            </Typography>
          </Stack>
        )}

        {activeStep === 1 && (
          <Stack spacing={3}>
            <Alert severity="success">
              <Typography variant="body2">
                Metadata extracted from <strong>{metadata.filename}</strong>
              </Typography>
            </Alert>

            <TextField
              label="Schema Name"
              value={schemaName}
              onChange={(e) => setSchemaName(e.target.value)}
              fullWidth
              placeholder="e.g., Image Metadata, Video Details, etc."
            />

            <Box>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Extracted Metadata
              </Typography>
              <Paper variant="outlined" sx={{ p: 2, maxHeight: 200, overflow: 'auto' }}>
                <Stack spacing={1}>
                  {Object.entries(metadata).map(([key, value]) => (
                    <Box key={key} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <Typography variant="body2" sx={{ fontWeight: 500 }}>
                        {key}:
                      </Typography>
                      <Typography variant="caption" color="text.secondary" sx={{ maxWidth: '60%', textAlign: 'right' }}>
                        {typeof value === 'object' ? JSON.stringify(value).substring(0, 100) : String(value).substring(0, 100)}
                      </Typography>
                    </Box>
                  ))}
                </Stack>
              </Paper>
            </Box>

            <Box>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Auto-Generated Schema Fields ({suggestedFields.length})
              </Typography>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Field Name</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell align="center">Required</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {suggestedFields.map((field, idx) => (
                    <TableRow key={idx}>
                      <TableCell>{field.field_name}</TableCell>
                      <TableCell>
                        <Chip label={field.field_type} size="small" variant="outlined" />
                      </TableCell>
                      <TableCell align="center">
                        {field.is_required ? <Check size={16} color="green" /> : <Typography variant="caption">-</Typography>}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Box>
          </Stack>
        )}

        {activeStep === 2 && (
          <Stack spacing={3} alignItems="center" sx={{ py: 4 }}>
            <Check size={64} color="green" />
            <Typography variant="h6">Ready to Create Schema</Typography>
            <Typography color="text.secondary" align="center">
              {suggestedFields.length} fields will be created from extracted metadata
            </Typography>
          </Stack>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={handleClose} disabled={loading || creating}>
          Cancel
        </Button>

        {activeStep > 0 && (
          <Button onClick={() => setActiveStep(activeStep - 1)} disabled={loading || creating}>
            Back
          </Button>
        )}

        {activeStep === 0 && (
          <Button variant="contained" onClick={handleExtract} disabled={loading || !file || !assetTypeId}>
            {loading ? 'Extracting...' : 'Extract Metadata'}
          </Button>
        )}

        {activeStep === 1 && (
          <Button variant="contained" onClick={() => setActiveStep(2)}>
            Next
          </Button>
        )}

        {activeStep === 2 && (
          <Button variant="contained" onClick={handleCreateSchema} disabled={creating}>
            {creating ? 'Creating...' : 'Create Schema'}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};
