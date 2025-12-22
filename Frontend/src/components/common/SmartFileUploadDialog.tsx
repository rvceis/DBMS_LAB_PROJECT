import { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  Alert,
  Stack,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  LinearProgress,
  Chip,
  RadioGroup,
  FormControlLabel,
  Radio,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  Paper,
} from '@mui/material';
import { Upload, FileUp, Check, AlertCircle } from 'lucide-react';
import toast from 'react-hot-toast';
import { useAssetTypesStore } from '@/stores/assetTypesStore';

interface SmartFileUploadDialogProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const SmartFileUploadDialog = ({ open, onClose, onSuccess }: SmartFileUploadDialogProps) => {
  const [step, setStep] = useState<'select' | 'suggest' | 'choose' | 'success'>('select');
  const [file, setFile] = useState<File | null>(null);
  const [assetTypeId, setAssetTypeId] = useState<string>('');
  const [recordName, setRecordName] = useState('');
  
  const [extracting, setExtracting] = useState(false);
  const [uploading, setUploading] = useState(false);
  
  const [metadata, setMetadata] = useState<any>({});
  const [suggestedFields, setSuggestedFields] = useState<any[]>([]);
  const [candidates, setCandidates] = useState<any[]>([]);
  
  const [chosenAction, setChosenAction] = useState<'use_existing' | 'create_new'>('use_existing');
  const [chosenSchemaId, setChosenSchemaId] = useState<string>('');
  const [newSchemaName, setNewSchemaName] = useState('');

  const { assetTypes } = useAssetTypesStore();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setRecordName(selectedFile.name.split('.')[0]);
    }
  };

  const handleSuggest = async () => {
    if (!file || !assetTypeId) {
      toast.error('Please select a file and asset type');
      return;
    }

    setExtracting(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('asset_type_id', assetTypeId);

      const token = localStorage.getItem('token');
      const response = await fetch('/api/uploads/smart-upload', {
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

      const data = await response.json();
      setMetadata(data.metadata);
      setSuggestedFields(data.suggested_fields);
      setCandidates(data.candidates || []);
      
      // Auto-select best match if available
      if (data.candidates && data.candidates.length > 0) {
        setChosenSchemaId(String(data.candidates[0].id));
      }
      
      toast.success('Metadata extracted! Choose a schema to continue.');
      setStep('choose');
    } catch (error: any) {
      toast.error(error.message);
    } finally {
      setExtracting(false);
    }
  };

  const handleCommit = async () => {
    if (!file || !assetTypeId) {
      toast.error('File or asset type missing');
      return;
    }

    if (chosenAction === 'use_existing' && !chosenSchemaId) {
      toast.error('Please select a schema');
      return;
    }

    if (chosenAction === 'create_new' && !newSchemaName) {
      toast.error('Please enter a schema name');
      return;
    }

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('asset_type_id', assetTypeId);
      formData.append('record_name', recordName || file.name);
      formData.append('action', chosenAction);
      
      if (chosenAction === 'use_existing') {
        formData.append('schema_id', chosenSchemaId);
      } else {
        formData.append('schema_name', newSchemaName);
      }

      const token = localStorage.getItem('token');
      const response = await fetch('/api/uploads/smart-upload', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Upload failed');
      }

      const result = await response.json();
      toast.success('File uploaded and record created!');
      setStep('success');
      
      setTimeout(() => {
        onSuccess();
        handleClose();
      }, 2000);
    } catch (error: any) {
      toast.error(error.message);
    } finally {
      setUploading(false);
    }
  };

  const handleClose = () => {
    setStep('select');
    setFile(null);
    setAssetTypeId('');
    setRecordName('');
    setMetadata({});
    setSuggestedFields([]);
    setCandidates([]);
    setChosenAction('use_existing');
    setChosenSchemaId('');
    setNewSchemaName('');
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <FileUp size={24} />
          Smart File Upload
        </Box>
      </DialogTitle>
      <DialogContent>
        <Stack spacing={3} sx={{ mt: 1 }}>
          {/* Step 1: Select File & Asset Type */}
          {step === 'select' && (
            <>
              <Alert severity="info">
                <Typography variant="body2">
                  Upload a file (image, video, document, dataset). We'll extract metadata and let you choose which schema to use.
                </Typography>
              </Alert>

              <FormControl fullWidth required>
                <InputLabel>Asset Type</InputLabel>
                <Select
                  value={assetTypeId}
                  label="Asset Type"
                  onChange={(e) => setAssetTypeId(e.target.value)}
                  disabled={extracting}
                >
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
                  id="smart-file-upload"
                  disabled={extracting}
                />
                <label htmlFor="smart-file-upload">
                  <Button
                    variant="outlined"
                    component="span"
                    startIcon={<Upload size={16} />}
                    fullWidth
                    disabled={extracting}
                  >
                    Select File
                  </Button>
                </label>
                {file && (
                  <Box sx={{ mt: 1, p: 2, bgcolor: 'action.hover', borderRadius: 1 }}>
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>
                      {file.name}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {(file.size / 1024).toFixed(2)} KB
                    </Typography>
                  </Box>
                )}
              </Box>

              <TextField
                label="Record Name (optional)"
                value={recordName}
                onChange={(e) => setRecordName(e.target.value)}
                fullWidth
                disabled={extracting}
                placeholder="Auto-filled from filename"
              />
            </>
          )}

          {/* Step 2: Suggest - Show extracted metadata */}
          {step === 'choose' && (
            <>
              <Alert severity="success">
                <Typography variant="body2" sx={{ fontWeight: 600 }}>
                  ✓ Metadata extracted from {file?.name}
                </Typography>
              </Alert>

              <Box>
                <Typography variant="h6" sx={{ mb: 2 }}>
                  Extracted Metadata
                </Typography>
                <Paper variant="outlined" sx={{ p: 2, maxHeight: 150, overflow: 'auto' }}>
                  <Stack spacing={1}>
                    {Object.entries(metadata)
                      .filter(([k]) => k !== 'file_path' && k !== 'original_filename')
                      .slice(0, 8)
                      .map(([key, value]) => (
                        <Box key={key} sx={{ display: 'flex', justifyContent: 'space-between', gap: 1 }}>
                          <Typography variant="body2" sx={{ fontWeight: 500 }}>
                            {key}:
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {String(value).substring(0, 50)}
                          </Typography>
                        </Box>
                      ))}
                  </Stack>
                </Paper>
              </Box>

              <Box>
                <Typography variant="h6" sx={{ mb: 2 }}>
                  Choose Schema
                </Typography>

                <RadioGroup
                  value={chosenAction}
                  onChange={(e) => setChosenAction(e.target.value as 'use_existing' | 'create_new')}
                >
                  <FormControlLabel value="use_existing" control={<Radio />} label="Use Existing Schema" />

                  {chosenAction === 'use_existing' && (
                    <FormControl fullWidth sx={{ ml: 3, mt: 1 }}>
                      <InputLabel>Available Schemas</InputLabel>
                      <Select
                        value={chosenSchemaId}
                        label="Available Schemas"
                        onChange={(e) => setChosenSchemaId(e.target.value)}
                      >
                        <MenuItem value="">
                          <em>Select Schema</em>
                        </MenuItem>
                        {candidates.map((c) => (
                          <MenuItem key={c.id} value={c.id}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <span>{c.name}</span>
                              <Chip
                                label={`${c.match_score}% match`}
                                size="small"
                                color={c.match_score >= 75 ? 'success' : c.match_score >= 50 ? 'warning' : 'default'}
                                variant="outlined"
                              />
                            </Box>
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  )}

                  {candidates.length === 0 && (
                    <Alert severity="warning" sx={{ mt: 1 }}>
                      <Typography variant="body2">
                        No existing schemas for this asset type. Create a new one.
                      </Typography>
                    </Alert>
                  )}

                  <FormControlLabel
                    value="create_new"
                    control={<Radio />}
                    label="Create New Schema"
                    sx={{ mt: 2 }}
                  />

                  {chosenAction === 'create_new' && (
                    <TextField
                      label="Schema Name"
                      value={newSchemaName}
                      onChange={(e) => setNewSchemaName(e.target.value)}
                      fullWidth
                      sx={{ ml: 3, mt: 1 }}
                      placeholder="e.g., Image Metadata, Document Info"
                    />
                  )}
                </RadioGroup>
              </Box>

              <Box>
                <Typography variant="body2" sx={{ fontWeight: 500, mb: 1 }}>
                  Detected Fields ({suggestedFields.length})
                </Typography>
                <Paper variant="outlined" sx={{ maxHeight: 200, overflow: 'auto' }}>
                  <Table size="small">
                    <TableHead>
                      <TableRow sx={{ bgcolor: 'action.hover' }}>
                        <TableCell>Field</TableCell>
                        <TableCell>Type</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {suggestedFields.map((f, idx) => (
                        <TableRow key={idx}>
                          <TableCell>{f.field_name}</TableCell>
                          <TableCell>
                            <Chip label={f.field_type} size="small" variant="outlined" />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </Paper>
              </Box>
            </>
          )}

          {/* Step 3: Success */}
          {step === 'success' && (
            <Stack alignItems="center" spacing={2} sx={{ py: 3 }}>
              <Check size={64} color="green" />
              <Typography variant="h6">Upload Complete!</Typography>
              <Typography color="text.secondary" align="center">
                File has been processed and record created successfully.
              </Typography>
            </Stack>
          )}
        </Stack>
      </DialogContent>

      <DialogActions>
        <Button onClick={handleClose} disabled={extracting || uploading}>
          Cancel
        </Button>

        {step === 'select' && (
          <Button
            variant="contained"
            onClick={handleSuggest}
            disabled={extracting || !file || !assetTypeId}
          >
            {extracting ? 'Extracting...' : 'Extract & Preview'}
          </Button>
        )}

        {step === 'choose' && (
          <>
            <Button onClick={() => setStep('select')} disabled={uploading}>
              Back
            </Button>
            <Button
              variant="contained"
              onClick={handleCommit}
              disabled={uploading || !chosenSchemaId && chosenAction === 'use_existing'}
            >
              {uploading ? 'Uploading...' : 'Upload & Create Record'}
            </Button>
          </>
        )}

        {step === 'success' && (
          <Button variant="contained" onClick={handleClose}>
            Done
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};
