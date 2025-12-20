import { Box, Typography } from '@mui/material';
import { FileX } from 'lucide-react';

interface EmptyStateProps {
  title?: string;
  message?: string;
  icon?: React.ReactNode;
}

export const EmptyState = ({
  title = 'No data',
  message = 'Nothing to display yet',
  icon = <FileX size={48} />,
}: EmptyStateProps) => (
  <Box
    sx={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: 300,
      color: 'text.secondary',
      gap: 2,
    }}
  >
    {icon}
    <Typography variant="h6" sx={{ fontWeight: 600 }}>
      {title}
    </Typography>
    <Typography variant="body2">{message}</Typography>
  </Box>
);
