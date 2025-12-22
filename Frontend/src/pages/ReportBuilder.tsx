import { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  Stack,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Checkbox,
  FormControlLabel,
  Chip,
  IconButton,
  Grid,
  Stepper,
  Step,
  StepLabel,
} from '@mui/material';
import { Plus, Trash2, Download, Save } from 'lucide-react';
import { useSchemaStore } from '@/stores/schemaStore';
import { useReportStore, type FilterDef, type QueryConfig } from '@/stores/reportStore';
import toast from 'react-hot-toast';
import { useNavigate, useSearchParams } from 'react-router-dom';

export const ReportBuilder = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const templateId = searchParams.get('template');

  const { schemas, fetchSchemas } = useSchemaStore();
  const { createTemplate, updateTemplate, fetchTemplate, selectedTemplate, generateAdhocReport, downloadReport } = useReportStore();

  const [activeStep, setActiveStep] = useState(0);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [schemaId, setSchemaId] = useState<number | ''>('');
  const [selectedFields, setSelectedFields] = useState<string[]>([]);
  const [filters, setFilters] = useState<FilterDef[]>([]);
  const [format, setFormat] = useState<'csv' | 'pdf'>('csv');
  const [isPublic, setIsPublic] = useState(false);
  const [pdfOrientation, setPdfOrientation] = useState<'portrait' | 'landscape'>('portrait');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchSchemas();
    if (templateId) {
      fetchTemplate(parseInt(templateId));
    }
  }, [templateId]);

  useEffect(() => {
    if (selectedTemplate && templateId) {
      setName(selectedTemplate.name);
      setDescription(selectedTemplate.description || '');
      setSchemaId(selectedTemplate.schema_id);
      setSelectedFields(selectedTemplate.query_config?.fields || []);
      setFilters(selectedTemplate.query_config?.filters || []);
      setIsPublic(selectedTemplate.is_public);
      setPdfOrientation(selectedTemplate.pdf_config?.orientation || 'portrait');
    }
  }, [selectedTemplate, templateId]);

  const selectedSchema = schemas.find((s) => s.id === schemaId);
  const availableFields = selectedSchema?.fields?.filter((f) => !f.is_deleted) || [];

  const addFilter = () => {
    setFilters([...filters, { field: '', operator: 'eq', value: '' }]);
  };

  const removeFilter = (index: number) => {
    setFilters(filters.filter((_, i) => i !== index));
  };

  const updateFilter = (index: number, key: keyof FilterDef, value: any) => {
    const updated = [...filters];
    updated[index] = { ...updated[index], [key]: value };
    setFilters(updated);
  };

  const handleSave = async () => {
    if (!name) {
      toast.error('Please enter a report name');
      return;
    }
    if (!schemaId) {
      toast.error('Please select a schema');
      return;
    }

    setSaving(true);
    try {
      const queryConfig: QueryConfig = {
        fields: selectedFields,
        filters,
        sort: [],
        limit: 10000,
      };

      const data = {
        name,
        description,
        schema_id: schemaId as number,
        query_config: queryConfig,
        display_config: {},
        pdf_config: {
          orientation: pdfOrientation,
          page_size: 'A4' as const,
        },
        is_public: isPublic,
      };

      if (templateId) {
        await updateTemplate(parseInt(templateId), data);
        toast.success('Template updated!');
      } else {
        await createTemplate(data);
        toast.success('Template created!');
      }
      navigate('/reports/templates');
    } catch (error: any) {
      toast.error(error.message || 'Failed to save template');
    } finally {
      setSaving(false);
    }
  };

  const handleGenerateNow = async () => {
    if (!schemaId) {
      toast.error('Please select a schema');
      return;
    }

    setSaving(true);
    try {
      const queryConfig: QueryConfig = {
        fields: selectedFields,
        filters,
        sort: [],
        limit: 10000,
      };

      const execution = await generateAdhocReport(schemaId as number, queryConfig, format, name || 'Ad-hoc Report');
      if (execution.status === 'completed') {
        toast.success('Report generated!');
        // Use store method to download with proper auth
        await downloadReport(execution.id);
      } else {
        toast.success('Report generation started');
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to generate report');
    } finally {
      setSaving(false);
    }
  };

  const steps = ['Basic Info', 'Select Fields', 'Add Filters', 'Format & Save'];

  return (
    <Box>
      <Typography variant="h4" sx={{ fontWeight: 700, mb: 4 }}>
        {templateId ? 'Edit Report Template' : 'Create Report Template'}
      </Typography>

      <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
        {steps.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>

      <Card>
        <CardContent>
          {activeStep === 0 && (
            <Stack spacing={3}>
              <TextField
                label="Report Name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                fullWidth
                required
              />
              <TextField
                label="Description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                fullWidth
                multiline
                rows={3}
              />
              <FormControl fullWidth required>
                <InputLabel>Schema</InputLabel>
                <Select
                  value={schemaId}
                  label="Schema"
                  onChange={(e) => setSchemaId(e.target.value as number)}
                >
                  <MenuItem value="">
                    <em>Select Schema</em>
                  </MenuItem>
                  {schemas.map((schema) => (
                    <MenuItem key={schema.id} value={schema.id}>
                      {schema.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Stack>
          )}

          {activeStep === 1 && (
            <Box>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Select Fields to Include
              </Typography>
              {!schemaId ? (
                <Typography color="text.secondary">Please select a schema first</Typography>
              ) : (
                <Stack spacing={1}>
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={selectedFields.length === availableFields.length}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedFields(availableFields.map((f) => f.field_name));
                          } else {
                            setSelectedFields([]);
                          }
                        }}
                      />
                    }
                    label="Select All"
                  />
                  {availableFields.map((field) => (
                    <FormControlLabel
                      key={field.id}
                      control={
                        <Checkbox
                          checked={selectedFields.includes(field.field_name)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedFields([...selectedFields, field.field_name]);
                            } else {
                              setSelectedFields(selectedFields.filter((f) => f !== field.field_name));
                            }
                          }}
                        />
                      }
                      label={
                        <Stack direction="row" spacing={1} alignItems="center">
                          <Typography>{field.field_name}</Typography>
                          <Chip label={field.field_type} size="small" variant="outlined" />
                        </Stack>
                      }
                    />
                  ))}
                </Stack>
              )}
            </Box>
          )}

          {activeStep === 2 && (
            <Box>
              <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
                <Typography variant="h6">Filters</Typography>
                <Button startIcon={<Plus size={16} />} onClick={addFilter}>
                  Add Filter
                </Button>
              </Stack>

              {filters.length === 0 ? (
                <Typography color="text.secondary">No filters added</Typography>
              ) : (
                <Stack spacing={2}>
                  {filters.map((filter, index) => (
                    <Card key={index} variant="outlined">
                      <CardContent>
                        <Grid container spacing={2} alignItems="center">
                          <Grid item xs={3}>
                            <FormControl fullWidth size="small">
                              <InputLabel>Field</InputLabel>
                              <Select
                                value={filter.field}
                                label="Field"
                                onChange={(e) => updateFilter(index, 'field', e.target.value)}
                              >
                                {availableFields.map((field) => (
                                  <MenuItem key={field.id} value={field.field_name}>
                                    {field.field_name}
                                  </MenuItem>
                                ))}
                              </Select>
                            </FormControl>
                          </Grid>
                          <Grid item xs={3}>
                            <FormControl fullWidth size="small">
                              <InputLabel>Operator</InputLabel>
                              <Select
                                value={filter.operator}
                                label="Operator"
                                onChange={(e) => updateFilter(index, 'operator', e.target.value)}
                              >
                                <MenuItem value="eq">Equals</MenuItem>
                                <MenuItem value="ne">Not Equals</MenuItem>
                                <MenuItem value="gt">Greater Than</MenuItem>
                                <MenuItem value="lt">Less Than</MenuItem>
                                <MenuItem value="gte">Greater or Equal</MenuItem>
                                <MenuItem value="lte">Less or Equal</MenuItem>
                                <MenuItem value="contains">Contains</MenuItem>
                              </Select>
                            </FormControl>
                          </Grid>
                          <Grid item xs={5}>
                            <TextField
                              fullWidth
                              size="small"
                              label="Value"
                              value={filter.value}
                              onChange={(e) => updateFilter(index, 'value', e.target.value)}
                            />
                          </Grid>
                          <Grid item xs={1}>
                            <IconButton size="small" onClick={() => removeFilter(index)}>
                              <Trash2 size={16} />
                            </IconButton>
                          </Grid>
                        </Grid>
                      </CardContent>
                    </Card>
                  ))}
                </Stack>
              )}
            </Box>
          )}

          {activeStep === 3 && (
            <Stack spacing={3}>
              <FormControl fullWidth>
                <InputLabel>Default Format</InputLabel>
                <Select value={format} label="Default Format" onChange={(e) => setFormat(e.target.value as any)}>
                  <MenuItem value="csv">CSV (Excel compatible)</MenuItem>
                  <MenuItem value="pdf">PDF (Formatted document)</MenuItem>
                </Select>
              </FormControl>

              {format === 'pdf' && (
                <FormControl fullWidth>
                  <InputLabel>PDF Orientation</InputLabel>
                  <Select
                    value={pdfOrientation}
                    label="PDF Orientation"
                    onChange={(e) => setPdfOrientation(e.target.value as any)}
                  >
                    <MenuItem value="portrait">Portrait</MenuItem>
                    <MenuItem value="landscape">Landscape</MenuItem>
                  </Select>
                </FormControl>
              )}

              <FormControlLabel
                control={<Checkbox checked={isPublic} onChange={(e) => setIsPublic(e.target.checked)} />}
                label="Make this template public (visible to all users)"
              />
            </Stack>
          )}

          <Stack direction="row" justifyContent="space-between" sx={{ mt: 4 }}>
            <Button disabled={activeStep === 0} onClick={() => setActiveStep(activeStep - 1)}>
              Back
            </Button>
            <Stack direction="row" spacing={2}>
              {activeStep === steps.length - 1 && (
                <>
                  <Button
                    variant="outlined"
                    startIcon={<Download size={16} />}
                    onClick={handleGenerateNow}
                    disabled={saving}
                  >
                    Generate Now
                  </Button>
                  <Button
                    variant="contained"
                    startIcon={<Save size={16} />}
                    onClick={handleSave}
                    disabled={saving}
                  >
                    Save Template
                  </Button>
                </>
              )}
              {activeStep < steps.length - 1 && (
                <Button variant="contained" onClick={() => setActiveStep(activeStep + 1)}>
                  Next
                </Button>
              )}
            </Stack>
          </Stack>
        </CardContent>
      </Card>
    </Box>
  );
};
