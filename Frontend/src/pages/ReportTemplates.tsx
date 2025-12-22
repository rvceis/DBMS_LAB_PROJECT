import { useEffect, useState } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  Stack,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
} from '@mui/material';
import { Plus, Download, Edit, Trash2, FileText, FileType } from 'lucide-react';
import { useReportStore } from '@/stores/reportStore';
import toast from 'react-hot-toast';

export const ReportTemplates = () => {
  const { templates, fetchTemplates, deleteTemplate, generateReport, downloadReport, loading } = useReportStore();
  const [deleteDialog, setDeleteDialog] = useState<{ open: boolean; id?: number }>({ open: false });
  const [generating, setGenerating] = useState<number | null>(null);

  useEffect(() => {
    fetchTemplates();
  }, []);

  const handleGenerate = async (templateId: number, format: 'csv' | 'pdf') => {
    setGenerating(templateId);
    try {
      const execution = await generateReport(templateId, format);
      if (execution.status === 'completed') {
        toast.success('Report generated!');
        // Use store method to download with proper auth
        await downloadReport(execution.id);
      } else {
        toast.success('Report generation started. Check history for status.');
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to generate report');
    } finally {
      setGenerating(null);
    }
  };

  const handleDelete = async () => {
    if (!deleteDialog.id) return;
    try {
      await deleteTemplate(deleteDialog.id);
      toast.success('Template deleted');
      setDeleteDialog({ open: false });
    } catch (error) {
      toast.error('Failed to delete template');
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700 }}>
          Report Templates
        </Typography>
        <Button
          variant="contained"
          startIcon={<Plus size={20} />}
          href="/reports/builder"
        >
          New Template
        </Button>
      </Box>

      {loading && templates.length === 0 ? (
        <Typography>Loading templates...</Typography>
      ) : templates.length === 0 ? (
        <Card sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary">
            No report templates yet
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Create your first report template to get started
          </Typography>
          <Button
            variant="contained"
            startIcon={<Plus size={20} />}
            href="/reports/builder"
            sx={{ mt: 2 }}
          >
            Create Template
          </Button>
        </Card>
      ) : (
        <Grid container spacing={3}>
          {templates.map((template) => (
            <Grid item xs={12} md={6} lg={4} key={template.id}>
              <Card>
                <CardContent>
                  <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
                    <Box>
                      <Typography variant="h6" sx={{ fontWeight: 600 }}>
                        {template.name}
                      </Typography>
                      {template.description && (
                        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                          {template.description}
                        </Typography>
                      )}
                    </Box>
                    <IconButton
                      size="small"
                      onClick={() => setDeleteDialog({ open: true, id: template.id })}
                    >
                      <Trash2 size={16} />
                    </IconButton>
                  </Stack>

                  <Stack direction="row" spacing={1} sx={{ mt: 2 }}>
                    {template.is_public && (
                      <Chip label="Public" size="small" color="success" variant="outlined" />
                    )}
                    <Chip
                      label={`${template.query_config?.fields?.length || 0} fields`}
                      size="small"
                      variant="outlined"
                    />
                    {template.query_config?.filters?.length > 0 && (
                      <Chip
                        label={`${template.query_config.filters.length} filters`}
                        size="small"
                        variant="outlined"
                      />
                    )}
                  </Stack>

                  <Stack direction="row" spacing={1} sx={{ mt: 3 }}>
                    <Button
                      size="small"
                      variant="outlined"
                      startIcon={<FileText size={16} />}
                      onClick={() => handleGenerate(template.id, 'csv')}
                      disabled={generating === template.id}
                    >
                      CSV
                    </Button>
                    <Button
                      size="small"
                      variant="outlined"
                      startIcon={<FileType size={16} />}
                      onClick={() => handleGenerate(template.id, 'pdf')}
                      disabled={generating === template.id}
                    >
                      PDF
                    </Button>
                    <Button
                      size="small"
                      startIcon={<Edit size={16} />}
                      href={`/reports/builder?template=${template.id}`}
                    >
                      Edit
                    </Button>
                  </Stack>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialog.open} onClose={() => setDeleteDialog({ open: false })}>
        <DialogTitle>Delete Template</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete this report template? This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialog({ open: false })}>Cancel</Button>
          <Button variant="contained" color="error" onClick={handleDelete}>
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
