import { Box, AppBar, Toolbar, IconButton, Avatar, Menu, MenuItem, Stack, Tooltip } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import { useUIStore } from '@/stores/uiStore';
import { Menu as MenuIcon, Moon, Sun, LogOut, Settings } from 'lucide-react';
import { useState } from 'react';

export const Header = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const { toggleSidebar, theme, toggleTheme } = useUIStore();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <AppBar
      position="fixed"
      sx={{
        zIndex: (theme) => theme.zIndex.drawer + 1,
        backgroundColor: 'background.paper',
        color: 'text.primary',
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
        borderBottom: '1px solid',
        borderColor: 'divider',
      }}
    >
      <Toolbar sx={{ display: 'flex', justifyContent: 'space-between' }}>
        <Stack direction="row" spacing={2} alignItems="center">
          <IconButton
            edge="start"
            color="inherit"
            aria-label="menu"
            onClick={() => toggleSidebar()}
            sx={{ display: { xs: 'flex', sm: 'none' } }}
          >
            <MenuIcon size={20} />
          </IconButton>
          <Box sx={{ fontWeight: 700, fontSize: '1.25rem', color: 'primary.main' }}>MetaDB</Box>
        </Stack>

        <Stack direction="row" spacing={1} alignItems="center">
          <Tooltip title={theme === 'dark' ? 'Light mode' : 'Dark mode'}>
            <IconButton size="small" onClick={toggleTheme} color="inherit">
              {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
            </IconButton>
          </Tooltip>

          <Avatar
            sx={{ cursor: 'pointer', width: 32, height: 32 }}
            onClick={handleMenuOpen}
            alt={user?.username}
          >
            {user?.username?.charAt(0).toUpperCase()}
          </Avatar>

          <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={handleMenuClose}>
            <MenuItem disabled>
              <div>
                <div style={{ fontWeight: 600 }}>{user?.username}</div>
                <div style={{ fontSize: '0.85rem', color: '#999' }}>{user?.email}</div>
              </div>
            </MenuItem>
            <MenuItem onClick={() => navigate('/settings')}>
              <Settings size={16} style={{ marginRight: 8 }} />
              Settings
            </MenuItem>
            <MenuItem onClick={handleLogout}>
              <LogOut size={16} style={{ marginRight: 8 }} />
              Logout
            </MenuItem>
          </Menu>
        </Stack>
      </Toolbar>
    </AppBar>
  );
};
