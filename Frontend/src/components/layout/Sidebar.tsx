import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Box,
  Divider,
  useMediaQuery,
} from '@mui/material';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import { useUIStore } from '@/stores/uiStore';
import {
  LayoutDashboard,
  Database,
  FileText,
  Settings,
  Users,
  BarChart3,
  FileBarChart,
  Clock,
} from 'lucide-react';

interface NavItem {
  label: string;
  path: string;
  icon: React.ReactNode;
  requiredRole?: 'admin' | 'editor' | 'viewer';
}

const navItems: NavItem[] = [
  { label: 'Dashboard', path: '/dashboard', icon: <LayoutDashboard size={20} /> },
  { label: 'Schemas', path: '/schemas', icon: <Database size={20} /> },
  { label: 'Metadata', path: '/metadata', icon: <FileText size={20} /> },
  { label: 'Reports', path: '/reports/templates', icon: <FileBarChart size={20} /> },
  { label: 'Report History', path: '/reports/history', icon: <Clock size={20} /> },
  { label: 'Analytics', path: '/analytics', icon: <BarChart3 size={20} /> },
];

const adminItems: NavItem[] = [
  { label: 'Asset Types', path: '/asset-types', icon: <BarChart3 size={20} />, requiredRole: 'admin' },
  { label: 'Users', path: '/users', icon: <Users size={20} />, requiredRole: 'admin' },
];

export const Sidebar = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const { sidebarOpen, toggleSidebar } = useUIStore();
  const isMobile = useMediaQuery((theme: any) => theme.breakpoints.down('sm'));

  const canAccess = (item: NavItem) => {
    if (!item.requiredRole) return true;
    return user?.role === item.requiredRole || user?.role === 'admin';
  };

  const filteredItems = [...navItems, ...adminItems].filter(canAccess);

  const handleNavigation = (path: string) => {
    navigate(path);
    if (isMobile) toggleSidebar();
  };

  const drawerContent = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ p: 2, fontWeight: 700, fontSize: '1.25rem', color: 'primary.main' }}>MetaDB</Box>
      <Divider />

      <List sx={{ flex: 1 }}>
        {filteredItems.map((item) => (
          <ListItem key={item.path} disablePadding>
            <ListItemButton
              selected={location.pathname === item.path}
              onClick={() => handleNavigation(item.path)}
              sx={{
                color: location.pathname === item.path ? 'primary.main' : 'inherit',
                backgroundColor: location.pathname === item.path ? 'action.selected' : 'transparent',
              }}
            >
              <ListItemIcon sx={{ color: 'inherit', minWidth: 40 }}>{item.icon}</ListItemIcon>
              <ListItemText primary={item.label} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>

      <Divider />
      <List>
        <ListItem disablePadding>
          <ListItemButton onClick={() => handleNavigation('/settings')}>
            <ListItemIcon sx={{ minWidth: 40 }}>
              <Settings size={20} />
            </ListItemIcon>
            <ListItemText primary="Settings" />
          </ListItemButton>
        </ListItem>
      </List>
    </Box>
  );

  return (
    <>
      <Drawer
        variant={isMobile ? 'temporary' : 'permanent'}
        open={isMobile ? sidebarOpen : true}
        onClose={() => toggleSidebar()}
        sx={{
          width: 280,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: 280,
            marginTop: '64px',
            height: 'calc(100vh - 64px)',
            backgroundColor: 'background.paper',
            borderRight: '1px solid',
            borderColor: 'divider',
          },
        }}
      >
        {drawerContent}
      </Drawer>
    </>
  );
};
