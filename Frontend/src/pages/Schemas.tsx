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
import { Edit2, Trash2, Plus, Copy } from 'lucide-react';
import { useSchemaStore } from '@/stores/schemaStore';
import { useAssetTypesStore } from '@/stores/assetTypesStore';
import { useForm } from 'react-hook-form';
import toast from 'react-hot-toast';

export const Schemas = () => {
  const { schemas, fetchSchemas, createSchema, updateSchema, selectedSchema, selectSchema, addField, deleteField } =
    useSchemaStore();
  const { assetTypes, fetchAssetTypes } = useAssetTypesStore();
  const [openDialog, setOpenDialog] = useState(false);
  const [openFieldDialog, setOpenFieldDialog] = useState(false);
  const [editDialog, setEditDialog] = useState<{ open: boolean; id?: number; name?: string }>({ open: false });
  const [searchTerm, setSearchTerm] = useState('');
  const { register, handleSubmit, reset, formState: { errors } } = useForm();
  const { register: registerField, handleSubmit: handleFieldSubmit, reset: resetField } = useForm();

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
      });
      toast.success('Field added!');
      setOpenFieldDialog(false);
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
        <Button variant="contained" startIcon={<Plus size={20} />} onClick={() => setOpenDialog(true)}>
          New Schema
        </Button>
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
                  <Button
                    size="small"
                    startIcon={<Plus size={16} />}
                    onClick={() => setOpenFieldDialog(true)}
                  >
                    Add Field
                  </Button>
                </Box>

                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow sx={{ backgroundColor: 'action.hover' }}>
                        <TableCell>Field Name</TableCell>
                        <TableCell>Type</TableCell>
                        <TableCell>Required</TableCell>
                        <TableCell align="right">Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {selectedSchema.fields?.map((field) => (
                        <TableRow key={field.id} hover>
                          <TableCell>{field.field_name}</TableCell>
                          <TableCell>{field.field_type}</TableCell>
                          <TableCell>{field.is_required ? '✓' : '-'}</TableCell>
                          <TableCell align="right">
                            <IconButton size="small" onClick={() => onDeleteField(field.field_name)}>
                              <Trash2 size={16} />
                            </IconButton>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
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
                helperText={errors.schemaName?.message}
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
                </Select>
              </FormControl>
              <FormControlLabel
                control={<Checkbox {...registerField('isRequired')} />}
                label="Required"
              />
            </Stack>

            <DialogActions sx={{ mt: 3 }}>
              <Button onClick={() => setOpenFieldDialog(false)}>Cancel</Button>
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
    </Box>
  );
};
