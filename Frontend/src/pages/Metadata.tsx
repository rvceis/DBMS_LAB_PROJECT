import { useEffect, useState } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  TextField,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  IconButton,
  Stack,
  Paper,
  Drawer,
  Checkbox,
  FormControlLabel,
  Switch,
} from '@mui/material';
import { Plus, Trash2, Eye, Edit2, Filter, X, Upload, FileUp } from 'lucide-react';
import { useAuthStore } from '@/stores/authStore';
import { useMetadataStore } from '@/stores/metadataStore';
import { useSchemaStore, Schema, SchemaField } from '@/stores/schemaStore';
import { useAssetTypesStore } from '@/stores/assetTypesStore';
import { useForm } from 'react-hook-form';
import toast from 'react-hot-toast';
import { EmptyState } from '@/components/common/EmptyState';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { ConfirmDialog } from '@/components/common/ConfirmDialog';
import { useFieldValidation } from '@/hooks/useFieldValidation';
import { DataImportDialog } from '@/components/common/DataImportDialog';
import { SmartFileUploadDialog } from '@/components/common/SmartFileUploadDialog';

export const Metadata = () => {
  const {
    records,
    fetchRecords,
    createRecord,
    updateRecord,
    deleteRecord,
    selectedRecord,
    selectRecord,
    filters,
    setFilters,
    loading,
  } = useMetadataStore();

  const { schemas, fetchSchemas } = useSchemaStore();
  const { assetTypes, fetchAssetTypes } = useAssetTypesStore();
  const { user } = useAuthStore();
  const { errors: validationErrors, validateAll, clearErrors, clearFieldError } = useFieldValidation();

  const [openDialog, setOpenDialog] = useState(false);
  const [editDialog, setEditDialog] = useState<{ open: boolean; record?: any }>({ open: false });
  const [openDetailDrawer, setOpenDetailDrawer] = useState(false);
  const [openDeleteDialog, setOpenDeleteDialog] = useState(false);
  const [deleteId, setDeleteId] = useState<number | null>(null);
  const [selectedSchema, setSelectedSchema] = useState<Schema | null>(null);
  const [fieldValues, setFieldValues] = useState<Record<string, any>>({});
  const [searchTerm, setSearchTerm] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [jsonValuesText, setJsonValuesText] = useState<string>("{}");
  const [importDialog, setImportDialog] = useState<{ open: boolean; schemaId?: number }>({ open: false });
  const [smartUploadDialog, setSmartUploadDialog] = useState(false);

  const { register, handleSubmit, reset, watch, setValue } = useForm({
    defaultValues: {
      name: '',
      assetTypeId: '',
      schemaId: '',
      tag: '',
      createNewSchema: false,
    },
  });

  const watchSchemaId = watch('schemaId');
  const watchAssetTypeId = watch('assetTypeId');
  const watchCreateNewSchema = watch('createNewSchema');

  useEffect(() => {
    fetchRecords();
    fetchSchemas();
    fetchAssetTypes();
  }, []);

  useEffect(() => {
    if (watchSchemaId) {
      const schema = schemas.find((s) => s.id === parseInt(watchSchemaId));
      setSelectedSchema(schema || null);
      // Initialize field values with defaults
      if (schema) {
        const defaults: Record<string, any> = {};
        schema.fields?.forEach((field) => {
          if (field.default_value) {
            defaults[field.field_name] = field.default_value;
          }
        });
        setFieldValues(defaults);
      }
    }
  }, [watchSchemaId, schemas]);

  const handleOpenDialog = () => {
    reset();
    setFieldValues({});
    setSelectedSchema(null);
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    reset();
    setFieldValues({});
    setSelectedSchema(null);
  };

  const handleFieldChange = (fieldName: string, value: any) => {
    setFieldValues((prev) => ({ ...prev, [fieldName]: value }));
    // Clear validation error when user types
    clearFieldError(fieldName);
  };

  const onSubmit = async (data: any) => {
    try {
      if (!data.assetTypeId) {
        toast.error('Please select an asset type');
        return;
      }
      if (!data.schemaId && !data.createNewSchema) {
        toast.error('Select a schema or enable auto-create');
        return;
      }
      
      // Validate fields if using existing schema
      if (data.schemaId && selectedSchema) {
        const activeFields = selectedSchema.fields.filter((f: any) => !f.is_deleted);
        const errors = validateAll(fieldValues, activeFields);
        if (Object.keys(errors).length > 0) {
          toast.error('Please fix validation errors');
          return;
        }
      }
      
      let valuesToSend = { ...fieldValues };
      // If auto-creating schema without selecting one, require JSON values input
      if (!data.schemaId && data.createNewSchema) {
        try {
          const parsed = JSON.parse(jsonValuesText || '{}');
          if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
            toast.error('Values must be a JSON object');
            return;
          }
          if (Object.keys(parsed).length === 0 && Object.keys(valuesToSend).length === 0) {
            toast.error('Provide at least one field in values');
            return;
          }
          // Merge parsed into valuesToSend, text input wins
          valuesToSend = { ...valuesToSend, ...parsed };
        } catch (e) {
          toast.error('Invalid JSON in Values');
          return;
        }
      }
      await createRecord({
        // Before submitting, transform json/array/object fields if using existing schema
        // so backend receives correct types
        // Note: auto-create path uses JSON object input already
        
        name: data.name,
        schema_id: data.schemaId ? parseInt(data.schemaId) : undefined,
        asset_type_id: parseInt(data.assetTypeId),
        values: (() => {
          if (data.schemaId && selectedSchema) {
            const activeFields = selectedSchema.fields.filter((f: any) => !f.is_deleted);
            const transformed = { ...valuesToSend } as Record<string, any>;
            for (const f of activeFields) {
              const raw = transformed[f.field_name];
              if (raw === undefined || raw === null || raw === '') continue;
              try {
                if (f.field_type === 'json' || f.field_type === 'object') {
                  transformed[f.field_name] = typeof raw === 'string' ? JSON.parse(raw) : raw;
                } else if (f.field_type === 'array') {
                  if (typeof raw === 'string') {
                    const trimmed = raw.trim();
                    transformed[f.field_name] = trimmed.startsWith('[')
                      ? JSON.parse(trimmed)
                      : trimmed.split(',').map((v) => v.trim());
                  }
                }
              } catch (e) {
                toast.error(`Field '${f.field_name}' has invalid ${f.field_type} data`);
                throw e;
              }
            }
            return transformed;
          }
          return valuesToSend;
        })(),
        create_new_schema: data.createNewSchema,
        tag: data.tag || undefined,
      });
      toast.success('Metadata record created!');
      handleCloseDialog();
      fetchRecords();
    } catch (error) {
      toast.error('Failed to create record');
      console.error(error);
    }
  };

  const handleDelete = async () => {
    if (!deleteId) return;
    try {
      await deleteRecord(deleteId);
      toast.success('Record deleted!');
      setOpenDeleteDialog(false);
      setDeleteId(null);
    } catch (error) {
      toast.error('Failed to delete record');
    }
  };

  const handleViewDetails = (record: any) => {
    selectRecord(record);
    setOpenDetailDrawer(true);
  };

  const handleEditRecord = (record: any) => {
    setEditDialog({ open: true, record });
    setFieldValues(record.values || {});
  };

  const saveRecordEdit = async () => {
    if (!editDialog.record) return;
    try {
      await updateRecord(editDialog.record.id, {
        name: editDialog.record.name,
        values: fieldValues,
      });
      setEditDialog({ open: false });
      toast.success('Record updated!');
    } catch (error) {
      toast.error('Failed to update record');
    }
  };

  const filteredRecords = records.filter((r) =>
    r.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // assetTypes come from store now

  const renderFieldInput = (field: SchemaField) => {
    const value = fieldValues[field.field_name] ?? '';
    const error = validationErrors[field.field_name];

    switch (field.field_type) {
      case 'string':
        return (
          <TextField
            fullWidth
            label={field.field_name}
            value={value}
            onChange={(e) => handleFieldChange(field.field_name, e.target.value)}
            required={field.is_required}
            helperText={error || field.description}
            error={!!error}
            size="small"
          />
        );
      case 'integer':
      case 'float':
        return (
          <TextField
            fullWidth
            label={field.field_name}
            type="number"
            value={value}
            onChange={(e) =>
              handleFieldChange(
                field.field_name,
                field.field_type === 'integer' ? parseInt(e.target.value) || 0 : parseFloat(e.target.value) || 0
              )
            }
            required={field.is_required}
            helperText={error || field.description}
            error={!!error}
            size="small"
          />
        );
      case 'boolean':
        return (
          <FormControl fullWidth size="small" error={!!error}>
            <InputLabel>{field.field_name}</InputLabel>
            <Select
              value={value === '' ? '' : value}
              onChange={(e) => handleFieldChange(field.field_name, e.target.value)}
              label={field.field_name}
            >
              <MenuItem value="">
                <em>None</em>
              </MenuItem>
              <MenuItem value={true as any}>True</MenuItem>
              <MenuItem value={false as any}>False</MenuItem>
            </Select>
            {(error || field.description) && (
              <Typography variant="caption" color={error ? 'error' : 'text.secondary'} sx={{ mt: 0.5, ml: 1.5 }}>
                {error || field.description}
              </Typography>
            )}
          </FormControl>
        );
      case 'date':
        return (
          <TextField
            fullWidth
            label={field.field_name}
            type="date"
            value={value}
            onChange={(e) => handleFieldChange(field.field_name, e.target.value)}
            required={field.is_required}
            helperText={error || field.description}
            error={!!error}
            size="small"
            InputLabelProps={{ shrink: true }}
          />
        );
      case 'json':
      case 'object':
        return (
          <TextField
            fullWidth
            label={`${field.field_name} (JSON)`}
            value={value}
            onChange={(e) => handleFieldChange(field.field_name, e.target.value)}
            required={field.is_required}
            helperText={error || field.description || 'Enter a valid JSON object'}
            error={!!error}
            multiline
            rows={3}
            size="small"
          />
        );
      case 'array':
        return (
          <TextField
            fullWidth
            label={`${field.field_name} (Array)`}
            value={value}
            onChange={(e) => handleFieldChange(field.field_name, e.target.value)}
            required={field.is_required}
            helperText={error || field.description || 'JSON array or comma-separated values'}
            error={!!error}
            multiline
            rows={2}
            size="small"
          />
        );
      default:
        return (
          <TextField
            fullWidth
            label={field.field_name}
            value={value}
            onChange={(e) => handleFieldChange(field.field_name, e.target.value)}
            required={field.is_required}
            helperText={error || field.description}
            error={!!error}
            size="small"
          />
        );
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700 }}>
          Metadata Records
        </Typography>
        <Stack direction="row" spacing={2}>
          <Button
            variant="outlined"
            startIcon={<Filter size={20} />}
            onClick={() => setShowFilters(!showFilters)}
          >
            Filters
          </Button>
          <Button
            variant="outlined"
            startIcon={<FileUp size={20} />}
            onClick={() => setSmartUploadDialog(true)}
          >
            Upload File
          </Button>
          {filters.schema_id && (
            <Button
              variant="outlined"
              startIcon={<Upload size={20} />}
              onClick={() => setImportDialog({ open: true, schemaId: filters.schema_id })}
            >
              Import Data
            </Button>
          )}
          <Button variant="contained" startIcon={<Plus size={20} />} onClick={handleOpenDialog}>
            New Record
          </Button>
        </Stack>
      </Box>

      {/* Filters Panel */}
      {showFilters && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={4}>
                <FormControl fullWidth size="small">
                  <InputLabel>Asset Type</InputLabel>
                  <Select
                    value={filters.asset_type_id ?? ''}
                    label="Asset Type"
                    onChange={(e) => {
                        const val = e.target.value as string;
                        const parsed = val ? parseInt(val) : undefined;
                        setFilters({ asset_type_id: parsed });
                        fetchRecords({ asset_type_id: parsed });
                    }}
                  >
                    <MenuItem value="">All</MenuItem>
                    {assetTypes.map((at) => (
                      <MenuItem key={at.id} value={at.id}>
                        {at.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={4}>
                <TextField
                  fullWidth
                  size="small"
                  label="Search by name"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </Grid>
              <Grid item xs={12} sm={4}>
                <Button
                  fullWidth
                  variant="outlined"
                  onClick={() => {
                    setSearchTerm('');
                    setFilters({ asset_type_id: undefined, schema_id: undefined });
                    fetchRecords({});
                  }}
                >
                  Clear Filters
                </Button>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Records Table */}
      <Card>
        <CardContent>
          {loading ? (
            <LoadingSpinner />
          ) : filteredRecords.length === 0 ? (
            <EmptyState title="No records found" message="Create your first metadata record to get started" />
          ) : (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow sx={{ backgroundColor: 'action.hover' }}>
                    <TableCell>Name</TableCell>
                    <TableCell>Schema</TableCell>
                    <TableCell>Asset Type</TableCell>
                    <TableCell>Tag</TableCell>
                    <TableCell>Created By</TableCell>
                    <TableCell>Created At</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {filteredRecords.map((record) => (
                    <TableRow key={record.id} hover>
                      <TableCell sx={{ fontWeight: 600 }}>{record.name}</TableCell>
                      <TableCell>
                        <Chip label={`Schema #${record.schema_id}`} size="small" variant="outlined" />
                      </TableCell>
                      <TableCell>{record.asset_type_name || 'N/A'}</TableCell>
                      <TableCell>
                        {record.tag && <Chip label={record.tag} size="small" color="primary" />}
                      </TableCell>
                      <TableCell>{record.created_by_name || 'Unknown'}</TableCell>
                      <TableCell>{new Date(record.created_at).toLocaleDateString()}</TableCell>
                      <TableCell align="right">
                        <IconButton size="small" onClick={() => handleViewDetails(record)}>
                          <Eye size={16} />
                        </IconButton>
                        {(user?.role === 'admin' || user?.id === record.created_by) && (
                          <>
                            <IconButton size="small" onClick={() => handleEditRecord(record)}>
                              <Edit2 size={16} />
                            </IconButton>
                            <IconButton
                              size="small"
                              color="error"
                              onClick={() => {
                                setDeleteId(record.id);
                                setOpenDeleteDialog(true);
                              }}
                            >
                              <Trash2 size={16} />
                            </IconButton>
                          </>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>

      {/* Create Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>Create New Metadata Record</DialogTitle>
        <DialogContent sx={{ pt: 3 }}>
          <form id="metadata-form" onSubmit={handleSubmit(onSubmit)}>
            <Stack spacing={3}>
              {/* Basic Info */}
              <TextField {...register('name', { required: true })} label="Record Name" fullWidth required />

              <FormControl fullWidth>
                <InputLabel>Asset Type *</InputLabel>
                <Select
                  {...register('assetTypeId', { required: true })}
                  label="Asset Type *"
                  defaultValue=""
                >
                  <MenuItem value="">
                    <em>Select...</em>
                  </MenuItem>
                  {assetTypes.map((at) => (
                    <MenuItem key={at.id} value={String(at.id)}>
                      {at.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              {watchAssetTypeId && (
                <FormControl fullWidth>
                  <InputLabel>Schema</InputLabel>
                  <Select {...register('schemaId')} label="Schema" defaultValue="">
                    <MenuItem value=""><em>None (auto-create)</em></MenuItem>
                    {schemas
                      .filter((s) => s.asset_type_id === parseInt(watchAssetTypeId))
                      .map((schema) => (
                        <MenuItem key={schema.id} value={String(schema.id)}>
                          {schema.name} (v{schema.version})
                        </MenuItem>
                      ))}
                  </Select>
                </FormControl>
              )}

              {!watchSchemaId && (
                <FormControlLabel
                  control={<Checkbox {...register('createNewSchema')} />}
                  label="Auto-create schema from field values"
                />
              )}

              <TextField {...register('tag')} label="Tag (optional)" fullWidth />

              {/* Dynamic Fields */}
              {selectedSchema && selectedSchema.fields && selectedSchema.fields.length > 0 && !watchCreateNewSchema && (
                <Paper sx={{ p: 3, backgroundColor: 'action.hover' }}>
                  <Typography variant="h6" sx={{ mb: 2 }}>
                    Field Values
                  </Typography>
                  <Grid container spacing={2}>
                    {selectedSchema.fields
                      .filter((f) => !f.is_deleted)
                      .map((field) => (
                        <Grid item xs={12} sm={6} key={field.id}>
                          {renderFieldInput(field)}
                        </Grid>
                      ))}
                  </Grid>
                </Paper>
              )}

              {watchCreateNewSchema && !watchSchemaId && (
                <Paper sx={{ p: 3, backgroundColor: 'action.hover' }}>
                  <Stack spacing={2}>
                    <Typography variant="body2" color="text.secondary">
                      No schema selected. We will auto-create a schema from the provided field values.
                      Enter a JSON object of key-value pairs below (e.g. {`{"title":"My file","pages":10}`} ).
                    </Typography>
                    <TextField
                      label="Values (JSON object)"
                      value={jsonValuesText}
                      onChange={(e) => setJsonValuesText(e.target.value)}
                      minRows={4}
                      maxRows={12}
                      fullWidth
                      multiline
                    />
                  </Stack>
                </Paper>
              )}
            </Stack>
          </form>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button variant="contained" type="submit" form="metadata-form">
            Create
          </Button>
        </DialogActions>
      </Dialog>

      {/* Detail Drawer */}
      <Drawer
        anchor="right"
        open={openDetailDrawer}
        onClose={() => setOpenDetailDrawer(false)}
        sx={{ '& .MuiDrawer-paper': { width: 400 } }}
      >
        <Box sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h6">Record Details</Typography>
            <IconButton onClick={() => setOpenDetailDrawer(false)}>
              <X size={20} />
            </IconButton>
          </Box>

          {selectedRecord && (
            <Stack spacing={2}>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Name
                </Typography>
                <Typography variant="body1" sx={{ fontWeight: 600 }}>
                  {selectedRecord.name}
                </Typography>
              </Box>

              <Box>
                <Typography variant="caption" color="text.secondary">
                  Schema
                </Typography>
                <Typography variant="body1">Schema #{selectedRecord.schema_id}</Typography>
              </Box>

              <Box>
                <Typography variant="caption" color="text.secondary">
                  Asset Type
                </Typography>
                <Typography variant="body1">{selectedRecord.asset_type_name || 'N/A'}</Typography>
              </Box>

              {selectedRecord.tag && (
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Tag
                  </Typography>
                  <Chip label={selectedRecord.tag} size="small" color="primary" sx={{ mt: 0.5 }} />
                </Box>
              )}

              <Box>
                <Typography variant="caption" color="text.secondary">
                  Field Values
                </Typography>
                <Paper sx={{ p: 2, mt: 1, backgroundColor: 'action.hover' }}>
                  {Object.entries(selectedRecord.values || {}).map(([key, value]) => (
                    <Box key={key} sx={{ mb: 1 }}>
                      <Typography variant="caption" color="text.secondary">
                        {key}:
                      </Typography>
                      <Typography variant="body2" sx={{ fontWeight: 500 }}>
                        {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                      </Typography>
                    </Box>
                  ))}
                </Paper>
              </Box>

              <Box>
                <Typography variant="caption" color="text.secondary">
                  Created By
                </Typography>
                <Typography variant="body1">{selectedRecord.created_by_name || 'Unknown'}</Typography>
              </Box>

              <Box>
                <Typography variant="caption" color="text.secondary">
                  Created At
                </Typography>
                <Typography variant="body1">{new Date(selectedRecord.created_at).toLocaleString()}</Typography>
              </Box>
            </Stack>
          )}
        </Box>
      </Drawer>

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={openDeleteDialog}
        onClose={() => setOpenDeleteDialog(false)}
        onConfirm={handleDelete}
        title="Delete Record"
        message="Are you sure you want to delete this metadata record? This action cannot be undone."
        confirmText="Delete"
        danger
      />

      {/* Edit Record Dialog */}
      <Dialog open={editDialog.open} onClose={() => setEditDialog({ open: false })} maxWidth="md" fullWidth>
        <DialogTitle>Edit Metadata Record</DialogTitle>
        <DialogContent sx={{ pt: 3 }}>
          <Stack spacing={3}>
            <TextField
              label="Name"
              fullWidth
              value={editDialog.record?.name || ''}
              onChange={(e) => setEditDialog({ ...editDialog, record: { ...editDialog.record, name: e.target.value } })}
            />
            {editDialog.record?.schema_id && (
              <Paper sx={{ p: 3, backgroundColor: 'action.hover' }}>
                <Typography variant="subtitle2" sx={{ mb: 2 }}>Field Values</Typography>
                <Grid container spacing={2}>
                  {Object.entries(fieldValues).map(([key, value]) => (
                    <Grid item xs={12} sm={6} key={key}>
                      <TextField
                        label={key}
                        fullWidth
                        value={value || ''}
                        onChange={(e) => setFieldValues({ ...fieldValues, [key]: e.target.value })}
                      />
                    </Grid>
                  ))}
                </Grid>
              </Paper>
            )}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialog({ open: false })}>Cancel</Button>
          <Button variant="contained" onClick={saveRecordEdit}>Save</Button>
        </DialogActions>
      </Dialog>

      {/* Data Import Dialog */}
      {importDialog.schemaId && (
        <DataImportDialog
          open={importDialog.open}
          onClose={() => setImportDialog({ open: false })}
          schemaId={importDialog.schemaId}
          onSuccess={() => fetchRecords()}
        />
      )}

      {/* Smart File Upload Dialog */}
      <SmartFileUploadDialog
        open={smartUploadDialog}
        onClose={() => setSmartUploadDialog(false)}
        onSuccess={() => {
          fetchRecords();
          fetchSchemas();
        }}
      />
    </Box>
  );
};
