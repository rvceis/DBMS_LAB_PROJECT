import { useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Stack,
  Typography,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  Chip,
  CircularProgress,
} from '@mui/material';
import { useUsersStore } from '@/stores/usersStore';
import { useAuthStore } from '@/stores/authStore';

export const Users = () => {
  const { users, fetchUsers, loading, error } = useUsersStore();
  const { user } = useAuthStore();

  useEffect(() => {
    fetchUsers();
  }, []);

  if (!user || user.role !== 'admin') {
    return (
      <Box sx={{ p: 3 }}>
        <Typography color="error">Admin access required</Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 700 }}>
          Users
        </Typography>
      </Stack>

      <Card>
        <CardHeader title="System Users" />
        <CardContent>
          {error && (
            <Typography color="error" sx={{ mb: 2 }}>
              {error}
            </Typography>
          )}

          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
              <CircularProgress />
            </Box>
          ) : users.length === 0 ? (
            <Typography color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
              No users found
            </Typography>
          ) : (
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>ID</TableCell>
                  <TableCell>Username</TableCell>
                  <TableCell>Email</TableCell>
                  <TableCell>Role</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {users.map((u) => (
                  <TableRow key={u.id} hover>
                    <TableCell>{u.id}</TableCell>
                    <TableCell sx={{ fontWeight: 500 }}>{u.username}</TableCell>
                    <TableCell>{u.email}</TableCell>
                    <TableCell>
                      <Chip
                        label={u.role}
                        size="small"
                        color={u.role === 'admin' ? 'error' : u.role === 'editor' ? 'primary' : 'default'}
                        variant="outlined"
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};
