import { useState } from 'react';
import {
  Box,
  Stack,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  IconButton,
  Typography,
  Chip,
  Button,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Grid,
  Checkbox,
  FormControlLabel,
} from '@mui/material';
import { Plus, Trash2, ChevronDown } from 'lucide-react';

interface Constraints {
  // Value constraints
  min?: number;
  max?: number;
  min_length?: number;
  max_length?: number;
  pattern?: string;
  pattern_key?: string;
  pattern_name?: string;
  enum?: string[];
  
  // Database constraints
  unique?: boolean;
  primary_key?: boolean;
  auto_increment?: boolean;
  indexed?: boolean;
  default_value?: any;
  foreign_key?: {
    table: string;
    field: string;
    on_delete?: 'CASCADE' | 'SET NULL' | 'RESTRICT';
    on_update?: 'CASCADE' | 'SET NULL' | 'RESTRICT';
  };
  nullable?: boolean;
}

interface ConstraintBuilderProps {
  fieldType: string;
  constraints: Constraints;
  onChange: (constraints: Constraints) => void;
}

// Common regex patterns
const PATTERNS = {
  email: {
    pattern: '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$',
    name: 'Email format'
  },
  phone: {
    pattern: '^\\+?1?\\d{9,15}$',
    name: 'Phone number'
  },
  url: {
    pattern: '^https?://[^\\s]+$',
    name: 'URL format'
  },
  alphanumeric: {
    pattern: '^[a-zA-Z0-9]+$',
    name: 'Alphanumeric only'
  },
  custom: {
    pattern: '',
    name: 'Custom pattern'
  }
};

export const ConstraintBuilder = ({ fieldType, constraints, onChange }: ConstraintBuilderProps) => {
  const [enumInput, setEnumInput] = useState('');

  const updateConstraint = (key: keyof Constraints, value: any) => {
    const updated = { ...constraints };
    if (value === '' || value === undefined || value === null) {
      delete updated[key];
    } else {
      // @ts-ignore
      updated[key] = value;
    }
    onChange(updated);
  };

  const addEnumValue = () => {
    if (!enumInput.trim()) return;
    const current = constraints.enum || [];
    if (!current.includes(enumInput.trim())) {
      updateConstraint('enum', [...current, enumInput.trim()]);
    }
    setEnumInput('');
  };

  const removeEnumValue = (value: string) => {
    const current = constraints.enum || [];
    updateConstraint('enum', current.filter(v => v !== value));
  };

  const selectPattern = (patternKey: string) => {
    const pattern = PATTERNS[patternKey as keyof typeof PATTERNS];
    if (pattern) {
      updateConstraint('pattern', pattern.pattern);
      updateConstraint('pattern_key', patternKey);
      updateConstraint('pattern_name', pattern.name);
    } else {
      updateConstraint('pattern', undefined);
      updateConstraint('pattern_key', undefined);
      updateConstraint('pattern_name', undefined);
    }
  };

  return (
    <Accordion>
      <AccordionSummary expandIcon={<ChevronDown size={20} />}>
        <Stack direction="row" spacing={1} alignItems="center">
          <Typography variant="subtitle2">Constraints</Typography>
          {Object.keys(constraints).length > 0 && (
            <Chip label={`${Object.keys(constraints).length} active`} size="small" color="primary" />
          )}
        </Stack>
      </AccordionSummary>
      <AccordionDetails>
        <Stack spacing={3}>
          {/* Number/Float constraints */}
          {(fieldType === 'integer' || fieldType === 'float') && (
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <TextField
                  label="Min Value"
                  type="number"
                  fullWidth
                  size="small"
                  value={constraints.min ?? ''}
                  onChange={(e) => updateConstraint('min', e.target.value ? Number(e.target.value) : undefined)}
                  helperText="Minimum allowed value"
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  label="Max Value"
                  type="number"
                  fullWidth
                  size="small"
                  value={constraints.max ?? ''}
                  onChange={(e) => updateConstraint('max', e.target.value ? Number(e.target.value) : undefined)}
                  helperText="Maximum allowed value"
                />
              </Grid>
            </Grid>
          )}

          {/* String constraints */}
          {fieldType === 'string' && (
            <>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <TextField
                    label="Min Length"
                    type="number"
                    fullWidth
                    size="small"
                    value={constraints.min_length ?? ''}
                    onChange={(e) => updateConstraint('min_length', e.target.value ? Number(e.target.value) : undefined)}
                    helperText="Minimum string length"
                  />
                </Grid>
                <Grid item xs={6}>
                  <TextField
                    label="Max Length"
                    type="number"
                    fullWidth
                    size="small"
                    value={constraints.max_length ?? ''}
                    onChange={(e) => updateConstraint('max_length', e.target.value ? Number(e.target.value) : undefined)}
                    helperText="Maximum string length"
                  />
                </Grid>
              </Grid>

              {/* Pattern/Regex */}
              <Box>
                <FormControl fullWidth size="small" sx={{ mb: 2 }}>
                  <InputLabel>Pattern Type</InputLabel>
                  <Select
                    value={constraints.pattern_key || ''}
                    label="Pattern Type"
                    onChange={(e) => selectPattern(e.target.value)}
                  >
                    <MenuItem value="">None</MenuItem>
                    {Object.entries(PATTERNS).map(([key, { name }]) => (
                      <MenuItem key={key} value={key}>{name}</MenuItem>
                    ))}
                  </Select>
                </FormControl>

                {constraints.pattern && (
                  <TextField
                    label="Regex Pattern"
                    fullWidth
                    size="small"
                    value={constraints.pattern}
                    onChange={(e) => updateConstraint('pattern', e.target.value)}
                    helperText="Regular expression for validation"
                    multiline
                    rows={2}
                  />
                )}
              </Box>
            </>
          )}

          {/* Enum values (for all types) */}
          <Box>
            <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
              Allowed Values (Enum)
            </Typography>
            <Stack direction="row" spacing={1} sx={{ mb: 1 }}>
              <TextField
                size="small"
                placeholder="Add allowed value..."
                value={enumInput}
                onChange={(e) => setEnumInput(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    addEnumValue();
                  }
                }}
                fullWidth
              />
              <Button
                variant="outlined"
                size="small"
                startIcon={<Plus size={16} />}
                onClick={addEnumValue}
              >
                Add
              </Button>
            </Stack>

            {constraints.enum && constraints.enum.length > 0 && (
              <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                {constraints.enum.map((value, idx) => (
                  <Chip
                    key={idx}
                    label={value}
                    size="small"
                    onDelete={() => removeEnumValue(value)}
                    deleteIcon={<Trash2 size={14} />}
                  />
                ))}
              </Stack>
            )}
          </Box>

          {/* Database Constraints */}
          <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid', borderColor: 'divider' }}>
            <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 600 }}>
              Database Constraints
            </Typography>
            
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={!!constraints.unique}
                      onChange={(e) => updateConstraint('unique', e.target.checked || undefined)}
                      size="small"
                    />
                  }
                  label="Unique"
                />
              </Grid>
              <Grid item xs={6}>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={!!constraints.indexed}
                      onChange={(e) => updateConstraint('indexed', e.target.checked || undefined)}
                      size="small"
                    />
                  }
                  label="Indexed"
                />
              </Grid>
              <Grid item xs={6}>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={!!constraints.primary_key}
                      onChange={(e) => updateConstraint('primary_key', e.target.checked || undefined)}
                      size="small"
                    />
                  }
                  label="Primary Key"
                />
              </Grid>
              <Grid item xs={6}>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={!!constraints.auto_increment}
                      onChange={(e) => updateConstraint('auto_increment', e.target.checked || undefined)}
                      size="small"
                    />
                  }
                  label="Auto Increment"
                />
              </Grid>
              <Grid item xs={6}>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={constraints.nullable !== false}
                      onChange={(e) => updateConstraint('nullable', e.target.checked ? undefined : false)}
                      size="small"
                    />
                  }
                  label="Nullable"
                />
              </Grid>
            </Grid>

            {/* Default Value */}
            <TextField
              label="Default Value"
              fullWidth
              size="small"
              value={constraints.default_value ?? ''}
              onChange={(e) => updateConstraint('default_value', e.target.value || undefined)}
              helperText="Default value for new records"
              sx={{ mt: 2 }}
            />

            {/* Foreign Key */}
            <Box sx={{ mt: 2 }}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={!!constraints.foreign_key}
                    onChange={(e) => {
                      if (e.target.checked) {
                        updateConstraint('foreign_key', { table: '', field: '', on_delete: 'CASCADE', on_update: 'CASCADE' });
                      } else {
                        updateConstraint('foreign_key', undefined);
                      }
                    }}
                    size="small"
                  />
                }
                label="Foreign Key"
              />
              {constraints.foreign_key && (
                <Box sx={{ mt: 1, pl: 4 }}>
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <TextField
                        label="Reference Table"
                        fullWidth
                        size="small"
                        value={constraints.foreign_key.table || ''}
                        onChange={(e) => updateConstraint('foreign_key', { ...constraints.foreign_key!, table: e.target.value })}
                      />
                    </Grid>
                    <Grid item xs={6}>
                      <TextField
                        label="Reference Field"
                        fullWidth
                        size="small"
                        value={constraints.foreign_key.field || ''}
                        onChange={(e) => updateConstraint('foreign_key', { ...constraints.foreign_key!, field: e.target.value })}
                      />
                    </Grid>
                    <Grid item xs={6}>
                      <FormControl fullWidth size="small">
                        <InputLabel>On Delete</InputLabel>
                        <Select
                          value={constraints.foreign_key.on_delete || 'CASCADE'}
                          label="On Delete"
                          onChange={(e) => updateConstraint('foreign_key', { ...constraints.foreign_key!, on_delete: e.target.value as any })}
                        >
                          <MenuItem value="CASCADE">CASCADE</MenuItem>
                          <MenuItem value="SET NULL">SET NULL</MenuItem>
                          <MenuItem value="RESTRICT">RESTRICT</MenuItem>
                        </Select>
                      </FormControl>
                    </Grid>
                    <Grid item xs={6}>
                      <FormControl fullWidth size="small">
                        <InputLabel>On Update</InputLabel>
                        <Select
                          value={constraints.foreign_key.on_update || 'CASCADE'}
                          label="On Update"
                          onChange={(e) => updateConstraint('foreign_key', { ...constraints.foreign_key!, on_update: e.target.value as any })}
                        >
                          <MenuItem value="CASCADE">CASCADE</MenuItem>
                          <MenuItem value="SET NULL">SET NULL</MenuItem>
                          <MenuItem value="RESTRICT">RESTRICT</MenuItem>
                        </Select>
                      </FormControl>
                    </Grid>
                  </Grid>
                </Box>
              )}
            </Box>
          </Box>

          {/* Constraint summary */}
          {Object.keys(constraints).length > 0 && (
            <Box sx={{ p: 2, backgroundColor: 'action.hover', borderRadius: 1 }}>
              <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                Active Constraints Summary:
              </Typography>
              <Stack spacing={0.5}>
                {constraints.min !== undefined && (
                  <Typography variant="body2">• Min: {constraints.min}</Typography>
                )}
                {constraints.max !== undefined && (
                  <Typography variant="body2">• Max: {constraints.max}</Typography>
                )}
                {constraints.min_length !== undefined && (
                  <Typography variant="body2">• Min length: {constraints.min_length}</Typography>
                )}
                {constraints.max_length !== undefined && (
                  <Typography variant="body2">• Max length: {constraints.max_length}</Typography>
                )}
                {constraints.pattern && (
                  <Typography variant="body2">• Pattern: {constraints.pattern_name || 'Custom regex'}</Typography>
                )}
                {constraints.enum && constraints.enum.length > 0 && (
                  <Typography variant="body2">• Allowed: {constraints.enum.join(', ')}</Typography>
                )}
                {constraints.unique && <Typography variant="body2" color="primary">• Unique</Typography>}
                {constraints.primary_key && <Typography variant="body2" color="error">• Primary Key</Typography>}
                {constraints.auto_increment && <Typography variant="body2" color="success">• Auto Increment</Typography>}
                {constraints.indexed && <Typography variant="body2">• Indexed</Typography>}
                {constraints.nullable === false && <Typography variant="body2">• Not Nullable</Typography>}
                {constraints.default_value !== undefined && (
                  <Typography variant="body2">• Default: {String(constraints.default_value)}</Typography>
                )}
                {constraints.foreign_key && (
                  <Typography variant="body2" color="secondary">
                    • Foreign Key → {constraints.foreign_key.table}.{constraints.foreign_key.field}
                  </Typography>
                )}
              </Stack>
            </Box>
          )}
        </Stack>
      </AccordionDetails>
    </Accordion>
  );
};
