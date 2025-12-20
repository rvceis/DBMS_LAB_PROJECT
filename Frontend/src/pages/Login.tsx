import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Card, TextField, Button, Typography, Link, Container, Stack } from '@mui/material';
import { useForm } from 'react-hook-form';
import { useAuthStore } from '@/stores/authStore';

export const Login = () => {
  const navigate = useNavigate();
  const { login, isAuthenticated, loading, error } = useAuthStore();
  const { register, handleSubmit, formState: { errors } } = useForm({
    defaultValues: { email: 'admin@test.com', password: 'password' },
  });

  useEffect(() => {
    if (isAuthenticated()) navigate('/dashboard');
  }, [isAuthenticated(), navigate]);

  const onSubmit = async (data: any) => {
    try {
      await login(data.email, data.password);
      navigate('/dashboard');
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <Container maxWidth="sm">
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
        }}
      >
        <Card sx={{ p: 4, width: '100%', borderRadius: 2 }}>
          <Typography variant="h4" sx={{ mb: 1, fontWeight: 700, textAlign: 'center' }}>
            MetaDB
          </Typography>
          <Typography variant="body2" sx={{ mb: 3, textAlign: 'center', color: 'text.secondary' }}>
            Dynamic Schema Management Platform
          </Typography>

          <form onSubmit={handleSubmit(onSubmit)}>
            <Stack spacing={2}>
              <TextField
                {...register('email', { required: 'Email required' })}
                label="Email"
                type="email"
                fullWidth
                error={!!errors.email}
                helperText={errors.email?.message}
              />
              <TextField
                {...register('password', { required: 'Password required' })}
                label="Password"
                type="password"
                fullWidth
                error={!!errors.password}
                helperText={errors.password?.message}
              />
              {error && <Typography color="error">{error}</Typography>}
              <Button variant="contained" fullWidth type="submit" disabled={loading} sx={{ mt: 2 }}>
                {loading ? 'Logging in...' : 'Login'}
              </Button>
            </Stack>
          </form>

          <Box sx={{ mt: 3, textAlign: 'center' }}>
            <Typography variant="body2">
              No account?{' '}
              <Link href="/register" underline="none" sx={{ fontWeight: 600, color: 'primary.main' }}>
                Register here
              </Link>
            </Typography>
          </Box>
        </Card>
      </Box>
    </Container>
  );
};
