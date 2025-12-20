import { CircularProgress, Box } from '@mui/material';

export const LoadingSpinner = () => (
  <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 200 }}>
    <CircularProgress />
  </Box>
);
