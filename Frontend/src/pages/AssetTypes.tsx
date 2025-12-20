import { useEffect, useState } from 'react';
import { Box, Card, CardContent, Stack, TextField, Button, Table, TableHead, TableRow, TableCell, TableBody, IconButton, Typography, Dialog, DialogTitle, DialogContent, DialogActions } from '@mui/material';
import { Plus, Trash2, Edit2 } from 'lucide-react';
import { useAssetTypesStore } from '@/stores/assetTypesStore';
import { useAuthStore } from '@/stores/authStore';
import toast from 'react-hot-toast';

export const AssetTypes = () => {
  const { assetTypes, fetchAssetTypes, updateAssetType, deleteAssetType } = useAssetTypesStore();
  const { user, token } = useAuthStore();
  const [name, setName] = useState('');
  const [editDialog, setEditDialog] = useState<{ open: boolean; id?: number; name?: string }>({ open: false });
  const isAdmin = user?.role === 'admin';

  useEffect(() => {
    fetchAssetTypes();
  }, []);

  const createType = async () => {
    if (!name.trim()) return;
    try {
      const res = await fetch('/api/asset-types', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ name: name.trim() }),
      });
      if (!res.ok) throw new Error((await res.json()).error || 'Failed');
      setName('');
      fetchAssetTypes();
      toast.success('Asset type created');
    } catch (e) {
      toast.error((e as Error).message);
    }
  };

  const handleEdit = (id: number, currentName: string) => {
    setEditDialog({ open: true, id, name: currentName });
  };

  const saveEdit = async () => {
    if (!editDialog.id || !editDialog.name?.trim()) return;
    try {
      await updateAssetType(editDialog.id, editDialog.name.trim());
      setEditDialog({ open: false });
      fetchAssetTypes();
      toast.success('Asset type updated');
    } catch (e) {
      toast.error((e as Error).message);
    }
  };

  const deleteType = async (id: number) => {
    if (!confirm('Delete this asset type?')) return;
    try {
      await deleteAssetType(id);
      fetchAssetTypes();
      toast.success('Asset type deleted');
    } catch (e) {
      toast.error((e as Error).message);
    }
  };

  return (
    <Box>
      <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 700 }}>Asset Types</Typography>
      </Stack>

      {isAdmin && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
              <TextField
                label="New asset type name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                fullWidth
              />
              <Button variant="contained" startIcon={<Plus size={18} />} onClick={createType}>
                Add
              </Button>
            </Stack>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>ID</TableCell>
                <TableCell>Name</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {assetTypes.map((t) => (
                <TableRow key={t.id} hover>
                  <TableCell>{t.id}</TableCell>
                  <TableCell>{t.name}</TableCell>
                  <TableCell align="right">
                    {isAdmin && (
                      <>
                        <IconButton size="small" onClick={() => handleEdit(t.id, t.name)}>
                          <Edit2 size={16} />
                        </IconButton>
                        <IconButton color="error" size="small" onClick={() => deleteType(t.id)}>
                          <Trash2 size={16} />
                        </IconButton>
                      </>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Edit Dialog */}
      <Dialog open={editDialog.open} onClose={() => setEditDialog({ open: false })} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Asset Type</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            label="Name"
            fullWidth
            value={editDialog.name || ''}
            onChange={(e) => setEditDialog({ ...editDialog, name: e.target.value })}
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialog({ open: false })}>Cancel</Button>
          <Button variant="contained" onClick={saveEdit}>Save</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
