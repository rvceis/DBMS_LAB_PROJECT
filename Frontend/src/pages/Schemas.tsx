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
  FormControlLabel,
  Checkbox,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  IconButton,
  Stack,
} from '@mui/material';
import { Edit2, Trash2, Plus, Wand2 } from 'lucide-react';
import { useSchemaStore } from '@/stores/schemaStore';
import type { SchemaField } from '@/stores/schemaStore';
import { useAssetTypesStore } from '@/stores/assetTypesStore';
import { useForm } from 'react-hook-form';
import toast from 'react-hot-toast';
import { ConstraintBuilder } from '@/components/common/ConstraintBuilder';
import { ExtractMetadataDialog } from '@/components/common/ExtractMetadataDialog';
import { SchemaChangeLog } from '@/components/SchemaChangeLog';

export const Schemas = () => {
  const { schemas, fetchSchemas, createSchema, updateSchema, selectedSchema, selectSchema, addField, updateField, deleteField } =
    useSchemaStore();
  const { assetTypes, fetchAssetTypes } = useAssetTypesStore();
  const [openDialog, setOpenDialog] = useState(false);
  const [openFieldDialog, setOpenFieldDialog] = useState(false);
  const [editDialog, setEditDialog] = useState<{ open: boolean; id?: number; name?: string }>({ open: false });
  const [fieldConstraints, setFieldConstraints] = useState<any>({});
  const [editFieldDialog, setEditFieldDialog] = useState<{ open: boolean; field?: any }>({ open: false });
  const [editFieldType, setEditFieldType] = useState<SchemaField['field_type']>('string');
  const [editFieldRequired, setEditFieldRequired] = useState<boolean>(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [extractDialog, setExtractDialog] = useState(false);
  const { register, handleSubmit, reset, formState: { errors } } = useForm();
  const { register: registerField, handleSubmit: handleFieldSubmit, reset: resetField, watch: watchField } = useForm();

  useEffect(() => {
    fetchSchemas();
    fetchAssetTypes();
  }, []);

  const onCreateSchema = async (data: any) => {
    try {
      await createSchema({
        name: data.schemaName,
        asset_type_id: parseInt(data.assetTypeId),
        fields: JSON.parse(data.fieldsJson),
      });
      toast.success('Schema created!');
      setOpenDialog(false);
      reset();
    } catch (error) {
      toast.error('Failed to create schema');
    }
  };

  const onAddField = async (data: any) => {
    if (!selectedSchema) return;
    try {
      await addField(selectedSchema.id, {
        field_name: data.fieldName,
        field_type: data.fieldType,
        is_required: data.isRequired || false,
        constraints: Object.keys(fieldConstraints || {}).length > 0 ? fieldConstraints : null,
      });
      toast.success('Field added!');
      setOpenFieldDialog(false);
      setFieldConstraints({});
      resetField();
    } catch (error) {
      toast.error('Failed to add field');
    }
  };

  const onDeleteField = async (fieldName: string) => {
    if (!selectedSchema || !window.confirm('Delete this field?')) return;
    try {
      await deleteField(selectedSchema.id, fieldName, false);
      toast.success('Field deleted!');
    } catch (error) {
      toast.error('Failed to delete field');
    }
  };

  const handleEditSchema = (schema: any) => {
    setEditDialog({ open: true, id: schema.id, name: schema.name });
  };

  const saveSchemaEdit = async () => {
    if (!editDialog.id || !editDialog.name?.trim()) return;
    try {
      await updateSchema(editDialog.id, { name: editDialog.name.trim() });
      setEditDialog({ open: false });
      toast.success('Schema updated!');
    } catch (error) {
      toast.error('Failed to update schema');
    }
  };

  const filteredSchemas = schemas.filter((s) => s.name.toLowerCase().includes(searchTerm.toLowerCase()));

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700 }}>
          Schemas
        </Typography>
        <Stack direction="row" spacing={2}>
          <Button
            variant="outlined"
            startIcon={<Wand2 size={20} />}
            onClick={() => setExtractDialog(true)}
          >
            Auto-Generate from File
          </Button>
          <Button variant="contained" startIcon={<Plus size={20} />} onClick={() => setOpenDialog(true)}>
            New Schema
          </Button>
        </Stack>
      </Box>

      <Grid container spacing={3}>
        {/* Schema List */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <TextField
                fullWidth
                placeholder="Search schemas..."
                size="small"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                sx={{ mb: 2 }}
              />
              <Box sx={{ maxHeight: 600, overflow: 'auto' }}>
                {filteredSchemas.map((schema) => (
                  <Box
                    key={schema.id}
                    onClick={() => selectSchema(schema)}
                    sx={{
                      p: 2,
                      mb: 1,
                      borderRadius: 1,
                      cursor: 'pointer',
                      backgroundColor: selectedSchema?.id === schema.id ? 'action.selected' : 'transparent',
                      border: selectedSchema?.id === schema.id ? '2px solid' : '1px solid',
                      borderColor: selectedSchema?.id === schema.id ? 'primary.main' : 'divider',
                      transition: 'all 0.2s',
                      '&:hover': { backgroundColor: 'action.hover' },
                    }}
                  >
                    <Typography sx={{ fontWeight: 600 }}>{schema.name}</Typography>
                    <Stack direction="row" spacing={1}>
                      <Chip label={`v${schema.version}`} size="small" variant="outlined" sx={{ mt: 1 }} />
                    </Stack>
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Schema Editor */}
        <Grid item xs={12} md={8}>
          {selectedSchema ? (
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                  <Stack direction="row" spacing={2} alignItems="center">
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>
                      {selectedSchema.name}
                    </Typography>
                    <IconButton size="small" onClick={() => handleEditSchema(selectedSchema)}>
                      <Edit2 size={18} />
                    </IconButton>
                  </Stack>
                  <Stack direction="row" spacing={1}>
                    <Button
                      size="small"
                      startIcon={<Plus size={16} />}
                      onClick={() => setOpenFieldDialog(true)}
                    >
                      Add Field
                    </Button>
                  </Stack>
                </Box>

                {/* Asset Type Display */}
                {selectedSchema.asset_type_id && assetTypes.length > 0 && (
                  <Typography variant="body2" color="textSecondary" sx={{ mt: 0.5 }}>
                    Asset Type: {assetTypes.find((at) => at.id === selectedSchema.asset_type_id)?.name || selectedSchema.asset_type_id}
                  </Typography>
                )}

                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow sx={{ backgroundColor: 'action.hover' }}>
                        <TableCell>Field Name</TableCell>
                        <TableCell>Type</TableCell>
                        <TableCell>Required</TableCell>
                        <TableCell>Constraints</TableCell>
                        <TableCell align="right">Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {selectedSchema.fields?.map((field) => (
                        <TableRow key={field.id} hover>
                          <TableCell sx={{ fontWeight: 600 }}>{field.field_name}</TableCell>
                          <TableCell>
                            <FormControl fullWidth size="small">
                              <Select
                                value={
                                  selectedSchema.fields.find((f) => f.id === field.id)?.field_type ?? field.field_type
                                }
                                onChange={async (e) => {
                                  if (!selectedSchema) {
                                    toast.error('No schema selected');
                                    return;
                                  }
                                  try {
                                    const newType = e.target.value as SchemaField['field_type'];
                                    await updateField(selectedSchema.id, field.field_name, { field_type: newType });
                                    toast.success('Type updated');
                                    // Optimistically update UI to reflect new type immediately
                                    const optimistic = {
                                      ...selectedSchema,
                                      fields: selectedSchema.fields.map((f) =>
                                        f.id === field.id ? { ...f, field_type: newType } : f
                                      ),
                                    } as typeof selectedSchema;
                                    selectSchema(optimistic);
                                  } catch (err: any) {
                                    console.error('Type update error:', err);
                                    toast.error(err?.message || 'Failed to update type');
                                  }
                                }}
                              >
                                <MenuItem value="string">String</MenuItem>
                                <MenuItem value="integer">Integer</MenuItem>
                                <MenuItem value="float">Float</MenuItem>
                                <MenuItem value="boolean">Boolean</MenuItem>
                                <MenuItem value="date">Date</MenuItem>
                                <MenuItem value="json">JSON</MenuItem>
                                <MenuItem value="array">Array</MenuItem>
                                <MenuItem value="object">Object</MenuItem>
                              </Select>
                            </FormControl>
                          </TableCell>
                          <TableCell>
                            <FormControlLabel
                              control={
                                <Checkbox
                                  checked={!!selectedSchema.fields.find((f) => f.id === field.id)?.is_required}
                                  onChange={async (e) => {
                                    if (!selectedSchema) {
                                      toast.error('No schema selected');
                                      return;
                                    }
                                    try {
                                      await updateField(selectedSchema.id, field.field_name, { is_required: e.target.checked });
                                      toast.success('Required updated');
                                      // Optimistically update UI to reflect new required state immediately
                                      const newRequired = e.target.checked;
                                      const optimistic = {
                                        ...selectedSchema,
                                        fields: selectedSchema.fields.map((f) =>
                                          f.id === field.id ? { ...f, is_required: newRequired } : f
                                        ),
                                      } as typeof selectedSchema;
                                      selectSchema(optimistic);
                                    } catch (err: any) {
                                      console.error('Required update error:', err);
                                      toast.error(err?.message || 'Failed to update required');
                                    }
                                  }}
                                />
                              }
                              label={
                                (selectedSchema.fields.find((f) => f.id === field.id)?.is_required ? 'Required' : 'Optional')
                              }
                            />
                          </TableCell>
                          <TableCell>
                            {field.constraints && Object.keys(field.constraints).length > 0 ? (
                              <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
                                {field.constraints.min !== undefined && (
                                  <Chip label={`Min: ${field.constraints.min}`} size="small" color="info" variant="outlined" />
                                )}
                                {field.constraints.max !== undefined && (
                                  <Chip label={`Max: ${field.constraints.max}`} size="small" color="info" variant="outlined" />
                                )}
                                {field.constraints.min_length !== undefined && (
                                  <Chip label={`Min Length: ${field.constraints.min_length}`} size="small" color="info" variant="outlined" />
                                )}
                                {field.constraints.max_length !== undefined && (
                                  <Chip label={`Max Length: ${field.constraints.max_length}`} size="small" color="info" variant="outlined" />
                                )}
                                {field.constraints.pattern && (
                                  <Chip 
                                    label={field.constraints.pattern_name || 'Pattern'} 
                                    size="small" 
                                    color="warning" 
                                    variant="outlined"
                                    icon={<Edit2 size={12} />}
                                  />
                                )}
                                {field.constraints.enum && field.constraints.enum.length > 0 && (
                                  <Chip 
                                    label={`Enum (${field.constraints.enum.length})`} 
                                    size="small" 
                                    color="success" 
                                    variant="outlined"
                                    title={field.constraints.enum.join(', ')}
                                  />
                                )}
                                {field.constraints.unique && (
                                  <Chip label="Unique" size="small" color="primary" variant="outlined" />
                                )}
                                {field.constraints.primary_key && (
                                  <Chip label="PK" size="small" color="error" variant="outlined" />
                                )}
                              </Stack>
                            ) : (
                              <Typography variant="caption" color="text.secondary">None</Typography>
                            )}
                          </TableCell>
                          <TableCell align="right">
                            <Stack direction="row" spacing={1} justifyContent="flex-end">
                              <IconButton size="small" onClick={() => {
                                setEditFieldDialog({ open: true, field });
                                setEditFieldType(field.field_type);
                                setEditFieldRequired(!!field.is_required);
                                setFieldConstraints(field.constraints || {});
                              }}>
                                <Edit2 size={16} />
                              </IconButton>
                              <IconButton size="small" onClick={() => onDeleteField(field.field_name)}>
                                <Trash2 size={16} />
                              </IconButton>
                            </Stack>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>

                {/* Schema Change Log */}
                {selectedSchema && selectedSchema.id && (
                  <SchemaChangeLog schemaId={selectedSchema.id} />
                )}
              </CardContent>
            </Card>
          ) : (
            <Card sx={{ p: 4, textAlign: 'center' }}>
              <Typography color="textSecondary">Select a schema to view details</Typography>
            </Card>
          )}
        </Grid>
      </Grid>

      {/* Create Schema Dialog */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Schema</DialogTitle>
        <DialogContent sx={{ pt: 3 }}>
          <form onSubmit={handleSubmit(onCreateSchema)}>
            <Stack spacing={3}>
              <TextField
                {...register('schemaName', { required: 'Schema name required' })}
                label="Schema Name"
                fullWidth
                error={!!errors.schemaName}
                helperText={errors.schemaName?.message as string}
              />
              <FormControl fullWidth>
                <InputLabel>Asset Type</InputLabel>
                <Select
                  {...register('assetTypeId', { required: true })}
                  label="Asset Type"
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
              <TextField
                {...register('fieldsJson', { required: 'Fields required' })}
                label="Fields (JSON)"
                fullWidth
                multiline
                rows={6}
                defaultValue='[{"name": "title", "type": "string", "required": true}]'
                error={!!errors.fieldsJson}
              />
            </Stack>

            <DialogActions sx={{ mt: 3 }}>
              <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
              <Button variant="contained" type="submit">
                Create
              </Button>
            </DialogActions>
          </form>
        </DialogContent>
      </Dialog>

      {/* Add Field Dialog */}
      <Dialog open={openFieldDialog} onClose={() => setOpenFieldDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Field</DialogTitle>
        <DialogContent sx={{ pt: 3 }}>
          <form onSubmit={handleFieldSubmit(onAddField)}>
            <Stack spacing={3}>
              <TextField
                {...registerField('fieldName', { required: 'Field name required' })}
                label="Field Name"
                fullWidth
              />
              <FormControl fullWidth>
                <InputLabel>Type</InputLabel>
                <Select {...registerField('fieldType')} label="Type" defaultValue="string">
                  <MenuItem value="string">String</MenuItem>
                  <MenuItem value="integer">Integer</MenuItem>
                  <MenuItem value="float">Float</MenuItem>
                  <MenuItem value="boolean">Boolean</MenuItem>
                  <MenuItem value="date">Date</MenuItem>
                  <MenuItem value="json">JSON</MenuItem>
                  <MenuItem value="array">Array</MenuItem>
                  <MenuItem value="object">Object</MenuItem>
                </Select>
              </FormControl>
              <FormControlLabel
                control={<Checkbox {...registerField('isRequired')} />}
                label="Required"
              />
              
              <ConstraintBuilder
                fieldType={watchField('fieldType') || 'string'}
                constraints={fieldConstraints}
                onChange={setFieldConstraints}
              />
            </Stack>

            <DialogActions sx={{ mt: 3 }}>
              <Button onClick={() => {
                setOpenFieldDialog(false);
                setFieldConstraints({});
              }}>Cancel</Button>
              <Button variant="contained" type="submit">
                Add
              </Button>
            </DialogActions>
          </form>
        </DialogContent>
      </Dialog>

      {/* Edit Schema Dialog */}
      <Dialog open={editDialog.open} onClose={() => setEditDialog({ open: false })} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Schema</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            label="Schema Name"
            fullWidth
            value={editDialog.name || ''}
            onChange={(e) => setEditDialog({ ...editDialog, name: e.target.value })}
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialog({ open: false })}>Cancel</Button>
          <Button variant="contained" onClick={saveSchemaEdit}>Save</Button>
        </DialogActions>
      </Dialog>

      {/* Edit Field Dialog */}
      <Dialog open={editFieldDialog.open} onClose={() => setEditFieldDialog({ open: false })} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Field</DialogTitle>
        <DialogContent sx={{ pt: 3 }}>
          {editFieldDialog.field && (
            <Stack spacing={3}>
              <TextField label="Field Name" fullWidth value={editFieldDialog.field.field_name} disabled />

              <FormControl fullWidth>
                <InputLabel>Type</InputLabel>
                <Select
                  value={editFieldType}
                  label="Type"
                  onChange={(e) => setEditFieldType(e.target.value as SchemaField['field_type'])}
                >
                  <MenuItem value="string">String</MenuItem>
                  <MenuItem value="integer">Integer</MenuItem>
                  <MenuItem value="float">Float</MenuItem>
                  <MenuItem value="boolean">Boolean</MenuItem>
                  <MenuItem value="date">Date</MenuItem>
                  <MenuItem value="json">JSON</MenuItem>
                  <MenuItem value="array">Array</MenuItem>
                  <MenuItem value="object">Object</MenuItem>
                </Select>
              </FormControl>

              <FormControlLabel
                control={<Checkbox checked={editFieldRequired} onChange={(e) => setEditFieldRequired(e.target.checked)} />}
                label="Required"
              />

              <ConstraintBuilder
                fieldType={editFieldType}
                constraints={fieldConstraints}
                onChange={setFieldConstraints}
              />
            </Stack>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditFieldDialog({ open: false })}>Cancel</Button>
          <Button
            variant="contained"
            onClick={async () => {
              if (!selectedSchema || !editFieldDialog.field) return;
              try {
                const newConstraints = Object.keys(fieldConstraints || {}).length ? fieldConstraints : null;
                await updateField(selectedSchema.id, editFieldDialog.field.field_name, {
                  field_type: editFieldType,
                  is_required: editFieldRequired,
                  constraints: newConstraints,
                });
                // Optimistic UI update for the edited field
                const optimistic = {
                  ...selectedSchema,
                  fields: selectedSchema.fields.map((f) =>
                    f.field_name === editFieldDialog.field!.field_name
                      ? { ...f, field_type: editFieldType, is_required: editFieldRequired, constraints: newConstraints || undefined }
                      : f
                  ),
                } as typeof selectedSchema;
                selectSchema(optimistic);
                toast.success('Field updated');
                setEditFieldDialog({ open: false });
                setFieldConstraints({});
                fetchSchemas();
              } catch (err) {
                toast.error('Failed to update field');
              }
            }}
          >
            Save Changes
          </Button>
        </DialogActions>
      </Dialog>

      {/* Extract Metadata Dialog */}
      <ExtractMetadataDialog
        open={extractDialog}
        onClose={() => setExtractDialog(false)}
        onSuccess={(schemaId) => {
          fetchSchemas();
          toast.success('Schema auto-generated successfully!');
        }}
      />
    </Box>
  );
};
