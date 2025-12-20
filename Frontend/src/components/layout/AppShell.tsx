import { Box, Container, Toolbar } from '@mui/material';
import { Header } from './Header';
import { Sidebar } from './Sidebar';

interface AppShellProps {
  children: React.ReactNode;
}

export const AppShell = ({ children }: AppShellProps) => {
  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', backgroundColor: 'background.default' }}>
      <Header />
      <Sidebar />
      <Box component="main" sx={{ flex: 1, overflow: 'auto' }}>
        <Toolbar />
        <Container maxWidth="lg" sx={{ py: 4 }}>
          {children}
        </Container>
      </Box>
    </Box>
  );
};
