import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Card, TextField, Button, Typography, Link, Container, Stack, MenuItem } from '@mui/material';
import { useForm } from 'react-hook-form';
import { useAuthStore } from '@/stores/authStore';

export const Register = () => {
  const navigate = useNavigate();
  const { register: registerUser, isAuthenticated, loading, error } = useAuthStore();
  const { register, handleSubmit, formState: { errors } } = useForm({
    defaultValues: { username: '', email: '', password: '', role: 'viewer' },
  });

  useEffect(() => {
    if (isAuthenticated()) navigate('/dashboard');
  }, [isAuthenticated(), navigate]);

  const onSubmit = async (data: any) => {
    try {
      await registerUser(data.username, data.email, data.password, data.role);
      navigate('/dashboard');
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <Container maxWidth="sm">
      <Box sx={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
        <Card sx={{ p: 4, width: '100%', borderRadius: 2 }}>
          <Typography variant="h4" sx={{ mb: 1, fontWeight: 700, textAlign: 'center' }}>
            Create Account
          </Typography>
          <Typography variant="body2" sx={{ mb: 3, textAlign: 'center', color: 'text.secondary' }}>
            Join MetaDB to manage dynamic schemas
          </Typography>

          <form onSubmit={handleSubmit(onSubmit)}>
            <Stack spacing={2}>
              <TextField
                {...register('username', { required: 'Username required' })}
                label="Username"
                fullWidth
                error={!!errors.username}
                helperText={errors.username?.message as string}
              />
              <TextField
                {...register('email', { required: 'Email required' })}
                label="Email"
                type="email"
                fullWidth
                error={!!errors.email}
                helperText={errors.email?.message as string}
              />
              <TextField
                {...register('password', { required: 'Password required' })}
                label="Password"
                type="password"
                fullWidth
                error={!!errors.password}
                helperText={errors.password?.message as string}
              />
              <TextField select label="Role" defaultValue="viewer" {...register('role')}> 
                <MenuItem value="viewer">Viewer</MenuItem>
                <MenuItem value="editor">Editor</MenuItem>
                <MenuItem value="admin">Admin</MenuItem>
              </TextField>
              {error && <Typography color="error">{error}</Typography>}
              <Button variant="contained" fullWidth type="submit" disabled={loading} sx={{ mt: 2 }}>
                {loading ? 'Creating...' : 'Register'}
              </Button>
            </Stack>
          </form>

          <Box sx={{ mt: 3, textAlign: 'center' }}>
            <Typography variant="body2">
              Already have an account?{' '}
              <Link href="/login" underline="none" sx={{ fontWeight: 600, color: 'primary.main' }}>
                Login
              </Link>
            </Typography>
          </Box>
        </Card>
      </Box>
    </Container>
  );
};
